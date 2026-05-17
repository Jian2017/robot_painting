#!/usr/bin/env python3
"""
Demo: camera detects cookie → arm executes recorded trajectory.

Flow:
  1. Load go_left.npy and go_right.npy
  2. Connect follower arm + top_cam
  3. Loop:
       - Detect cookie position (left / right / none)
       - If detected: replay corresponding trajectory
       - Wait for arm to finish, then loop again

Usage:
    python run_demo.py
    python run_demo.py --once          # run once then exit
    python run_demo.py --dry_run       # detect only, don't move arm
"""

import argparse
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from detect_cookie import CookieDetector

BASE          = Path(__file__).parent
FOLLOWER_PORT = "/dev/cu.usbmodem00000000050C1"
FOLLOWER_ID   = "follower1"
FPS           = 30
JOINT_NAMES   = ["shoulder_pan", "shoulder_lift", "elbow_flex",
                 "wrist_flex", "wrist_yaw", "wrist_roll", "gripper"]
CAM_INDEX     = 1   # top_cam


def connect_follower():
    sys.path.insert(0, str(Path(__file__).parent.parent / "env_setup_03_arm" / "vendor" /
                         "lerobot-robot-seeed-b601"))
    from lerobot_robot_seeed_b601.seeed_b601_dm_follower import SeeedB601DMFollower
    from lerobot_robot_seeed_b601.config_seeed_b601_dm_follower import SeeedB601DMFollowerConfig

    cfg = SeeedB601DMFollowerConfig(
        port=FOLLOWER_PORT, id=FOLLOWER_ID, can_adapter="damiao",
    )
    robot = SeeedB601DMFollower(cfg)
    robot.connect(calibrate=False)

    # Hold current position immediately to prevent snap-to-zero
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

    return robot


def load_trajectory(side: str) -> dict:
    path = BASE / f"datasets_{side}" / "data" / "chunk-000" / "file-000.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Trajectory not found: {path}\nRun: bash record_{side}.sh")
    df = pd.read_parquet(str(path))
    positions  = np.stack(df["action"].values)           # (T, 7) degrees
    timestamps = df["timestamp"].values.astype(float)    # (T,) seconds
    return {"positions": positions, "timestamps": timestamps}


def replay(robot, traj: dict, speed: float = 1.0):
    """Replay a recorded trajectory on the follower arm."""
    positions  = traj["positions"]   # (T, 7)
    timestamps = traj["timestamps"]  # (T,)
    T = len(positions)

    print(f"  Replaying {T} frames ({timestamps[-1]:.1f}s at speed {speed}x)...")
    t0 = time.perf_counter()

    for i in range(T):
        target_t = timestamps[i] / speed
        # Busy-wait for timing
        while time.perf_counter() - t0 < target_t:
            time.sleep(0.001)

        action = {f"{j}.pos": float(positions[i, ji])
                  for ji, j in enumerate(JOINT_NAMES)}
        robot.send_action(action)

    print("  Done.")


def detect_stable(detector, cap, n_frames: int = 10) -> str:
    """Vote over n_frames to get a stable detection result."""
    votes = []
    for _ in range(n_frames):
        ret, frame = cap.read()
        if ret:
            votes.append(detector.detect(frame))
        time.sleep(1.0 / FPS)

    counts = {"left": votes.count("left"), "right": votes.count("right"), "none": votes.count("none")}
    result = max(counts, key=counts.get)
    print(f"  Detection votes: {counts} → {result}")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once",     action="store_true", help="Run one detection+action cycle then exit")
    p.add_argument("--dry_run",  action="store_true", help="Detect only, don't move arm")
    p.add_argument("--speed",    type=float, default=1.0, help="Replay speed multiplier (e.g. 0.8 = slower)")
    args = p.parse_args()

    # Load trajectories
    print("Loading trajectories...")
    trajs = {}
    for side in ("left", "right"):
        try:
            trajs[side] = load_trajectory(side)
            T = len(trajs[side]["positions"])
            dur = trajs[side]["timestamps"][-1]
            print(f"  go_{side}: {T} frames, {dur:.1f}s")
        except FileNotFoundError as e:
            print(f"  WARNING: {e}")

    if not trajs and not args.dry_run:
        print("ERROR: No trajectories found. Record them first:")
        print("  bash record_left.sh")
        print("  bash record_right.sh")
        sys.exit(1)

    # Connect camera
    print("Connecting camera (top_cam)...")
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    detector = CookieDetector()

    # Connect robot
    robot = None
    if not args.dry_run:
        print("Connecting follower arm...")
        robot = connect_follower()

    print("\n=== Demo running. Press Ctrl-C to stop. ===\n")

    last_action = None

    try:
        while True:
            print("Detecting cookie position...")
            result = detect_stable(detector, cap, n_frames=15)

            # Show live frame
            ret, frame = cap.read()
            if ret:
                color = {"left": (0, 128, 255), "right": (0, 255, 0), "none": (0, 0, 255)}[result]
                cv2.putText(frame, f"Cookie: {result}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
                cv2.line(frame, (320, 0), (320, 480), (200, 200, 200), 2)
                cv2.imshow("demo", frame)
                cv2.waitKey(1)

            if result == "none":
                print("  No cookie detected. Waiting 2s...")
                time.sleep(2)
            elif result in trajs:
                if args.dry_run:
                    print(f"  [dry_run] Would execute go_{result}")
                else:
                    print(f"  Executing go_{result}...")
                    replay(robot, trajs[result], speed=args.speed)
                last_action = result
                if args.once:
                    break
                print("  Waiting 3s before next detection...\n")
                time.sleep(3)
            else:
                print(f"  No trajectory recorded for '{result}'. Skipping.")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if robot is not None:
            robot.disconnect()


if __name__ == "__main__":
    main()
