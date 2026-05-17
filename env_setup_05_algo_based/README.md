# env_setup_05_algo_based — Cookie Detection + Trajectory Replay

No ML training. Simple CV detection + recorded trajectory replay via leader+follower teleoperation.

## Workflow

```
Calibrate arms → Record trajectories → Calibrate cookie color → Run demo
```

---

## Step 1: Calibrate arms

Both arms must share the same home position before recording.

```bash
bash calibrate.sh
```

- Deletes old follower calibration and sets current position as zero
- Prompts to calibrate leader arm (type `c` + ENTER when ready)

---

## Step 2: Record trajectories

Record any named trajectory with leader+follower teleoperation:

```bash
bash record.sh <name>
```

Examples:
```bash
bash record.sh left              # move arm to left
bash record.sh right             # move arm to right
bash record.sh bringcookie_to_cup
```

Controls during recording:
- `→` right arrow — save episode
- `←` left arrow  — discard episode
- `Esc`           — stop recording

Data saved to `datasets_<name>/data/chunk-000/file-000.parquet`.

---

## Step 3: Calibrate cookie color

Place the cookie in view of the top camera:

```bash
python detect_cookie.py
```

Click on the cookie 5–10 times → press ENTER → saves `cookie_color.json`.

Preview detection live:
```bash
python detect_cookie.py preview
```

---

## Step 4: Replay a trajectory

```bash
python replay.py <name>
```

Examples:
```bash
python replay.py left
python replay.py bringcookie_to_cup
```

---

## Step 5: Run demo

Detect cookie → automatically replay corresponding trajectory:

```bash
python demo.py           # detect once, execute once
python demo.py --loop    # keep looping
```

---

## File structure

```
env_setup_05_algo_based/
├── calibrate.sh           # calibrate both arms to same home position
├── record.sh              # record any named trajectory (leader+follower)
├── replay.py              # replay a recorded trajectory on follower arm
├── detect_cookie.py       # cookie color calibration + CookieDetector class
├── demo.py                # main demo: detect cookie → replay trajectory
├── _calibrate_follower.py # helper: calibrate follower arm only
├── record_left.sh         # shortcut: record "left" trajectory
└── record_right.sh        # shortcut: record "right" trajectory
```

## Environment

```bash
source /Users/jian/workspace/robot_painting/env_setup_03_arm/venv/bin/activate
```

`record.sh` activates the venv automatically. `replay.py` and `demo.py` need it activated manually.
