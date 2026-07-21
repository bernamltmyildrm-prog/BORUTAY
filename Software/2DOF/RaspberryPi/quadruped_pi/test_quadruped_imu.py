"""
test_quadruped_imu.py
=====================
IMU compensation ile quadruped testi (FakeGyro modunda).
Pitch arttikca on bacaklar uzar, arka bacaklar kisalir.
"""
import time
import config
from gyro import GyroProc
from quadruped import QuadRuped

gyro = GyroProc(use_fake_if_missing=True)
dog = QuadRuped(gyro=gyro)
dog.stand()

print(f"{'step':>5} | {'pitch':>7} | {'pitch_corr':>11} | "
      f"{'RF foot.z':>10} | {'RH foot.z':>10}")
print("-" * 65)

for i in range(50):
    targets = dog.update(config.CONTROL_LOOP_DT)
    if i % 3 == 0:
        pitch = dog.imu_state.pitch_deg if dog.imu_state else 0
        corr = dog.last_pitch_correction_mm
        rf_z = targets[config.LEG_RF].foot.z
        rh_z = targets[config.LEG_RH].foot.z
        print(f"{i:5d} | {pitch:7.2f} | {corr:11.2f} | "
              f"{rf_z:10.2f} | {rh_z:10.2f}")
    time.sleep(0.02)