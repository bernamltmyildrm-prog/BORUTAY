"""
test_gyro.py
============
MPU-6050 gyro.py icin hizli test dosyasi.

Calistirma:
    python test_gyro.py

Windows'ta veya IMU yokken:
    FakeGyro modunda calisir.

Raspberry Pi'de MPU-6050 bagliyken:
    Gercek roll/pitch okumaya calisir.
"""

import time
from gyro import GyroProc


gyro = GyroProc(use_fake_if_missing=True)

print("=" * 85)
print("MPU-6050 GYROPROC TEST")
print("=" * 85)
print(
    f"{'step':>4} | {'roll':>8} | {'pitch':>8} | "
    f"{'yaw':>8} | {'pitch corr':>11} | {'roll corr':>10} | mode"
)
print("-" * 85)

try:
    for i in range(100):
        state = gyro.update(dt=0.02)

        if i % 5 == 0:
            mode = "FAKE" if state.fake_mode else "REAL"
            print(
                f"{i:4d} | "
                f"{state.roll_deg:8.3f} | "
                f"{state.pitch_deg:8.3f} | "
                f"{state.yaw_deg:8.3f} | "
                f"{state.pitch_correction_mm:11.3f} | "
                f"{state.roll_correction_mm:10.3f} | "
                f"{mode:>4}"
            )

        time.sleep(0.02)

finally:
    gyro.close()

print("\n>>> Test bitti.")