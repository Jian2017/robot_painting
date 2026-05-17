#!/usr/bin/env python
"""Run ACT policy on the real B601 follower arm."""

import time
import torch

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.utils import build_inference_frame, make_robot_action

from lerobot_robot_seeed_b601.seeed_b601_dm_follower import SeeedB601DMFollower
from lerobot_robot_seeed_b601.config_seeed_b601_dm_follower import SeeedB601DMFollowerConfig

CHECKPOINT = "/Users/jian/workspace/robot_painting/outputs/act_painting_test/checkpoints/000200/pretrained_model"
DATASET_ROOT = "/Users/jian/workspace/robot_painting/data/painting_demo_with_2camera"
DATASET_ID = "painting_demo_with_2camera"

FOLLOWER_PORT = "/dev/cu.usbmodem00000000050C1"
FOLLOWER_ID = "follower1"

MAX_EPISODES = 1
MAX_STEPS_PER_EPISODE = 900  # ~30 seconds at 30Hz
FPS = 30


def main():
    device = torch.device("mps")

    print(f"Loading ACT policy from {CHECKPOINT}...")
    model = ACTPolicy.from_pretrained(CHECKPOINT)
    model.eval()

    dataset_metadata = LeRobotDatasetMetadata(DATASET_ID, root=DATASET_ROOT)
    preprocess, postprocess = make_pre_post_processors(model.config, dataset_stats=dataset_metadata.stats)

    camera_config = {
        "top_cam": OpenCVCameraConfig(index_or_path=1, width=480, height=640, fps=30, rotation=90),
        "side_cam": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=30),
    }

    robot_cfg = SeeedB601DMFollowerConfig(
        port=FOLLOWER_PORT,
        id=FOLLOWER_ID,
        can_adapter="damiao",
        cameras=camera_config,
    )
    robot = SeeedB601DMFollower(robot_cfg)
    print("Connecting to robot...")
    robot.connect(calibrate=False)
    print("Robot connected. Starting eval...")

    try:
        for ep in range(MAX_EPISODES):
            print(f"\n--- Episode {ep + 1}/{MAX_EPISODES} ---")
            print("Press Ctrl+C to stop.")
            for step in range(MAX_STEPS_PER_EPISODE):
                t0 = time.perf_counter()

                obs = robot.get_observation()
                obs_frame = build_inference_frame(
                    observation=obs,
                    ds_features=dataset_metadata.features,
                    device=device,
                )
                obs_pre = preprocess(obs_frame)

                with torch.no_grad():
                    action = model.select_action(obs_pre)

                action_post = postprocess(action)
                action_dict = make_robot_action(action_post, dataset_metadata.features)
                robot.send_action(action_dict)

                dt = time.perf_counter() - t0
                time.sleep(max(0, 1 / FPS - dt))

            print(f"Episode {ep + 1} done.")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        robot.disconnect()
        print("Robot disconnected.")


if __name__ == "__main__":
    main()
