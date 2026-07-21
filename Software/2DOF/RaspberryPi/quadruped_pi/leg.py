"""
leg.py
======
Tek bir bacagin Inverse Kinematics (IK) cozumu.

Bacak 2-DOF (hip + knee).
Girdi:  Ayak ucu pozisyonu (x, z) - bacagin bukulme duzleminde, gövdeye göre
Cikti:  (theta_hip, theta_knee) - derece olarak

Koordinat sistemi (bacak bagimsiz, yan profilden):
        HIP (0, 0)
        ●━━━━━━━ +X (ileri)
        │
        │
        ▼ -Z (asagi)

Ornek: Ayak gövdenin tam altinda, 150 mm asagida ise:
       foot = (x=0, z=-150)
       Beklenen: hip ~0, knee ~-bukulmus

Kaynak: tezdeki Equation 3.6 ve 3.7 (cosine yasasi).
"""

import math
import config


def inverse_kinematics(x: float, z: float) -> tuple:
    """
    Ayak ucu (x, z) icin (theta_hip_deg, theta_knee_deg) hesaplar.
    
    Parametreler:
        x: ayak ucunun X koordinati (mm, ileri+)
        z: ayak ucunun Z koordinati (mm, yukari+, genelde negatif)
    
    Donen deger:
        (theta_hip, theta_knee) tuple, dereceler.
        Eger hedef erisilemez ise (None, None) doner.
    """
    L1 = config.FEMUR_LENGTH
    L2 = config.TIBIA_LENGTH
    
    # Adim 1: Hip'ten ayaga uzakligi hesapla
    d = math.sqrt(x * x + z * z)
    
    # Adim 2: Erisim sinirlarini kontrol et
    d_max = L1 + L2
    d_min = abs(L1 - L2)
    
    if d > d_max:
        # Hedef cok uzakta - bacak yetisemez
        print(f"  UYARI: Hedef cok uzak (d={d:.1f} mm > L1+L2={d_max:.1f} mm)")
        return (None, None)
    
    if d < d_min:
        # Hedef cok yakinda - bacak buyuk olcude bukulse bile yetisemez
        print(f"  UYARI: Hedef cok yakin (d={d:.1f} mm < |L1-L2|={d_min:.1f} mm)")
        return (None, None)
    
    # Adim 3: Diz acisi (theta_knee)
    # Cosine yasasi: c^2 = a^2 + b^2 - 2ab*cos(C)
    # Burada c=d, a=L1, b=L2, C = (180 - theta_knee)
    cos_knee = (L1 * L1 + L2 * L2 - d * d) / (2.0 * L1 * L2)
    
    # Numeric guvenlik (floating point yuvarlama hatasi icin)
    cos_knee = max(-1.0, min(1.0, cos_knee))
    
    # arccos(cos_knee) bize "ic acidan tamamlayici" verir, donusturuyoruz
    theta_knee_rad = math.acos(cos_knee) - math.pi
    theta_knee_deg = math.degrees(theta_knee_rad)
    
    # Adim 4: Kalca acisi (theta_hip)
    # Iki bilesen: 
    #   alpha = hip-ayak cizgisinin yatayla yaptigi aci
    #   beta  = femur'un hip-ayak cizgisinden sapmasi
    alpha = math.atan2(z, x)  # genelde negatif (z<0)
    
    cos_beta = (L1 * L1 + d * d - L2 * L2) / (2.0 * L1 * d)
    cos_beta = max(-1.0, min(1.0, cos_beta))
    beta = math.acos(cos_beta)
    
    # theta_hip = alpha + beta (sag bacak konvansiyonu)
    theta_hip_rad = alpha + beta
    theta_hip_deg = math.degrees(theta_hip_rad)
    
    return (theta_hip_deg, theta_knee_deg)


def forward_kinematics(theta_hip_deg: float, theta_knee_deg: float) -> tuple:
    """
    Inverse Kinematics'in tersi: Servo acilarini bilince ayak ucu nerede olur?
    
    Bunu IK'yi dogrulamak icin kullaniyoruz. Eger IK dogru calisiyorsa:
        FK(IK(x, z)) = (x, z)
    """
    L1 = config.FEMUR_LENGTH
    L2 = config.TIBIA_LENGTH
    
    theta_hip = math.radians(theta_hip_deg)
    theta_knee = math.radians(theta_knee_deg)
    
    # Diz pozisyonu
    knee_x = L1 * math.cos(theta_hip)
    knee_z = L1 * math.sin(theta_hip)
    
    # Tibia, femur'a gore theta_knee kadar bukulmus
    # Toplam aci yatay eksene gore: theta_hip + theta_knee
    foot_x = knee_x + L2 * math.cos(theta_hip + theta_knee)
    foot_z = knee_z + L2 * math.sin(theta_hip + theta_knee)
    
    return (foot_x, foot_z)


# =============================================================================
# Self-test: dosyayi direkt calistirinca IK ve FK'yi birkac noktada test eder.
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Leg IK/FK Test")
    print(f"  L1 (femur) = {config.FEMUR_LENGTH} mm")
    print(f"  L2 (tibia) = {config.TIBIA_LENGTH} mm")
    print(f"  Max reach  = {config.FEMUR_LENGTH + config.TIBIA_LENGTH:.1f} mm")
    print("=" * 60)
    print()
    
    # Test 1: Ayak govdenin tam altinda, 150 mm asagida (stand pose)
    test_points = [
        ( 0,  -150),   # Tam altinda
        ( 0,  -100),   # Daha yakin (knee daha cok bukulu)
        ( 0,  -180),   # Daha uzakta (knee neredeyse duz)
        (30,  -150),   # Hafif ileride (yuruyusun stance fazi)
        (-30, -150),   # Hafif geride
        ( 0,  -250),   # ERISILEMEZ (max reach 194)
        ( 0,  -10),    # ERISILEMEZ (cok yakin)
    ]
    
    print(f"{'X (mm)':>8} {'Z (mm)':>8} | {'hip (°)':>9} {'knee (°)':>9} | {'FK check'}")
    print("-" * 70)
    for x, z in test_points:
        hip, knee = inverse_kinematics(x, z)
        if hip is None:
            print(f"{x:>8.1f} {z:>8.1f} | erisilemez")
            continue
        
        # Forward kinematics ile dogrulama
        fx, fz = forward_kinematics(hip, knee)
        error = math.sqrt((fx - x)**2 + (fz - z)**2)
        ok = "OK" if error < 0.1 else f"HATA={error:.2f}"
        
        print(f"{x:>8.1f} {z:>8.1f} | {hip:>9.2f} {knee:>9.2f} | FK=({fx:6.1f},{fz:6.1f}) {ok}")
    
    print()
    print(">>> IK/FK testi tamamlandi.")