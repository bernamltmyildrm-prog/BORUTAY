"""
test_baglanti.py
================
Hizli test: config.py ve vecrot.py modullerini import edebiliyor muyuz?
"""

import config
from vecrot import Vector, Rotator

print("=" * 50)
print("Kopek konfigurasyonu yuklendi:")
print("=" * 50)
print(f"  Femur uzunlugu (L1): {config.FEMUR_LENGTH} mm")
print(f"  Tibia uzunlugu (L2): {config.TIBIA_LENGTH} mm")
print(f"  Toplam ulasim:       {config.FEMUR_LENGTH + config.TIBIA_LENGTH:.1f} mm")
print(f"  Stand height:        {config.BODY_STAND_HEIGHT} mm")
print(f"  Kontrol frekansi:    {config.CONTROL_LOOP_HZ} Hz")
print()
print("Bacak isimleri:", config.LEG_NAMES)
print()

# Bir ayak ucu pozisyonu tanimla
ayak_ucu = Vector(0, 0, -150)
print(f"Sag on ayak hedef pozisyon: {ayak_ucu}")

# Govde oryantasyonu
govde_egim = Rotator(yaw=0, pitch=5, roll=0)
print(f"Govde oryantasyonu:         {govde_egim}")

print()
print(">>> Tum moduller basariyla baglandi.")