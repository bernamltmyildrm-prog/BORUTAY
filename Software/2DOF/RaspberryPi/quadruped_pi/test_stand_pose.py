"""
test_stand_pose.py
==================
8 servoyu hepsi birden config.SERVO_CENTER pozisyonuna alir.
Robot askida iken bacaklarin "ayakta" pozisyonuna gectiginden emin ol.

ASIRI GUVENLI BIR SCRIPT:
    Servolar hizli hareket etmesin diye basamakli (ramp) gidiyor.
    Mevcut konum -> hedef konum arasinda her servo 1 saniyede
    yumusakca hareket eder.

KULLANIM:
    1. Robot askida olsun (yere basmasin)
    2. python test_stand_pose.py
    3. 1-2 saniye icinde tum bacaklar stand pozisyonuna gecmeli
    4. Robot dengeli durmuyorsa Ctrl+C ile durdur

GUVENLIK:
    - Eger servo gariplikle ses cikariyorsa veya mekanik zorlanma varsa
      hemen Ctrl+C bas.
    - HardwareController set_servo_angle_direct() ile dogrudan
      SERVO_CENTER degerlerini gonderir, IK donusumu yapmaz.
"""

import time
import sys

import config
from hardware import HardwareController


RAMP_DURATION_S = 1.5   # mevcut konumdan SERVO_CENTER'a kac saniyede gidilsin
RAMP_STEPS = 30         # kac adimda


def main():
    print("=" * 60)
    print(" STAND POSE TESTI")
    print(" 8 servo SERVO_CENTER pozisyonuna ramp ile gidecek")
    print("=" * 60)
    print()
    print(" ROBOT ASKIDA OLSUN. Bacaklar yere basmasin.")
    print(" Hazirsan Enter, iptal icin Ctrl+C")
    try:
        input()
    except KeyboardInterrupt:
        print("\nIptal edildi")
        return 1

    # Donanim baslat (gercek mod)
    hw = HardwareController(real=True, verbose=False)
    if not hw.real:
        print("HATA: HardwareController gercek moda gecemedi.")
        print("PCA9685 baglantisini ve i2cdetect ciktisini kontrol et.")
        return 1

    # Hedef acilari hazirla (SERVO_CENTER'dan)
    targets = []  # (channel, target_angle, label) tuple listesi
    for leg in range(config.NUM_LEGS):
        for joint in range(config.NUM_JOINTS):
            channel = config.SERVO_CHANNELS[leg][joint]
            target = config.SERVO_CENTER[leg][joint]
            label = f"{config.LEG_NAMES[leg]}-{'hip' if joint == config.JOINT_HIP else 'knee'}"
            targets.append((channel, target, label))

    # Mevcut acilari oku — hardware.last_servo_angles kullaniyor
    # Daha once gonderilmis bir aci yoksa "merkez" varsayalim (90)
    current = {}
    for ch, _, _ in targets:
        current[ch] = hw.last_servo_angles.get(ch, 90.0)

    print()
    print("Hedef acilar (SERVO_CENTER):")
    for ch, target, label in targets:
        print(f"  Kanal {ch} ({label:>8s}): {current[ch]:6.1f} -> {target:6.1f}")
    print()
    print(f"Ramp suresi: {RAMP_DURATION_S:.1f} saniye, {RAMP_STEPS} adim")
    print()

    try:
        # Ramp dongusu
        dt = RAMP_DURATION_S / RAMP_STEPS
        for step in range(1, RAMP_STEPS + 1):
            ratio = step / RAMP_STEPS  # 0..1 arasinda
            for ch, target, _ in targets:
                start = current[ch]
                intermediate = start + (target - start) * ratio
                hw.set_servo_angle_direct(ch, intermediate)
            time.sleep(dt)

        print()
        print(">>> Stand pose pozisyonuna gidildi.")
        print(">>> Robot dengeli mi? Bacaklar dik mi?")
        print(">>> Ctrl+C ile cik ve servolari serbest birak.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nServolar serbest birakiliyor...")
        hw.release_all()
        print("Bitti.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
