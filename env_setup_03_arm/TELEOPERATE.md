# Teleoperate 实战记录（macOS，2026-05-15）

## 实际串口（本机）

| 设备 | 串口 |
|------|------|
| Star Arm 102（主臂，CH340） | `/dev/cu.usbserial-10` |
| reBot B601-DM（从臂） | `/dev/cu.usbmodem00000000050C1` |

## 成功命令

```bash
source venv/bin/activate

lerobot-teleoperate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-10 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}'
```

成功后输出：
```
rebot_arm_102_leader connected.
follower1 SeeedB601DMFollower connected.
Teleop loop time: 16.67ms (60 Hz)
```

---

## 踩坑记录

### 1. JSON 引号缺失导致参数解析失败

**报错**：`draccus.utils.DecodingError: Couldn't parse 'None' into a int`

**原因**：`--teleop.joint_directions` 的 JSON 字符串中某个 key 缺少开头的 `"`。

**错误写法**：
```
"wrist_flex":1,wrist_yaw":1
```

**正确写法**：
```
"wrist_flex":1,"wrist_yaw":1
```

### 2. 串口报 `Invalid argument`（所有波特率均失败）

**报错**：`ServoBusError: serial error: Invalid argument`

**原因**：上次程序未正常退出（崩溃或强制关闭），串口状态残留损坏，macOS 不会自动重置。

**修复**：把 Star Arm 102 的 USB 线**拔掉重插**，立即恢复，无需重启系统或重装驱动。

**预防**：每次停止前先让臂回零位，再 `Ctrl+C`，再断电。若程序异常退出，第一步先重插 USB。
