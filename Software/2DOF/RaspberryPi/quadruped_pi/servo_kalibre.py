"""
servo_kalibre.py
================
Interaktif tek servo kontrolu.

Terminalden kanal numarasi ve aci yazarsin, servo o konuma gider.
Servo hareket etmesi gereken yere gidip gitmedigini gormek icin kullan.

KULLANIM:
    python servo_kalibre.py

KOMUTLAR (Enter ile gonder):
    0 90      -> Kanal 0'a 90 derece git
    1 45      -> Kanal 1'e 45 derece git
    0 +5      -> Kanal 0'in mevcut acisina +5 ekle
    0 -10     -> Kanal 0'in mevcut acisina -10 ekle
    sweep 0   -> Kanal 0'i 0->180 sureyle suprer (yon test)
    all 90    -> Tum kullanilan kanallari 90'a al
    release   -> Tum servolari serbest birak (PWM kes)
    show      -> Mevcut servo acilarini yazdir
    q         -> Cikis

NOT:
    Bu script servo SERVO_RANGE_DEG araliginda (0-180 derece) calisir,
    config.SERVO_CENTER, SERVO_DIRECTION, SERVO_OFFSET dikkate ALMAZ.
    Yani direkt fiziksel servo acisi gonderirsin.
"""

import time
import sys

import config
from adafruit_servokit import ServoKit


def main():
    print("=" * 60)
    print(" SERVO KALIBRASYON ARACI")
    print(" Kanal 0-7: RF, RH, LH, LF (hip, knee)")
    print("=" * 60)
    print()

    # PCA9685 baglanti
    try:
        kit = ServoKit(channels=16, address=config.PCA9685_I2C_ADDRESS)
    except Exception as exc:
        print(f"HATA: PCA9685 baglantisi kurulamadi: {exc}")
        print("Kontrol et: i2cdetect -y 1 -> 0x40 gorunuyor mu?")
        return 1

    # Kullanilan kanallari yapilandir (RF, RH, LH, LF = 0-7)
    used_channels = []
    for leg in range(config.NUM_LEGS):
        for joint in range(config.NUM_JOINTS):
            ch = config.SERVO_CHANNELS[leg][joint]
            kit.servo[ch].set_pulse_width_range(
                config.SERVO_PULSE_MIN_US,
                config.SERVO_PULSE_MAX_US,
            )
            kit.servo[ch].actuation_range = int(config.SERVO_RANGE_DEG)
            used_channels.append(ch)

    print(f"PCA9685 baglandi @ 0x{config.PCA9685_I2C_ADDRESS:02X}")
    print(f"Kullanilan kanallar: {sorted(used_channels)}")
    print()

    # Her kanalin mevcut acisini takip et
    current_angles = {ch: None for ch in used_channels}

    # Kanal -> bacak/eklem ismi (gosterim icin)
    def channel_label(ch):
        for leg in range(config.NUM_LEGS):
            for joint in range(config.NUM_JOINTS):
                if config.SERVO_CHANNELS[leg][joint] == ch:
                    leg_name = config.LEG_NAMES[leg]
                    joint_name = "hip" if joint == config.JOINT_HIP else "knee"
                    return f"{leg_name}-{joint_name}"
        return f"ch{ch}"

    print_help()

    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCikiliyor...")
            break

        if not cmd:
            continue

        # Cikis
        if cmd in ("q", "quit", "exit"):
            print("Cikiliyor...")
            break

        # Yardim
        if cmd in ("h", "help", "?"):
            print_help()
            continue

        # Tum servolari serbest birak
        if cmd == "release":
            for ch in used_channels:
                kit.servo[ch].angle = None
                current_angles[ch] = None
            print(">>> Tum servolar PWM kesildi (serbest)")
            continue

        # Mevcut durumu goster
        if cmd == "show":
            print("\nMevcut servo acilari:")
            for ch in sorted(used_channels):
                a = current_angles[ch]
                a_str = f"{a:6.1f}" if a is not None else " -----"
                print(f"  Kanal {ch}  ({channel_label(ch):>8s}): {a_str} derece")
            continue

        # Sweep test (0 -> 180 -> 0)
        if cmd.startswith("sweep"):
            parts = cmd.split()
            if len(parts) < 2:
                print("Kullanim: sweep <kanal>")
                continue
            try:
                ch = int(parts[1])
            except ValueError:
                print("Kanal numarasi gecersiz")
                continue
            if ch not in used_channels:
                print(f"Kanal {ch} kullanim disi")
                continue

            print(f">>> Kanal {ch} ({channel_label(ch)}) sweep: 0 -> 180 -> 90")
            print("    (Ctrl+C ile durdur)")
            try:
                for angle in range(0, 181, 10):
                    kit.servo[ch].angle = float(angle)
                    current_angles[ch] = float(angle)
                    print(f"    {angle} derece", end="\r")
                    time.sleep(0.15)
                for angle in range(180, -1, -10):
                    kit.servo[ch].angle = float(angle)
                    current_angles[ch] = float(angle)
                    print(f"    {angle} derece", end="\r")
                    time.sleep(0.15)
                # 90'da bitir
                kit.servo[ch].angle = 90.0
                current_angles[ch] = 90.0
                print(f"    Sweep bitti. Kanal {ch} -> 90 derece")
            except KeyboardInterrupt:
                print("\n    Sweep iptal edildi")
            continue

        # Tum kanallari ayni acya al
        if cmd.startswith("all"):
            parts = cmd.split()
            if len(parts) < 2:
                print("Kullanim: all <aci>")
                continue
            try:
                angle = float(parts[1])
            except ValueError:
                print("Aci gecersiz")
                continue
            angle = clamp(angle, 0.0, 180.0)
            for ch in used_channels:
                kit.servo[ch].angle = angle
                current_angles[ch] = angle
            print(f">>> Tum kanallar -> {angle} derece")
            continue

        # Tek kanal komutu: "<ch> <angle>" veya "<ch> +<delta>" / "<ch> -<delta>"
        parts = cmd.split()
        if len(parts) < 2:
            print("Komut anlasilamadi. 'help' yaz.")
            continue

        try:
            ch = int(parts[0])
        except ValueError:
            print(f"Kanal numarasi gecersiz: {parts[0]}")
            continue

        if ch not in used_channels:
            print(f"Kanal {ch} kullanim disi (gecerli: {sorted(used_channels)})")
            continue

        target_str = parts[1]

        # Delta mi (+5 / -10) yoksa mutlak deger mi?
        if target_str.startswith("+") or target_str.startswith("-"):
            try:
                delta = float(target_str)
            except ValueError:
                print(f"Delta gecersiz: {target_str}")
                continue

            if current_angles[ch] is None:
                base = 90.0
                print(f"    Mevcut aci bilinmiyor, 90'dan basliyor")
            else:
                base = current_angles[ch]

            new_angle = clamp(base + delta, 0.0, 180.0)
        else:
            try:
                new_angle = float(target_str)
            except ValueError:
                print(f"Aci gecersiz: {target_str}")
                continue
            new_angle = clamp(new_angle, 0.0, 180.0)

        kit.servo[ch].angle = new_angle
        current_angles[ch] = new_angle
        print(f"    Kanal {ch} ({channel_label(ch)}) -> {new_angle:.1f} derece")

    # Cikistan once tum servolari serbest birak
    print("\nServolari serbest birakiyorum...")
    for ch in used_channels:
        try:
            kit.servo[ch].angle = None
        except Exception:
            pass

    return 0


def clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def print_help():
    print("Komutlar:")
    print("  <kanal> <aci>     ornek: 0 90    -> kanal 0'a 90 derece")
    print("  <kanal> +<delta>  ornek: 0 +5    -> kanal 0'a +5 ekle")
    print("  <kanal> -<delta>  ornek: 0 -10   -> kanal 0'a -10 ekle")
    print("  sweep <kanal>     ornek: sweep 0 -> 0->180->0 sweep")
    print("  all <aci>         ornek: all 90  -> hepsi 90'a")
    print("  show              -> mevcut acilari yazdir")
    print("  release           -> PWM kes, servolar serbest kalsin")
    print("  q                 -> cikis")
    print()
    print("Kanal haritasi:")
    for leg in range(config.NUM_LEGS):
        hip_ch, knee_ch = config.SERVO_CHANNELS[leg]
        print(f"  {config.LEG_NAMES[leg]}: hip=kanal {hip_ch}, knee=kanal {knee_ch}")


if __name__ == "__main__":
    sys.exit(main())
