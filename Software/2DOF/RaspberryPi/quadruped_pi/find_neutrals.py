"""
find_neutrals.py
================
Her bacagin hip ve knee servosu icin "stand pose" notr aci bulma rutini.

NE YAPAR:
    Her 8 servoyu sirayla acar, sen "+" / "-" tuslariyla bacak
    DIK ve DENGELI duruncaya kadar ayarlarsin. Buldugun degerleri
    config.py'deki SERVO_CENTER'a kopyalayabilirsin.

KULLANIM:
    1. Robot bir destege yaslanmis veya askida olsun (yere temas etmesin)
    2. python find_neutrals.py
    3. Her servo icin:
        - Servo SERVO_CENTER'daki mevcut degere gider
        - Sen tuslarla ayarlarsin:
            + veya =   -> +1 derece
            -          -> -1 derece
            ++         -> +5 derece
            --         -> -5 derece
            ok / Enter -> bu deger kabul, sonraki servoya gec
            skip       -> bu servoyu atla, eskisi kalsin
            q          -> cikis, buraya kadar bulduklarini yazdir

ONERILEN BASLANGIC POZISYONU (stand pose):
    HIP servo  : bacak dik asagi baksin (femur dikine inde)
    KNEE servo : tibia femure 90 derecede olsun (klasik stand)

CIKTI:
    Tum servolar gezildikten sonra ekrana config.py icin yapistirilacak
    format'ta SERVO_CENTER bloku basilir.
"""

import sys

import config
from adafruit_servokit import ServoKit


def main():
    print("=" * 70)
    print(" SERVO NOTR BULMA")
    print("=" * 70)
    print()
    print(" Her servo icin tuslar:")
    print("   +  =>  +1 derece")
    print("   ++ =>  +5 derece")
    print("   -  =>  -1 derece")
    print("   -- =>  -5 derece")
    print("   <sayi>  =>  o aciya direkt git (orn: 95)")
    print("   ok  veya Enter  =>  bu deger kabul, sonraki servoya gec")
    print("   skip => bu servoyu atla")
    print("   q   =>  cikis, buraya kadarini bas")
    print()
    print(" ROBOT ASKIDA OLSUN. Bacaklar yere basmasin.")
    print("=" * 70)
    print()

    input("Hazirsan Enter'a bas... ")

    # PCA9685
    try:
        kit = ServoKit(channels=16, address=config.PCA9685_I2C_ADDRESS)
    except Exception as exc:
        print(f"HATA: PCA9685 baglantisi: {exc}")
        return 1

    # Servo kanallarini hazirla
    for leg in range(config.NUM_LEGS):
        for joint in range(config.NUM_JOINTS):
            ch = config.SERVO_CHANNELS[leg][joint]
            kit.servo[ch].set_pulse_width_range(
                config.SERVO_PULSE_MIN_US,
                config.SERVO_PULSE_MAX_US,
            )
            kit.servo[ch].actuation_range = int(config.SERVO_RANGE_DEG)

    # Mevcut SERVO_CENTER degerlerinden basla
    found = {}
    for leg in range(config.NUM_LEGS):
        found[leg] = {}
        for joint in range(config.NUM_JOINTS):
            found[leg][joint] = config.SERVO_CENTER[leg][joint]

    # Her bacak/eklem icin tek tek
    leg_order = [config.LEG_RF, config.LEG_RH, config.LEG_LH, config.LEG_LF]
    joint_order = [config.JOINT_HIP, config.JOINT_KNEE]

    quit_requested = False

    for leg in leg_order:
        if quit_requested:
            break
        for joint in joint_order:
            if quit_requested:
                break

            leg_name = config.LEG_NAMES[leg]
            joint_name = "HIP" if joint == config.JOINT_HIP else "KNEE"
            channel = config.SERVO_CHANNELS[leg][joint]
            angle = found[leg][joint]

            print()
            print("=" * 70)
            print(f"  Sira: {leg_name}-{joint_name}  (kanal {channel})")
            print(f"  Baslangic aci: {angle:.1f} derece")
            print("=" * 70)

            # Servoyu mevcut acya getir
            kit.servo[channel].angle = clamp(angle, 0.0, 180.0)
            print(f"  Servo {angle:.1f} dereceye gitti.")
            print()
            if joint == config.JOINT_HIP:
                print("  HEDEF: femur (ust bacak) govdeden dik asagi baksin")
            else:
                print("  HEDEF: tibia (alt bacak) femure 90 derecede,")
                print("         ayak ucu dogrudan altta olsun")
            print()

            while True:
                try:
                    cmd = input(f"  [{leg_name}-{joint_name} @ {angle:.1f}] > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    quit_requested = True
                    break

                if cmd in ("q", "quit"):
                    quit_requested = True
                    break

                if cmd in ("ok", "", "n", "next"):
                    found[leg][joint] = angle
                    print(f"  ✓ {leg_name}-{joint_name} = {angle:.1f} kaydedildi")
                    break

                if cmd in ("skip", "s"):
                    print(f"  → {leg_name}-{joint_name} atlandi, eski deger: {found[leg][joint]:.1f}")
                    break

                # Delta komutlari
                if cmd == "+" or cmd == "=":
                    angle = clamp(angle + 1.0, 0.0, 180.0)
                elif cmd == "-":
                    angle = clamp(angle - 1.0, 0.0, 180.0)
                elif cmd == "++":
                    angle = clamp(angle + 5.0, 0.0, 180.0)
                elif cmd == "--":
                    angle = clamp(angle - 5.0, 0.0, 180.0)
                else:
                    # Sayisal mutlak deger?
                    try:
                        new_angle = float(cmd)
                        angle = clamp(new_angle, 0.0, 180.0)
                    except ValueError:
                        print("  Komut anlasilmadi. + - ++ -- ok skip q veya sayi")
                        continue

                kit.servo[channel].angle = angle
                print(f"  → {angle:.1f} derece")

    # Cikti: config.py'ye yapistirilacak format
    print()
    print("=" * 70)
    print(" SONUCLAR")
    print("=" * 70)
    print()
    print("Bunu config.py'deki SERVO_CENTER blokunun yerine yapistir:")
    print()
    print("SERVO_CENTER = {")
    for leg in leg_order:
        leg_name = config.LEG_NAMES[leg]
        hip = found[leg][config.JOINT_HIP]
        knee = found[leg][config.JOINT_KNEE]
        print(f"    LEG_{leg_name}: {{JOINT_HIP: {hip:.1f}, JOINT_KNEE: {knee:.1f}}},  # {leg_name}")
    print("}")
    print()

    # Servolari serbest birak
    print("Servolar serbest birakiliyor...")
    for leg in range(config.NUM_LEGS):
        for joint in range(config.NUM_JOINTS):
            ch = config.SERVO_CHANNELS[leg][joint]
            try:
                kit.servo[ch].angle = None
            except Exception:
                pass

    print("Bitti.")
    return 0


def clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


if __name__ == "__main__":
    sys.exit(main())
