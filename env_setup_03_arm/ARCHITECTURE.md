# 系统架构

```mermaid
flowchart TD
    subgraph lerobot["lerobot 框架"]
        direction LR
        record["lerobot-record\n数据采集"] ~~~ train["lerobot-train\n训练 ACT / Diffusion"] ~~~ eval["lerobot-eval\n推理"] ~~~ teleop["lerobot-teleoperate\n遥操作"]
    end

    subgraph plugin["lerobot-robot-seeed-b601 插件   ⚠️ 漂移 bug 在这里"]
        direction LR
        obs["get_observation()\n电机角度 + 摄像头图像"] ~~~ action["send_action()\n发位置指令"] ~~~ configure["configure()\n初始化 / 错误恢复"]
    end

    subgraph sdk["motorbridge SDK"]
        can["CAN 总线 / 串口通信"]
    end

    subgraph hw["硬件"]
        direction LR
        star["Star Arm 102\n主臂"] ~~~ b601["B601-DM\n从臂"] ~~~ cam["USB 摄像头"]
    end

    lerobot -->|"调用 Robot 接口"| plugin
    plugin -->|"CAN 指令"| sdk
    sdk --> b601
    plugin -->|"读帧"| cam

    style plugin fill:#fff3cd,stroke:#ffc107
    style lerobot fill:#d1ecf1,stroke:#0c5460
    style sdk fill:#f8f9fa,stroke:#6c757d
    style hw fill:#d4edda,stroke:#155724
```

---

## 标准流程：数据收集 → 训练 → 推理

```mermaid
flowchart LR
    subgraph collect["① 数据收集  lerobot-record"]
        direction TB
        human["人操控主臂"] --> follower["从臂跟随执行"]
        follower --> dataset["存入数据集\n关节角度 + 摄像头图像\n（每条 episode）"]
    end

    subgraph train["② 训练  lerobot-train"]
        direction TB
        dataset2["读取数据集"] --> nn["神经网络学习\nACT / Diffusion Policy\n图像 + 角度 → 下一步动作"]
        nn --> ckpt["保存模型权重"]
    end

    subgraph eval["③ 推理  lerobot-eval"]
        direction TB
        cam2["摄像头实时图像"] --> policy["加载模型\n自主决策"]
        policy --> robot["发指令给从臂\n无需人操控"]
    end

    collect -->|"50+ episodes"| train
    train -->|"训练好的权重"| eval
```

### 各阶段说明

| 阶段 | 谁在控制从臂 | 摄像头作用 | 输出 |
|------|------------|-----------|------|
| **数据收集** | 人（通过主臂） | 录像，和角度一起存 | 数据集 |
| **训练** | 无（离线） | 作为网络输入特征 | 模型权重 |
| **推理** | 神经网络 | 实时输入，驱动决策 | 机器人自主行动 |
