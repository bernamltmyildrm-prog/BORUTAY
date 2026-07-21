"""
test_hardware.py
================
hardware.py icin hizli SIM test.

Calistirma:
    python test_hardware.py

Bu test Windows'ta da calisir.
Gercek servolari hareket ettirmez.
Sadece servo kanal/acilarini ekrana basar.
"""

from quadruped import QuadRuped
from hardware import HardwareController


dog = QuadRuped()
hw = HardwareController(real=False, verbose=True)

print("=" * 80)
print("HARDWARE SIM TEST")
print("=" * 80)

print("\n>>> STAND")
dog.stand()
targets = dog.update(dt=0.02)
hw.apply_targets(targets)

print("\n>>> IDLE / CROUCH")
dog.idle()
targets = dog.update(dt=0.02)
hw.apply_targets(targets)

print("\n>>> WALK - 5 adim")
dog.walk(speed_scale=1.0)

for i in range(5):
    print(f"\n--- walk step {i + 1} ---")
    targets = dog.update(dt=0.02)
    hw.apply_targets(targets)

print("\n>>> Test bitti.")
