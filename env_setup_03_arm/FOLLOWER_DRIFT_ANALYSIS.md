# Follower Arm Drift 问题分析

## 现象

Follower arm（B601-DM）运行时角度不准、出现漂移，偶尔手臂突然甩向零位。
管理员反馈：舵机状态指示灯有时变红，此时舵机不收信号。

---

## 根本原因

舵机变红（error state）后停止响应 CAN 消息，`motor.get_state()` 返回 `None`。

当前库的 `get_observation()`（`seeed_b601_follower.py:273`）在读不到状态时直接用 `0.0` 填充：

```python
state = motor.get_state()
if state is not None:
    obs_dict[f"{motor_name}.pos"] = math.degrees(state.pos)
else:
    obs_dict[f"{motor_name}.pos"] = 0.0   # ← 漂移根源
```

触发链：**舵机红灯 → 读不到状态 → 位置报告为 0° → follower 收到 0° 指令 → 手臂突然甩向零位**

---

## 与 reBotArm_control_py 的对比

参考仓库：https://github.com/vectorBH6/reBotArm_control_py

| 方面 | 当前 lerobot seeed 插件 | reBotArm_control_py |
|------|------------------------|----------------------|
| **初始化 enable** | `enable_all()` 一次性调用，不验证状态 | `enable_all()` → 轮询状态码（0=disabled, 1=enabled）→ 最多重试 10+ 次，确认全绿才继续 |
| **读不到状态时的 fallback** | 直接用 `0.0`，**触发错误指令** | 用上一帧已知位置，不发新指令 |
| **运行中错误恢复** | 无 | 检测到红灯 → `clear_error()` + `enable()` 重新唤醒 |
| **通信异常处理** | `poll_feedback_once()` 失败只打 warning，继续跑 | 捕获 `CallError`，不让异常终止控制循环 |
| **断开时** | 有 `motor.clear_error()` | 同样有 |

---

## 修复方案

两处改动，均在 `vendor/lerobot-robot-seeed-b601/lerobot_robot_seeed_b601/seeed_b601_follower.py`，不需要动 lerobot 主库。

### 改动 1：`get_observation()` fallback 改为保持上一帧位置

读不到状态时不返回 `0.0`，而是返回上一帧缓存的角度，follower 就地保持，不乱跑。

```python
# 在 __init__ 里初始化缓存
self._last_obs: dict[str, float] = {}

# get_observation() 里
state = motor.get_state()
if state is not None:
    pos = math.degrees(state.pos)
    self._last_obs[motor_name] = pos          # 更新缓存
else:
    pos = self._last_obs.get(motor_name, 0.0) # 用上一帧，而非 0
obs_dict[f"{motor_name}.pos"] = pos
```

### 改动 2：`configure()` / 控制循环加错误恢复

检测到电机状态异常时，调 `clear_error()` + `enable()` 把它从红变绿。

```python
# configure() 里 ensure_mode 失败时，先尝试清错误再重试
motor.clear_error()
time.sleep(MEDIUM_TIMEOUT_SEC)
motor.enable()
time.sleep(MEDIUM_TIMEOUT_SEC)
motor.ensure_mode(target_mode)
```

---

## 文件索引

| 文件 | 说明 |
|------|------|
| `vendor/lerobot-robot-seeed-b601/lerobot_robot_seeed_b601/seeed_b601_follower.py` | 需要修改的核心文件 |
| `vendor/lerobot-robot-seeed-b601/lerobot_robot_seeed_b601/seeed_b601_dm_follower.py` | DM 电机子类，无需改动 |
