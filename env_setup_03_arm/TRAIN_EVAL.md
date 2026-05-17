# ACT 训练与部署到机器人

## 数据集

同事录制的数据，3 episodes，1504 帧，2 个摄像头：

```
/Users/jian/workspace/robot_painting/data/painting_demo_with_2camera/
├── meta/info.json          # total_episodes=3, fps=30
├── data/chunk-000/         # 关节角度 parquet
└── videos/
    ├── observation.images.top_cam/
    └── observation.images.side_cam/
```

## 前置：安装 FFmpeg

torchcodec（lerobot 默认视频解码器）不支持 Homebrew 安装的 FFmpeg 8，需要先装 ffmpeg 并改用 pyav 后端：

```bash
brew install ffmpeg
```

## 训练

```bash
source venv/bin/activate
lerobot-train \
  --dataset.repo_id=painting_demo_with_2camera \
  --dataset.root=/Users/jian/workspace/robot_painting/data/painting_demo_with_2camera \
  --dataset.video_backend=pyav \
  --policy.type=act \
  --policy.device=mps \
  --policy.repo_id=local/act_painting_test \
  --policy.push_to_hub=false \
  --batch_size=4 \
  --steps=200 \
  --output_dir=/Users/jian/workspace/robot_painting/outputs/act_painting_test \
  --log_freq=10 \
  --eval_freq=200
```

关键参数说明：
- `--dataset.video_backend=pyav`：绕开不支持 FFmpeg 8 的 torchcodec
- `--policy.push_to_hub=false`：不上传到 HuggingFace Hub（需要登录）
- `--policy.device=mps`：macOS GPU
- `--steps=200`：200 步只是验证流程，实际需要 10000+ 步

训练输出（200 步示例）：
```
step:10  loss:8.120
step:100 loss:5.051
step:200 loss:3.988   ← 还未收敛，仅做流程验证
```

模型保存到：
```
outputs/act_painting_test/checkpoints/000200/pretrained_model/
├── model.safetensors          # 197MB，51.6M 参数
├── config.json
├── policy_preprocessor_*.safetensors   # 归一化统计
└── policy_postprocessor_*.safetensors
```

## 推理（部署到真实机器人）

### 为什么不用 `lerobot-eval`

`lerobot-eval` 的 `gym_manipulator` 环境需要额外安装 `gym_gym_manipulator` 包（HILSerl 框架），对真实机器人推理过重。直接写脚本更简单。

### 修改 lerobot_eval.py（附带修复，供参考）

`lerobot-eval` 解析相机参数时找不到 `opencv` 类型（因为 `OpenCVCameraConfig` 没有被导入），在文件头加了一行：

```python
# vendor/lerobot/src/lerobot/scripts/lerobot_eval.py 第72行
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
```

（`lerobot-teleoperate` 已有这行，`lerobot-eval` 原来没有。）

### 推理脚本

`run_act_eval.py`（在 `env_setup_03_arm/` 目录）：

```bash
source venv/bin/activate
python run_act_eval.py
```

脚本核心逻辑：

```python
model = ACTPolicy.from_pretrained(CHECKPOINT)
dataset_metadata = LeRobotDatasetMetadata(DATASET_ID, root=DATASET_ROOT)
preprocess, postprocess = make_pre_post_processors(model.config, dataset_stats=dataset_metadata.stats)

robot.connect(calibrate=False)

for step in range(MAX_STEPS_PER_EPISODE):
    obs = robot.get_observation()
    obs_frame = build_inference_frame(obs, ds_features=dataset_metadata.features, device=device)
    action = model.select_action(preprocess(obs_frame))
    robot.send_action(make_robot_action(postprocess(action), dataset_metadata.features))
    time.sleep(1 / FPS)
```

可调参数（脚本顶部）：
- `MAX_STEPS_PER_EPISODE = 900`：控制每次 eval 运行时长（900步 ≈ 30秒）
- `MAX_EPISODES = 1`：运行几轮

## 提升质量

| 当前 | 目标 |
|------|------|
| 3 episodes | 50+ episodes |
| 200 训练步 | 10000–50000 步 |
| loss ≈ 4.0 | loss ≈ 0.5 以下 |

正式训练命令（跑一晚上）：

```bash
source venv/bin/activate
lerobot-train \
  --dataset.repo_id=painting_demo_with_2camera \
  --dataset.root=/Users/jian/workspace/robot_painting/data/painting_demo_with_2camera \
  --dataset.video_backend=pyav \
  --policy.type=act \
  --policy.device=mps \
  --policy.repo_id=local/act_painting_v1 \
  --policy.push_to_hub=false \
  --batch_size=4 \
  --steps=10000 \
  --output_dir=/Users/jian/workspace/robot_painting/outputs/act_painting_v1 \
  --log_freq=100 \
  --eval_freq=10000
```

训练完修改 `run_act_eval.py` 里的 `CHECKPOINT` 路径再 eval：

```python
CHECKPOINT = "/Users/jian/workspace/robot_painting/outputs/act_painting_v1/checkpoints/010000/pretrained_model"
```
