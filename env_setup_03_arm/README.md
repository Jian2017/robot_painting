# env_setup_03_arm — LeRobot + Leader (Star Arm 102) + Follower (reBot B601-DM)

在本目录做**独立、可复现**的环境：LeRobot 能同时连接 **Star Arm 102（主臂 / teleop）** 与 **reBot Arm B601-DM（从臂 / robot）**。流程对齐 Seeed Wiki，使用 **Seeed 维护的 `lerobot` 源码** 与两个官方插件包（editable install），而不是只用 PyPI 上的通用 `lerobot` wheel。

## 官方资料（你提供的链接）

| 内容 | 链接 |
|------|------|
| reBot DevArm GitHub | https://github.com/Seeed-Projects/reBot-DevArm |
| B601-DM 产品页 | https://www.seeedstudio.com/reBot-Arm-B601-DM-p-6740.html |
| Star Arm 102（Leader）产品页 | https://www.seeedstudio.com/Star-Arm-102-p-6765.html |
| B601-DM 上手（组装/校准；出厂已预校准可从 Step 3 开始） | https://wiki.seeedstudio.com/rebot_b601_dm_getting_started/ |
| Pinocchio & Meshcat | https://wiki.seeedstudio.com/rebot_arm_b601_dm_pinocchio_meshcat/ |
| **LeRobot 集成（本文主要依据）** | https://wiki.seeedstudio.com/rebot_arm_b601_dm_lerobot/ |
| Leader 插件仓库 | https://github.com/Seeed-Projects/lerobot-teleoperator-rebot-arm-102 |
| ROS 2 | https://wiki.seeedstudio.com/rebot_arm_b601_dm_ros2_integration/ |
| 视觉抓取 Demo | https://wiki.seeedstudio.com/rebot_arm_b601_dm_grasping_demo/ |

## 目录约定（保持干净）

- `venv/`：虚拟环境（已 `.gitignore`，不要提交）。
- `vendor/`：三个 git 仓库克隆目录（已 `.gitignore`）。
- 需要**从零重来**时：删掉 `venv/` 和 `vendor/`，再跑一遍 bootstrap。

## 系统要求（与 Wiki 对齐）

- Wiki 推荐 **Python 3.12**（Conda 示例）；本目录用 **`python3.12 -m venv`**；若无 3.12，把 `bootstrap.sh` 里的 `PYTHON` 改成你的解释器再试。
- **Ubuntu + NVIDIA**：按 Wiki 装匹配 CUDA 的 PyTorch；装完 `lerobot` 后务必检查 `torch.cuda.is_available()` 是否为 `True`（editable 安装有时会带上 CPU 版 torch，需按 [PyTorch 官网](https://pytorch.org/) 纠正）。
- **macOS**：无 CUDA，一般用 **CPU 或 MPS**；串口名与 Linux 不同（见下）。

## 一键 bootstrap

```bash
cd env_setup_03_arm
chmod +x bootstrap.sh
./bootstrap.sh
```

脚本会：

1. 创建 `venv/`（若不存在）。
2. 在 `vendor/` 浅克隆并（再次运行时）`git pull`：
   - `https://github.com/Seeed-Projects/lerobot.git`
   - `https://github.com/Seeed-Projects/lerobot-teleoperator-rebot-arm-102.git`
   - `https://github.com/Seeed-Projects/lerobot-robot-seeed-b601.git`
3. `pip install -e` 上述三者，并 `pip install motorbridge`。

**ffmpeg**：Wiki 用 `conda install ffmpeg`；若你只用 venv，请用系统包管理器安装 `ffmpeg`（例如 `brew install ffmpeg`），保证命令行能运行 `ffmpeg`。

## 串口与权限

### Linux（Wiki 原文）

- Leader：`/dev/ttyUSB*`（Wiki）；从臂串口桥：`/dev/ttyACM*`。
- 权限示例：`sudo chmod 666 /dev/ttyUSB*`、`sudo chmod 666 /dev/ttyACM*`。
- 若 Leader 占用异常，Wiki 提到 **`brltty` 占用串口** 时需 `sudo apt remove brltty`（见 Wiki「Calibrate the Leader Arm」小节）。

### macOS（与本机 `SETUP.md` 一致）

- Star Arm 102（CH340）常为：`/dev/cu.usbserial-*`（波特率 Fashion Star 侧为 **1_000_000**，由插件/SDK 处理，无需在 `lerobot-calibrate` 里单独设）。
- B601 从臂桥接器可能是：`/dev/cu.usbmodem*` 等；用下面命令选实际路径：

```bash
source venv/bin/activate
lerobot-find-port
ls /dev/cu.*
```

## 校准（两台都要做）

校准文件在 Wiki 所述缓存目录（例如 `~/.cache/huggingface/lerobot/calibration/...`）。若要**彻底重校**，需按 Wiki 删除对应缓存再重新跑 `lerobot-calibrate`。

**从臂（B601-DM，Damiao 串口桥示例）：**

```bash
lerobot-calibrate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao
```

（macOS 把 `--robot.port=` 换成你的 `cu.*` 设备路径。）

**主臂（reBot Arm 102 / `rebot_arm_102_leader`）：**

```bash
lerobot-calibrate \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader
```

校完后可用插件自带脚本读原始角（路径以本目录 `vendor` 为准）：

```bash
source venv/bin/activate
python ./vendor/lerobot-teleoperator-rebot-arm-102/examples/read_raw_angles.py --port /dev/ttyUSB0
```

（同样，macOS 将 `--port` 改为 `/dev/cu.usbserial-...`。）

## 遥操作（Leader + Follower 同时在线）

Wiki 示例（Linux 端口）：

```bash
lerobot-teleoperate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --teleop.type=rebot_arm_102_leader \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader \
  --teleop.joint_directions='{"shoulder_pan":-1,"shoulder_lift":-1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":-1,"gripper":-4}'
```

**说明：**

- `--teleop.joint_directions` 与 Wiki 一致；若实际运动方向与预期相反，按 [lerobot-teleoperator-rebot-arm-102 README](https://github.com/Seeed-Projects/lerobot-teleoperator-rebot-arm-102) 调整。
- 安全提示见 Wiki「Teleoperate」：**断电/断信号前先停程序并把臂回到安全零位**，再上电重启，避免乱数导致失控。

## 与 `env_setup_01_leader_arm` 的关系

- `env_setup_01_leader_arm`：最小 venv + `fashionstar-uart-sdk`，适合单独验证串口读角。
- **本目录**：完整 LeRobot + Seeed 双插件，用于 **`lerobot-teleoperate` / `lerobot-record`** 与 B601 从臂联调。

## 可选：RealSense / Orbbec 相机分支

Wiki 说明深度相机支持在 **`DepthCameraSupport`** 分支；若需要，在 `vendor/lerobot` 内切换分支后重新 `pip install -e ".[realsense]"` 或 `".[orbbec]"`（以 Wiki 为准）。
