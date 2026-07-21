"""
test_one_leg_rf.py
==================
RF / sag on tek bacak daha canli hareket testi.

RF HIP  -> channel 0
RF KNEE -> channel 1

Bu test ilk neutral testten sonra kullanilir.
Bacak havada ve serbest olmali.
"""

import time
import config
from hardware import HardwareController

RF = config.LEG_RF
HIP = config.JOINT_HIP
KNEE = config.JOINT_KNEE

def wait_user(msg):
    input("\n" + msg + "\nDevam icin Enter, durmak icin Ctrl+C...")

def main():
    print("=" * 70)
    print("RF / SAG ON TEK BACAK CANLI TEST")
    print("=" * 70)
    print("RF HIP  -> channel 0")
    print("RF KNEE -> channel 1")
    print()
    print("Kontrol:")
    print("  - Bacak havada/serbest")
    print("  - Servo mekanik sona dayanmiyor")
    print("  - XL4016 cikisi 5.9 V civari")
    print("  - Ortak GND var")
    print("=" * 70)

    wait_user("Hazirsan baslayalim.")

    hw = HardwareController(real=True, verbose=True)

    if not hw.real or hw.kit is None:
        print("HATA: PCA9685 baslatilamadi. I2C / 0x40 kontrol et.")
        return

    try:
        print("\n>>> 1) Stand pozisyonu")
        hw.set_joint_angle(RF, HIP, -54.49)
        hw.set_joint_angle(RF, KNEE, -79.40)
        time.sleep(1.0)

        wait_user("Stand pozisyonu normal ise devam.")

        print("\n>>> 2) HIP daha belirgin hareket")
        hip_angles = [
            -42.0,
            -50.0,
            -62.0,
            -54.49,
        ]

        for angle in hip_angles:
            hw.set_joint_angle(RF, HIP, angle)
            time.sleep(0.8)

        wait_user("HIP hareketi normal ise devam.")

        print("\n>>> 3) KNEE daha belirgin hareket")
        knee_angles = [
            -65.0,
            -79.40,
            -95.0,
            -79.40,
        ]

        for angle in knee_angles:
            hw.set_joint_angle(RF, KNEE, angle)
            time.sleep(0.8)

        wait_user("KNEE hareketi normal ise devam.")

        print("\n>>> 4) Bacak canlandirma / mini step")
        sequence = [
            (-45.0, -70.0),
            (-52.0, -82.0),
            (-62.0, -95.0),
            (-54.49, -79.40),
        ]

        for repeat in range(2):
            print(f"\n--- mini step cycle {repeat + 1} ---")
            for hip_deg, knee_deg in sequence:
                hw.set_joint_angle(RF, HIP, hip_deg)
                hw.set_joint_angle(RF, KNEE, knee_deg)
                time.sleep(0.45)

        print("\n>>> Test tamamlandi.")

    except KeyboardInterrupt:
        print("\n>>> Test durduruldu.")

    finally:
        print("\n>>> PWM release yapiliyor.")
        hw.release_all()
        print(">>> Bitti. Istersen servo gucunu kapat.")

if __name__ == "__main__":
    main()