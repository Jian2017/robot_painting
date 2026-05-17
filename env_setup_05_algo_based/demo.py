#!/usr/bin/env python3
"""
检测饼干位置 → 调用 replay.py left 或 replay.py right

用法:
    python demo.py          # 检测一次，执行动作
    python demo.py --loop   # 循环：检测 → 执行 → 再检测
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import cv2

from detect_cookie import CookieDetector

CAM_INDEX = 1   # top_cam
SCRIPT    = Path(__file__).parent / "replay.py"
PYTHON    = sys.executable


def detect_once(detector, cap, n_frames=20) -> str:
    """拍 n_frames 帧投票，返回 'left' | 'right' | 'none'"""
    votes = []
    for _ in range(n_frames):
        ret, frame = cap.read()
        if ret:
            result = detector.detect(frame, debug=True)
            votes.append(result)
            cv2.waitKey(30)

    counts = {s: votes.count(s) for s in ("left", "right", "none")}
    winner = max(counts, key=counts.get)
    print(f"检测结果: {counts} → {winner}")
    return winner


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loop", action="store_true", help="循环执行直到 Ctrl-C")
    args = p.parse_args()

    detector = CookieDetector()
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("摄像头已连接。按 Ctrl-C 退出。")

    try:
        while True:
            print("\n正在检测饼干位置...")
            side = detect_once(detector, cap)
            cv2.destroyAllWindows()

            if side == "none":
                print("未检测到饼干，等待 2 秒...")
                time.sleep(2)
            else:
                print(f"饼干在 {side}，执行 replay {side} ...")
                subprocess.run([PYTHON, str(SCRIPT), side], check=True)
                print("动作完成。")

            if not args.loop:
                break

            print("等待 3 秒后再次检测...")
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n退出。")
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
