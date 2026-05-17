#!/usr/bin/env bash
# Calibrate both arms to the same home position.
set -uo pipefail

ARM_DIR="/Users/jian/workspace/robot_painting/env_setup_03_arm"
ALGO_DIR="/Users/jian/workspace/robot_painting/env_setup_05_algo_based"

cd "$ARM_DIR"
source venv/bin/activate

echo "=== Step 1: Calibrate FOLLOWER arm ==="
echo "Move follower arm to HOME position first."
echo ""

# Delete old calibration so connect() triggers re-calibration
rm -f ~/.cache/huggingface/lerobot/calibration/robots/seeed_b601_dm_follower/follower1.json

python3 "$ALGO_DIR/_calibrate_follower.py"

echo ""
echo "=== Step 2: Calibrate LEADER arm ==="
echo "Move leader arm to the SAME home position as follower."
echo "When prompted, type 'c' + ENTER to run new calibration."
echo ""

lerobot-calibrate \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-140 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}'

echo ""
echo "Done. Both arms calibrated from the same home position."
echo "Now run: bash record_left.sh  or  bash record_right.sh"
