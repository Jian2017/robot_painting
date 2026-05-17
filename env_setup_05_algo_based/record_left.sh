#!/usr/bin/env bash
set -uo pipefail
cd /Users/jian/workspace/robot_painting/env_setup_03_arm
source venv/bin/activate

lerobot-record \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-140 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}' \
  --dataset.repo_id=local/algo_left \
  --dataset.root=/Users/jian/workspace/robot_painting/env_setup_05_algo_based/datasets_left \
  --dataset.single_task="move arm to left" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=3 \
  --dataset.push_to_hub=false \
  --dataset.video=false \
  --display_data=false
