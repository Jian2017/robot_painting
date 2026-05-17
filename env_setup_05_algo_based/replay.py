#!/usr/bin/env python3
"""
Replay recorded left or right trajectory on the follower arm.

Usage:
    python replay.py left
    python replay.py right
"""

import sys, time, math
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "env_setup_03_arm" / "vendor" /
                     "lerobot-robot-seeed-b601"))

from lerobot_robot_seeed_b601.seeed_b601_dm_follower import SeeedB601DMFollower
from lerobot_robot_seeed_b601.config_seeed_b601_dm_follower import SeeedB601DMFollowerConfig

PORT   = "/dev/cu.usbmodem00000000050C1"
BASE   = Path(__file__).parent
JOINTS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
          "wrist_flex.pos", "wrist_yaw.pos", "wrist_roll.pos", "gripper.pos"]


def load_trajectory(side: str) -> tuple[np.ndarray, np.ndarray]:
    path = BASE / f"datasets_{side}" / "data" / "chunk-000" / "file-000.parquet"
    if not path.exists():
        print(f"ERROR: {path} not found. Run record_{side}.sh first.")
        sys.exit(1)
    df = pd.read_parquet(str(path))
    positions  = np.stack(df["action"].values)    # (T, 7) degrees
    timestamps = df["timestamp"].values.astype(float)  # (T,) seconds
    return positions, timestamps


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay.py <名字>")
        print("例如:  python replay.py left")
        print("       python replay.py home")
        sys.exit(1)
    side = sys.argv[1]

    positions, timestamps = load_trajectory(side)
    T = len(positions)
    print(f"Loaded go_{side}: {T} frames, {timestamps[-1]:.1f}s")

    cfg = SeeedB601DMFollowerConfig(port=PORT, id="follower1", can_adapter="damiao")
    robot = SeeedB601DMFollower(cfg)
    print("Connecting...")
    robot.connect(calibrate=False)

    # Hold current position immediately after connect to prevent snap
    time.sleep(0.2)
    for motor in robot.motors.values():
        motor.request_feedback()
    try:
        robot.bus.poll_feedback_once()
    except Exception:
        pass
    hold = {}
    for name, motor in robot.motors.items():
        state = motor.get_state()
        hold[f"{name}.pos"] = math.degrees(state.pos) if state else 0.0
    robot.send_action(hold)

    input("Press ENTER to start replay...")
    print("Replaying...")

    t0 = time.perf_counter()
    for i in range(T):
        # Wait until it's time for this frame
        while time.perf_counter() - t0 < timestamps[i]:
            time.sleep(0.001)

        action = {JOINTS[j]: float(positions[i, j]) for j in range(7)}
        robot.send_action(action)

    print("Done.")
    robot.disconnect()


if __name__ == "__main__":
    main()
