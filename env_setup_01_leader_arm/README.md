# env_setup_leader_arm

Star Arm 102 Leader Arm 读取关节角度。

## 硬件

- **机械臂**: Seeed Studio Star Arm 102
- **电机**: Fashion Star RA8 系列
- **供电**: 12V @ 2A，XT30 接口
- **USB 芯片**: CH340
- **波特率**: 1,000,000 bps

## 安装

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## 找串口

```bash
ls /dev/cu.usbserial-*
```

然后把 `read_leader_arm.py` 里的 `PORT` 改成对应的端口。

## 运行

```bash
venv/bin/python read_leader_arm.py
```
