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

### 3. 主臂动快时从臂跟不上 / 动作错乱（2026-05-16）

**现象**：teleop 时，主臂（leader）稍微动快一点，从臂（follower）就变慢、跟不上、动作错乱；主臂动得很慢时从臂能正常跟随。

**原因**：**不是通信频率问题**。从臂 6 个关节运行在 **POS_VEL 模式**，配置里 `pos_vel_velocity = 150 °/s`，电机内部把转速**限死在 150 °/s**。主臂动得比这快时，从臂物理上追不上不断前移的目标，只能一直滞后追赶。

- 60 Hz 下目标每 16.67 ms 更新一次，从臂一帧最多走 `150 × 0.0167 ≈ 2.5°`；主臂一帧超过 ~2.5°（即 > 150 °/s）就跟不上。
- 各关节滞后量不同 → 中间姿态对不上任何真实主臂姿态 → 看起来「错乱」。
- 日志里 `Teleop loop time: 16.67ms (60 Hz)` 说明循环稳定在 60 Hz，通信带宽不是瓶颈。
- 命令链：`send_action()` 用配置里固定的 `pos_vel_velocity` 调 `send_pos_vel(pos, vel)`（`seeed_b601_follower.py:334-347`）。

**调优方案（按优先级）**：

1. **调高 `pos_vel_velocity`（主要旋钮）**：150 °/s ≈ 2.6 rad/s 对 DM 电机偏保守。逐步加大测试：

   ```bash
   --robot.pos_vel_velocity='[400,400,400,400,400,400,400]'
   ```

   按 300 → 400 → 600 逐档试。注意：太高会抖动、过冲，甚至电流冲击把舵机打成红灯（error state）。

2. **提高 `fps`**（如 `--fps=100`）：目标步长更小、插值更平滑，但**不解除速度上限**，作用次要。

3. **速度前馈（需改代码，最佳方案）**：在 `send_action()` 里用主臂实时关节速度（Δ角度 / Δt）作为 `send_pos_vel` 的 `vel`，从臂就按主臂实际速度跟随，无需固定折中值。

4. **与 drift bug 的联动**：若「错乱」表现为手臂突然甩向零位，那不是滞后，而是未修复的 drift bug——提速更容易触发舵机红灯 → `get_state()` 返回 `None` → 上报 `0.0`。提速前建议先做 `FOLLOWER_DRIFT_ANALYSIS.md` 的修复。
