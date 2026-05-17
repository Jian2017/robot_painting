#!/usr/bin/env python3
"""
Cookie detector: top_cam → "left" | "right" | "none"

Two modes:
  - calibrate: click on cookie to sample its HSV color range
  - detect:    use saved color range to detect cookie position
"""

import json
import cv2
import numpy as np
from pathlib import Path

CALIB_FILE = Path(__file__).parent / "cookie_color.json"
CAM_INDEX  = 1   # top_cam (Innomaker)


# ── Color calibration ─────────────────────────────────────────────────────────

_clicked_hsv = []

def _mouse_callback(event, x, y, flags, frame):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        color = hsv[y, x]
        _clicked_hsv.append(color.tolist())
        print(f"  sampled HSV: {color.tolist()}")


def calibrate():
    """Interactive: click the cookie 5+ times, saves HSV range."""
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("=== Cookie Color Calibration ===")
    print("Click on the cookie multiple times (5-10 clicks), then press ENTER.")

    global _clicked_hsv
    _clicked_hsv = []

    cv2.namedWindow("calibrate")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        display = frame.copy()
        cv2.putText(display, f"Clicks: {len(_clicked_hsv)}  Press ENTER when done",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("calibrate", display)
        cv2.setMouseCallback("calibrate", _mouse_callback, frame)

        key = cv2.waitKey(30) & 0xFF
        if key == 13 and len(_clicked_hsv) >= 3:  # ENTER
            break
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return

    cap.release()
    cv2.destroyAllWindows()

    samples = np.array(_clicked_hsv)
    margin = np.array([15, 60, 60])
    hsv_lo = np.clip(samples.min(axis=0) - margin, 0, [179, 255, 255]).tolist()
    hsv_hi = np.clip(samples.max(axis=0) + margin, 0, [179, 255, 255]).tolist()

    data = {"hsv_lo": hsv_lo, "hsv_hi": hsv_hi}
    CALIB_FILE.write_text(json.dumps(data, indent=2))
    print(f"Saved: {CALIB_FILE}")
    print(f"  lo={hsv_lo}  hi={hsv_hi}")


# ── Detector ──────────────────────────────────────────────────────────────────

class CookieDetector:
    def __init__(self):
        if not CALIB_FILE.exists():
            print("WARNING: no calibration file. Run calibrate() first.")
            self.hsv_lo = np.array([10,  80,  80])
            self.hsv_hi = np.array([30, 255, 255])
        else:
            data = json.loads(CALIB_FILE.read_text())
            self.hsv_lo = np.array(data["hsv_lo"])
            self.hsv_hi = np.array(data["hsv_hi"])

    def detect(self, frame_bgr: np.ndarray, debug: bool = False) -> str:
        """
        Returns: "left" | "right" | "none"
        frame_bgr: 480x640 BGR image from top_cam
        """
        h, w = frame_bgr.shape[:2]
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lo, self.hsv_hi)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return "none"

        # Largest contour
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < 500:   # too small → noise
            return "none"

        M = cv2.moments(largest)
        cx = int(M["m10"] / M["m00"])

        if debug:
            out = frame_bgr.copy()
            cv2.drawContours(out, [largest], -1, (0, 255, 0), 2)
            cv2.circle(out, (cx, int(M["m01"] / M["m00"])), 6, (0, 0, 255), -1)
            cv2.line(out, (w // 2, 0), (w // 2, h), (255, 0, 0), 2)
            cv2.imshow("detect_debug", out)

        return "left" if cx < w // 2 else "right"


# ── Preview / test ────────────────────────────────────────────────────────────

def preview():
    """Live preview: shows detection result. Press Q to quit."""
    detector = CookieDetector()
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Live detection preview. Press Q to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        result = detector.detect(frame, debug=True)
        cv2.putText(frame, f"Cookie: {result}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    {"left": (0, 128, 255), "right": (0, 255, 0), "none": (0, 0, 255)}[result], 3)
        cv2.line(frame, (320, 0), (320, 480), (255, 0, 0), 2)
        cv2.imshow("cookie detector", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        preview()
    else:
        calibrate()
        preview()
