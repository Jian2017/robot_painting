# 系统架构

```mermaid
flowchart TD
    subgraph lerobot["lerobot（别人写好的框架）"]
        record["lerobot-record\n数据采集"]
        train["lerobot-train\n神经网络训练\nACT / Diffusion Policy"]
        eval["lerobot-eval\n推理执行"]
        teleop["lerobot-teleoperate\n遥操作"]
    end

    subgraph plugin["lerobot-robot-seeed-b601（Seeed 插件）⚠️ 漂移 bug 在这里"]
        follower["seeed_b601_follower.py\n硬件抽象层"]
        connect["connect()"]
        obs["get_observation()\n读电机角度"]
        action["send_action()\n发位置指令"]
        configure["configure()\n初始化 / 错误恢复"]
    end

    subgraph sdk["motorbridge SDK（不需要动）"]
        can["CAN 总线 / 串口通信"]
    end

    subgraph hw["硬件"]
        b601["B601-DM 从臂\nDamiao 电机"]
        star["Star Arm 102 主臂\nFashion Star 舵机"]
    end

    lerobot -->|"调用 Robot 接口"| plugin
    plugin -->|"CAN 指令"| sdk
    sdk -->|"物理连接"| hw

    style plugin fill:#fff3cd,stroke:#ffc107
    style lerobot fill:#d1ecf1,stroke:#0c5460
    style sdk fill:#f8f9fa,stroke:#6c757d
    style hw fill:#d4edda,stroke:#155724
```

## 各层职责

| 层 | 代码 | 职责 | 需要改动？ |
|----|------|------|-----------|
| **lerobot 框架** | `vendor/lerobot` | 数据格式、训练循环、神经网络（ACT 等）、推理 | 否 |
| **Seeed 插件** | `vendor/lerobot-robot-seeed-b601` | 把 lerobot 抽象指令翻译为 CAN 命令，读写电机状态 | **是（修漂移）** |
| **motorbridge SDK** | pip 包 | CAN/串口底层通信 | 否 |
| **硬件** | B601-DM、Star Arm 102 | 执行物理动作 | — |

## 漂移 bug 位置

`seeed_b601_follower.py` → `get_observation()`：电机变红停止响应时，返回 `0.0°` 而非上一帧位置，lerobot 不感知，直接把 `0°` 当作目标发出去，导致手臂甩向零位。

详见 [`FOLLOWER_DRIFT_ANALYSIS.md`](./FOLLOWER_DRIFT_ANALYSIS.md)。
