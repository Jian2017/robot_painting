# env_setup_03_arm_record — 双臂 + 双摄像头录数据

在 `env_setup_03_arm` 环境基础上，接入两个摄像头，完成 `lerobot-record` 数据采集。

---

## 硬件配置（本机，2026-05-16）

### 串口

| 设备 | 串口 | 备注 |
|------|------|------|
| Star Arm 102（主臂） | `/dev/cu.usbserial-140` | 经 dock 后端口名从 `usbserial-10` 变为 `usbserial-140` |
| reBot B601-DM（从臂） | `/dev/cu.usbmodem00000000050C1` | 直连 Mac USB |

> **串口漂移**：换 dock 或重插后端口名可能变化，每次先用 `ls /dev/cu.usb*` 确认。

### 摄像头

| OpenCV Index | 设备名 | 用途 | 备注 |
|-------------|--------|------|------|
| 0 | Innomaker-U20CAM-1080p-S1 | wrist_cam（arm head） | 图像横向，需 `rotation=90` |
| 1 | HD USB Camera | top_cam（俯视桌面） | 正常，无需旋转 |
| 2 | FaceTime HD Camera | ❌ 不用 | Mac 内置 |
| 3 | jphone Camera | ❌ 不用 | iPhone Continuity Camera，OpenCV 读不了 |

> **摄像头 index 会随插拔顺序变化**，换设备后用 `lerobot-find-cameras` 或下方脚本重新确认。

```bash
# 快速确认哪个 index 是哪个摄像头
source ../env_setup_03_arm/venv/bin/activate
python3 - <<'EOF'
import cv2, time, os
os.makedirs("cam_check", exist_ok=True)
for idx in range(5):
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened(): cap.release(); continue
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(2)
    ret, frame = cap.read()
    if ret and frame is not None and frame.sum() > 0:
        cv2.imwrite(f"cam_check/index_{idx}.png", frame)
        print(f"index {idx}: OK")
    else:
        print(f"index {idx}: black")
    cap.release()
EOF
open cam_check/
```

---

## 关键注意事项

### 摄像头 rotation 与 width/height 的关系

`rotation=90` 时，width/height 必须按**旋转后的输出尺寸**填写，lerobot 内部自动换算 capture 分辨率：

| 摄像头原始分辨率 | rotation | config 里填的 width × height |
|----------------|---------|------------------------------|
| 640 × 480 | 无 | 640 × 480 |
| 640 × 480 | 90° | **480 × 640**（宽高对调）|

错误示例（会报 `RuntimeError: failed to set capture_width`）：
```json
{"wrist_cam": {"type":"opencv","index_or_path":0,"width":640,"height":480,"rotation":90}}
```

正确写法：
```json
{"wrist_cam": {"type":"opencv","index_or_path":0,"width":480,"height":640,"rotation":90}}
```

---

## 完整命令

### Teleoperate（验证硬件，不存数据）

```bash
cd ../env_setup_03_arm
source venv/bin/activate

lerobot-teleoperate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.cameras='{"wrist_cam":{"type":"opencv","index_or_path":0,"fps":30,"width":480,"height":640,"rotation":90},"top_cam":{"type":"opencv","index_or_path":1,"fps":30,"width":640,"height":480}}' \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-140 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}'
```

### Record（正式录数据）

```bash
cd ../env_setup_03_arm
source venv/bin/activate

lerobot-record \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.cameras='{"wrist_cam":{"type":"opencv","index_or_path":0,"fps":30,"width":480,"height":640,"rotation":90},"top_cam":{"type":"opencv","index_or_path":1,"fps":30,"width":640,"height":480}}' \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-140 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}' \
  --dataset.repo_id=local/painting_demo \
  --dataset.num_episodes=50 \
  --dataset.single_task="Draw a circle on the paper"
```

数据保存位置：`~/.cache/huggingface/lerobot/local/painting_demo/`

---

## 录数据要点

- 每次录前把画布放回胶带标记位置
- 每条 episode 做**同一个动作**（如画圆），保持一致
- 质量 > 数量：50 条好的 > 100 条乱的
- 录完一条后按提示键保存，再做下一条
- 异常退出后重插 USB 再重跑（参考 `env_setup_03_arm/TELEOPERATE.md`）

---

## 下一步

```bash
# 录完 50 条后开始训练
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=local/painting_demo \
  --output_dir=outputs/painting_act
```
