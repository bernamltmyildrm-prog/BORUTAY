"""
test_quadruped.py
=================
quadruped.py icin hizli test dosyasi.

Calistirma:
    python test_quadruped.py
"""

import config
from quadruped import QuadRuped


dog = QuadRuped()

print("=" * 70)
print("QUADRUPED ANA SINIF TESTI")
print("=" * 70)

dog.stand()
targets = dog.update(config.CONTROL_LOOP_DT)
dog.print_targets(targets)

print("\n" + "=" * 70)
print("WALK MODE TESTI")
print("=" * 70)

dog.walk(speed_scale=1.0)

for i in range(20):
    targets = dog.update(config.CONTROL_LOOP_DT)

    # Her 5 adimda bir yazdiralim, ekran cok dolmasin.
    if i % 5 == 0:
        print(f"\nKontrol adimi: {i}")
        dog.print_targets(targets)

print("\n>>> Test bitti. Tum bacaklar icin reachable=YES ise bu katman dogru calisiyor.")
