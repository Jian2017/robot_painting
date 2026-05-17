import sys, time
sys.path.insert(0, 'vendor/lerobot-robot-seeed-b601')
from lerobot_robot_seeed_b601.seeed_b601_dm_follower import SeeedB601DMFollower
from lerobot_robot_seeed_b601.config_seeed_b601_dm_follower import SeeedB601DMFollowerConfig

cfg = SeeedB601DMFollowerConfig(
    port='/dev/cu.usbmodem00000000050C1',
    id='follower1',
    can_adapter='damiao',
)
robot = SeeedB601DMFollower(cfg)
robot.connect(calibrate=True)
robot.disconnect()
print("Follower calibration done.")
