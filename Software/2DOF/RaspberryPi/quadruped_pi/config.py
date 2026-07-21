"""
config.py - BUYUK KOPEK (1.8x olcek)
=====================================
Borutay quadruped robot - merkezi konfigurasyon.
Tum sabitler burada, diger dosyalar bunu import eder.

BASKI %180 (1.8x) BUYUTULDU: tum mm degerleri eski config x 1.8.
Acilar ve IK matematigi AYNI (geometrik benzerlik - ucgen buyuyunce
acilari degismez). Sadece uzunluk/yukseklik/adim degerleri olceklendi.
"""

# =============================================================================
# BACAK GEOMETRISI (mm) - 1.8x olcek
# =============================================================================
# Eski STL olculeri x 1.8
FEMUR_LENGTH = 190.46       # ust bacak (eski 105.81 x 1.8)
TIBIA_LENGTH = 159.53       # alt bacak (eski  88.63 x 1.8)

# Govde geometrisi (mm) - 1.8x
BODY_LENGTH = 396.0         # on hip ile arka hip arasi (eski 220 x 1.8)
BODY_WIDTH = 198.0          # sol hip ile sag hip arasi (eski 110 x 1.8)
BODY_STAND_HEIGHT = 288.0   # ayak ucundan govde tabanina (eski 160 x 1.8)
BODY_IDLE_HEIGHT = 234.0    # cromelmis poz (eski 130 x 1.8)

# =============================================================================
# BACAK INDEKSLEME
# =============================================================================
LEG_RF = 0  # Right Front  (Sag On)
LEG_RH = 1  # Right Hind   (Sag Arka)
LEG_LH = 2  # Left Hind    (Sol Arka)
LEG_LF = 3  # Left Front   (Sol On)
NUM_LEGS = 4
LEG_NAMES = ["RF", "RH", "LH", "LF"]


def is_front_leg(leg):
    """Bacak on bacak mi?"""
    return leg == LEG_RF or leg == LEG_LF


def is_right_leg(leg):
    """Bacak sag bacak mi?"""
    return leg == LEG_RF or leg == LEG_RH


# =============================================================================
# EKLEM INDEKSLEME
# =============================================================================
JOINT_HIP = 0   # ust eklem (kalca)
JOINT_KNEE = 1  # alt eklem (diz)
NUM_JOINTS = 2  # her bacakta 2 servo (2-DOF)

# Eklem aci limitleri (derece) - IK hesabi icin
HIP_MIN_DEG = -65.0
HIP_MAX_DEG = +65.0
KNEE_MIN_DEG = -120.0
KNEE_MAX_DEG = +10.0

# =============================================================================
# SERVO CHANNEL MAPPING (PCA9685)
# =============================================================================
# Her bacagin (hip_channel, knee_channel) PCA9685 kanal numarasi.
SERVO_CHANNELS = {
    LEG_RF: (0, 1),   # Sag On  : hip=0, knee=1
    LEG_RH: (2, 3),   # Sag Arka: hip=2, knee=3
    LEG_LH: (4, 5),   # Sol Arka: hip=4, knee=5
    LEG_LF: (6, 7),   # Sol On  : hip=6, knee=7
}

# =============================================================================
# SERVO KALIBRASYON (her servo icin ayri ayarlanir)
# =============================================================================
# Mekanik nötr konumda servo'nun gerçek açi degeri (derece).
# 180-derece servo icin orta = 90. Horn'u 90'da takmadiysan burada ayarla.
#
# YENI BUYUK KOPEK MONTAJI: horn'lar yeni takiliyor. Once servo_kalibre.py
# ile 'all 90' yapip horn'lari stand pozisyonunda tak, sonra find_neutrals.py
# ile ince ayar yapip cikan degerleri buraya yapistir.
#
# Baslangic olarak hepsi 90 (yeni montaj icin notr). Kalibrasyon sonrasi
# guncellenecek.
SERVO_CENTER = {
    LEG_RF: {JOINT_HIP: 90.0, JOINT_KNEE: 90.0},
    LEG_RH: {JOINT_HIP: 90.0, JOINT_KNEE: 90.0},
    LEG_LH: {JOINT_HIP: 90.0, JOINT_KNEE: 90.0},
    LEG_LF: {JOINT_HIP: 90.0, JOINT_KNEE: 90.0},
}

# Servo donus yonu: +1 normal, -1 ters.
# Sol bacaklar genelde sag bacaklarin aynasi oldugu icin ters donmesi gerekir.
SERVO_DIRECTION = {
    LEG_RF: {JOINT_HIP: +1, JOINT_KNEE: +1},
    LEG_RH: {JOINT_HIP: +1, JOINT_KNEE: +1},
    LEG_LH: {JOINT_HIP: -1, JOINT_KNEE: -1},
    LEG_LF: {JOINT_HIP: -1, JOINT_KNEE: -1},
}

# Horn'u takarken olusan kucuk mekanik kayma icin offset (derece).
# Kalibrasyon sirasinda her bacak icin elle ayarlanir.
SERVO_OFFSET = {
    LEG_RF: {JOINT_HIP: 0.0, JOINT_KNEE: 0.0},
    LEG_RH: {JOINT_HIP: 0.0, JOINT_KNEE: 0.0},
    LEG_LH: {JOINT_HIP: 0.0, JOINT_KNEE: 0.0},
    LEG_LF: {JOINT_HIP: 0.0, JOINT_KNEE: 0.0},
}

# =============================================================================
# PCA9685 + SERVO PARAMETRELERI
# =============================================================================
# DS3235 standart hobby PWM: 500-2500 us pulse, 50 Hz frame.
PCA9685_I2C_ADDRESS = 0x40       # varsayilan adres
PCA9685_FREQ_HZ = 50              # servo refresh rate

SERVO_PULSE_MIN_US = 500          # bir uca karsilik gelir
SERVO_PULSE_MAX_US = 2500         # diger uca karsilik gelir
SERVO_RANGE_DEG = 180.0           # DS3235 180-derece versiyon

# Servo komut acisi guvenlik sinirlari (PCA9685'e gonderilen)
SERVO_MIN_ANGLE_DEG = 0.0
SERVO_MAX_ANGLE_DEG = 180.0

# =============================================================================
# KONTROL DONGUSU
# =============================================================================
CONTROL_LOOP_HZ = 50
CONTROL_LOOP_DT = 1.0 / CONTROL_LOOP_HZ  # = 0.02 s

# =============================================================================
# GAIT (YURUYUS) PARAMETRELERI - 1.8x olcek
# =============================================================================
GAIT_STEP_LENGTH_X = 108.0   # mm, bir adimda ayak ne kadar ileri-geri (eski 60 x 1.8)
GAIT_STEP_HEIGHT_Z = 72.0    # mm, swing sirasinda ayak ne kadar yukseliyor (eski 40 x 1.8)
GAIT_PERIOD_S = 0.9          # saniye, tam cycle suresi (eski 0.75 -> buyuk kutle
                             # icin biraz yavaslatildi; testte 0.8-1.1 dene)

# =============================================================================
# PID PARAMETRELERI (IMU gelince kullanilacak)
# =============================================================================
BALANCE_PITCH_KP = 0.8
BALANCE_PITCH_KI = 0.0
BALANCE_PITCH_KD = 0.05

BALANCE_ROLL_KP = 0.8
BALANCE_ROLL_KI = 0.0
BALANCE_ROLL_KD = 0.05

BALANCE_CORRECTION_LIMIT_MM = 18.0    # eski 10 x 1.8
BALANCE_DEADBAND_DEG = 0.5
COMPLEMENTARY_ALPHA = 0.98

# IMU I2C ayarlari
IMU_I2C_BUS = 1
MPU6050_ADDR = 0x68
