"""
读取 Star Arm 102 Leader Arm 各关节位置

用法:
    python read_leader_arm.py

依赖:
    pip install fashionstar-uart-sdk pyserial
"""

import time
import serial
from fashionstar_uart_sdk import UartServoManager

PORT = "/dev/cu.usbserial-110"  # 以 `ls /dev/cu.usbserial-*` 为准
BAUDRATE = 1000000               # Fashion Star RA8 系列默认波特率

uart = serial.Serial(PORT, BAUDRATE, timeout=0.1)
manager = UartServoManager(uart)

# id0~id5: 6个关节，id6: 夹爪
SERVO_IDS = list(range(7))

print(f"已连接: {PORT} @ {BAUDRATE}")
print("按 Ctrl+C 退出\n")

try:
    while True:
        parts = []
        for sid in SERVO_IDS:
            angle = manager.query_servo_angle(sid)
            parts.append(f"id{sid}={angle:7.2f}°" if angle is not None else f"id{sid}=N/A")
        print("  ".join(parts))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n退出")
finally:
    uart.close()
