#!/usr/bin/env bash
# One-shot bootstrap for LeRobot + Star Arm 102 (leader) + reBot B601-DM (follower).
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
pip install -e ./vendor/lerobot
pip install -e ./vendor/lerobot-teleoperator-rebot-arm-102
pip install -e ./vendor/lerobot-robot-seeed-b601
pip install motorbridge

echo
echo "Done. Activate with: source ${ROOT}/venv/bin/activate"
echo "Then: lerobot-find-port   # pick leader + follower ports"
echo "See README.md for calibrate + teleoperate."
