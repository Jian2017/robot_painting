# Demo 准备计划（2026-05-16，明天）

Demo 时间：2026-05-17
目标：机器人拿笔，看到桌面纸张，模仿绘画动作。

---

## 现实评估

"看到图像 → 继续画画"是**视觉条件模仿学习**任务，完整链路：采数据 → 训练 → 推理。

两天内可做到的版本：**模仿固定绘画动作**（如画圆、简单图案），而不是真正理解"已画了什么、下一步画哪里"——后者是研究级问题。

**最坏情况 fallback**：直接展示 teleoperate——人操主臂画画、从臂跟随，今天已跑通，同样有说服力。

---

## 今天已完成（2026-05-15）

- [x] 环境搭建（lerobot + B601-DM follower + Star Arm 102 leader）
- [x] 两臂联调成功，60Hz 稳定运行
- [x] 串口对应关系确认（`cu.usbserial-10` 主臂，`cu.usbmodem00000000050C1` 从臂）
- [x] 定位 follower arm 漂移根本原因（见 `FOLLOWER_DRIFT_ANALYSIS.md`）

---

## 明天全天计划

### 上午：修硬件 + 接摄像头（必须完成）

#### 1. 修漂移（1-2小时）🔴 最高优先级

不修此问题，录制的数据全部无效。

改动文件：`vendor/lerobot-robot-seeed-b601/lerobot_robot_seeed_b601/seeed_b601_follower.py`

- `get_observation()`：fallback 改为保持上一帧缓存位置，而非返回 `0.0`
- `configure()`：加 `clear_error()` + `enable()` 错误恢复逻辑

详见 `FOLLOWER_DRIFT_ANALYSIS.md`。

#### 2. 接摄像头（30分钟）🔴

```bash
source venv/bin/activate
lerobot-find-cameras   # 找摄像头 index
```

至少一个**俯视摄像头**固定在桌面正上方，验证能稳定出图。

#### 3. 搭桌面环境（30分钟）🔴

- 桌面铺纯色布（白色或黑色）
- 画布/纸固定位置，胶带标记四角，每次放同一位置
- 关窗帘，台灯固定光照，消除自然光变化
- 机械臂装好笔，确认笔尖能接触纸面

---

### 下午：采数据（核心）

#### 4. 验证完整链路（30分钟）

```bash
lerobot-teleoperate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.cameras.top_cam.type=opencv \
  --robot.cameras.top_cam.index_or_path=0 \
  --robot.cameras.top_cam.fps=30 \
  --robot.cameras.top_cam.width=640 \
  --robot.cameras.top_cam.height=480 \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-10 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}'
```

确认摄像头图像正常、臂无漂移后再开始录数据。

#### 5. 录数据（2-3小时）🔴 目标 50 条以上

```bash
lerobot-record \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.cameras.top_cam.type=opencv \
  --robot.cameras.top_cam.index_or_path=0 \
  --robot.cameras.top_cam.fps=30 \
  --robot.cameras.top_cam.width=640 \
  --robot.cameras.top_cam.height=480 \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/cu.usbserial-10 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}' \
  --dataset.repo_id=local/painting_demo \
  --dataset.num_episodes=50
```

**录制要求**：
- 每条 demo 画同一个图案（建议：圆形或简单曲线），保持动作一致
- 画布每次放回胶带标记位置
- 质量优先于数量：50 条好的 > 100 条乱的

---

### 傍晚：开始训练（跑过夜）

#### 6. 启动训练 🟡

```bash
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=local/painting_demo \
  --output_dir=outputs/painting_act
```

选 ACT（Action Chunking Transformer），比 Diffusion Policy 训练快，适合紧急情况。让它跑一整夜。

---

### Demo 当天早上：推理测试

#### 7. 推理验证 🟡

```bash
lerobot-eval \
  --policy.path=outputs/painting_act/checkpoints/last \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/cu.usbmodem00000000050C1 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.cameras.top_cam.type=opencv \
  --robot.cameras.top_cam.index_or_path=0 \
  --robot.cameras.top_cam.fps=30 \
  --robot.cameras.top_cam.width=640 \
  --robot.cameras.top_cam.height=480
```

效果不好还有半天可以调整或切换到 fallback 方案。

---

## 优先级汇总

| 优先级 | 任务 | 不做的后果 |
|--------|------|-----------|
| 🔴 必做 | 修漂移 | 数据无效，demo 失控 |
| 🔴 必做 | 摄像头接通 | 无视觉输入 |
| 🔴 必做 | 搭桌面环境 | 数据质量差，训练失败 |
| 🔴 必做 | 采数据 50 条 | 无训练集 |
| 🟡 重要 | 训练 ACT | 退化为 teleoperate replay |
| 🟢 可选 | 推理调优 | 视训练结果而定 |
