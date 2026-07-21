"""
servo_neutral.py
================
RF bacaginin iki servosunu 90 derece (180/2 = orta) konumuna alir.
Bu konumda servo horn'larini monte et.

Kullanim:
    1. PCA9685 + servolari bagla (henuz horn takma)
    2. python servo_neutral.py
    3. Servolar 90 dereceye gider ve orada kilitlenir
    4. Bu konumdayken horn'lari mekanik bacak nötr olacak sekilde tak
    5. Ctrl+C ile cik

Servolar: DS3235 180-derece versiyon
Pulse range: 500-2500 us
"""

import time
from adafruit_servokit import ServoKit

import config


def main():
    # PCA9685'i 16 kanalli olarak baslat
    kit = ServoKit(channels=16)

    # RF bacaginin servo kanallarini config'den al
    hip_ch, knee_ch = config.SERVO_CHANNELS[config.LEG_RF]

    # Servolari yapilandir (180 derece, 500-2500us pulse)
    for ch in [hip_ch, knee_ch]:
        kit.servo[ch].set_pulse_width_range(
            config.SERVO_PULSE_MIN_US,
            config.SERVO_PULSE_MAX_US
        )
        kit.servo[ch].actuation_range = int(config.SERVO_RANGE_DEG)

    # Nötr aci = orta nokta
    notr = config.SERVO_RANGE_DEG / 2.0  # 180/2 = 90

    print(f"Servo {hip_ch}  (RF hip)  -> {notr} derece (notr)")
    kit.servo[hip_ch].angle = notr

    print(f"Servo {knee_ch} (RF knee) -> {notr} derece (notr)")
    kit.servo[knee_ch].angle = notr

    print()
    print("=" * 60)
    print(" Servolar notr konumda kilitli.")
    print(" Horn'lari mekanik bacak NÖTR pozisyonda olacak")
    print(" sekilde monte et.")
    print()
    print(" Cikmak icin Ctrl+C")
    print("=" * 60)

    # Servolar konumunu tutsun diye sonsuz dongu
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCikiliyor. Servolar gücü kestiginde gevseyecek,")
        print("ama horn vidalandiysa pozisyon korunur.")


if __name__ == "__main__":
    main()
