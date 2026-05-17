#!/usr/bin/env bash
# 录制任意名字的轨迹
# 用法: bash record.sh <名字>
# 例如: bash record.sh left
#       bash record.sh right
#       bash record.sh home
#       bash record.sh paint_stroke

set -uo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
    echo "用法: bash record.sh <名字>"
    echo "例如: bash record.sh left"
    exit 1
fi

ALGO_DIR="/Users/jian/workspace/robot_painting/env_setup_05_algo_based"
DATASET_DIR="$ALGO_DIR/datasets_$NAME"

if [ -d "$DATASET_DIR" ]; then
    echo "警告: $DATASET_DIR 已存在。"
    echo -n "是否删除并重新录制? [y/N] "
    read -r ans
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
        rm -rf "$DATASET_DIR"
        echo "已删除旧数据。"
    else
        echo "取消。"
        exit 0
    fi
fi

cd /Users/jian/workspace/robot_painting/env_setup_03_arm
source venv/bin/activate

echo "开始录制: $NAME"
echo "  数据保存到: $DATASET_DIR"
echo "  录制完成后按 → 右箭头 保存，← 左箭头 丢弃，Esc 退出"
echo ""

lerobot-record \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-140 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}' \
  --dataset.repo_id="local/algo_$NAME" \
  --dataset.root="$DATASET_DIR" \
  --dataset.single_task="move arm to $NAME" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=3 \
  --dataset.push_to_hub=false \
  --dataset.video=false \
  --display_data=false

echo ""
echo "录制完成: $NAME → $DATASET_DIR"
