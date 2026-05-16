#!/usr/bin/env bash
# One-shot bootstrap for LeRobot + Star Arm 102 (leader) + reBot B601-DM (follower).
# Variant of bootstrap.sh that ALSO applies the follower drift fix
# (FOLLOWER_DRIFT_ANALYSIS.md) to the freshly cloned lerobot-robot-seeed-b601.
# See README.md for links and manual steps.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3.12}"
if ! command -v "$PY" &>/dev/null; then
  PY="python3"
fi

if [[ ! -d venv ]]; then
  "$PY" -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install -U pip wheel

mkdir -p vendor
cd vendor

clone_or_update() {
  local url="$1"
  local name="$2"
  if [[ -d "$name/.git" ]]; then
    git -C "$name" pull --ff-only
  else
    git clone --depth 1 "$url" "$name"
  fi
}

clone_or_update "https://github.com/Seeed-Projects/lerobot.git" "lerobot"
clone_or_update "https://github.com/Seeed-Projects/lerobot-teleoperator-rebot-arm-102.git" "lerobot-teleoperator-rebot-arm-102"
clone_or_update "https://github.com/Seeed-Projects/lerobot-robot-seeed-b601.git" "lerobot-robot-seeed-b601"

cd "$ROOT"

# --- Drift fix -------------------------------------------------------------
# Applies the two fixes from FOLLOWER_DRIFT_ANALYSIS.md to the cloned
# lerobot-robot-seeed-b601 source. The heredoc below is the verbatim
# `git diff` of those changes. Idempotent: a re-run detects an already-
# patched tree and skips; if the patch no longer matches (upstream changed
# the file) it warns instead of silently shipping unpatched code. For a
# guaranteed-clean apply, delete vendor/lerobot-robot-seeed-b601 first.
SEEED_REPO="${ROOT}/vendor/lerobot-robot-seeed-b601"
DRIFT_PATCH="$(mktemp)"
cat > "$DRIFT_PATCH" <<'DRIFT_PATCH_EOF'
diff --git a/lerobot_robot_seeed_b601/seeed_b601_follower.py b/lerobot_robot_seeed_b601/seeed_b601_follower.py
index 4f47e39..fbb723b 100644
--- a/lerobot_robot_seeed_b601/seeed_b601_follower.py
+++ b/lerobot_robot_seeed_b601/seeed_b601_follower.py
@@ -96,6 +96,12 @@ class SeeedB601FollowerBase(Robot):
         self.motors = {}
         self.motor_names = list(config.motor_can_ids.keys())
 
+        # Last known good motor positions (degrees). Used as a fallback in
+        # get_observation() when a motor briefly stops reporting state, so the
+        # arm holds position instead of snapping to 0 deg. See
+        # FOLLOWER_DRIFT_ANALYSIS.md.
+        self._last_obs: dict[str, float] = {}
+
         # Initialize cameras
         self.cameras = make_cameras_from_configs(config.cameras)
 
@@ -226,13 +232,21 @@ class SeeedB601FollowerBase(Robot):
                 if motor_name == FOLLOWER_GRIPPER_MOTOR
                 else MotorBridgeMode.POS_VEL
             )
-            for _ in range(num_retry + 1):
+            for attempt in range(num_retry + 1):
                 try:
                     motor.ensure_mode(target_mode)
                     break
                 except Exception as e:
-                    if _ == num_retry:
+                    if attempt == num_retry:
                         raise e
+                    # Motor may be in error state (red): clear the error and
+                    # re-enable before retrying. See FOLLOWER_DRIFT_ANALYSIS.md.
+                    try:
+                        motor.clear_error()
+                        time.sleep(MEDIUM_TIMEOUT_SEC)
+                        motor.enable()
+                    except Exception:
+                        logger.warning(f"{motor_name} error-recovery attempt failed")
                     time.sleep(MEDIUM_TIMEOUT_SEC)
             logger.info(f"{motor_name} ensure mode {target_mode}")
 
@@ -266,11 +280,16 @@ class SeeedB601FollowerBase(Robot):
             state = motor.get_state()
             if state is not None:
                 # motorbridge works natively in radians. Convert to degrees.
-                obs_dict[f"{motor_name}.pos"] = math.degrees(state.pos)
+                pos = math.degrees(state.pos)
+                self._last_obs[motor_name] = pos  # cache last known good pos
+                obs_dict[f"{motor_name}.pos"] = pos
                 obs_dict[f"{motor_name}.vel"] = math.degrees(state.vel)
                 obs_dict[f"{motor_name}.torque"] = state.torq
             else:
-                obs_dict[f"{motor_name}.pos"] = 0.0
+                # Motor not reporting (likely error / red state): hold the last
+                # known position instead of snapping to 0 deg. See
+                # FOLLOWER_DRIFT_ANALYSIS.md.
+                obs_dict[f"{motor_name}.pos"] = self._last_obs.get(motor_name, 0.0)
                 obs_dict[f"{motor_name}.vel"] = 0.0
                 obs_dict[f"{motor_name}.torque"] = 0.0
 
DRIFT_PATCH_EOF

if git -C "$SEEED_REPO" apply --reverse --check "$DRIFT_PATCH" 2>/dev/null; then
  echo "Drift fix: already applied, skipping."
elif git -C "$SEEED_REPO" apply --check "$DRIFT_PATCH" 2>/dev/null; then
  git -C "$SEEED_REPO" apply "$DRIFT_PATCH"
  echo "Drift fix: applied to seeed_b601_follower.py"
else
  echo "WARNING: drift fix did not apply cleanly (did upstream change the file?)."
  echo "         Apply the two changes from FOLLOWER_DRIFT_ANALYSIS.md by hand."
fi
rm -f "$DRIFT_PATCH"
# ---------------------------------------------------------------------------

pip install -e ./vendor/lerobot
pip install -e ./vendor/lerobot-teleoperator-rebot-arm-102
pip install -e ./vendor/lerobot-robot-seeed-b601
pip install motorbridge

echo
echo "Done. Activate with: source ${ROOT}/venv/bin/activate"
echo "Then: lerobot-find-port   # pick leader + follower ports"
echo "See README.md for calibrate + teleoperate."
