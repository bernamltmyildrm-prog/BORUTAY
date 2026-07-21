"""
config.py
=========
Borutay quadruped robot - merkezi konfigurasyon.
Tum sabitler burada, diger dosyalar bunu import eder.
"""

# =============================================================================
# BACAK GEOMETRISI (mm)
# =============================================================================
# STL dosyalarindan olculen gercek uzunluklar
FEMUR_LENGTH = 105.81       # ust bacak (hip pivotundan diz pivotuna)
TIBIA_LENGTH = 88.63        # alt bacak (diz pivotundan ayak ucuna)

# Govde geometrisi (mm)
BODY_LENGTH = 220.0         # on hip ile arka hip arasi
BODY_WIDTH = 110.0          # sol hip ile sag hip arasi
BODY_STAND_HEIGHT = 160.0   # ayak ucundan govde tabanina (stand pose)
BODY_IDLE_HEIGHT = 130.0     # cromelmis poz (rest)

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
SERVO_CENTER = {
    LEG_RF: {JOINT_HIP: 144.5, JOINT_KNEE: 159.4},  # RF -> stand servo: 95 / 90
    LEG_RH: {JOINT_HIP: 144.5, JOINT_KNEE: 159.40},  # RH -> stand servo: 90 / 80
    LEG_LH: {JOINT_HIP: 35.50,  JOINT_KNEE: 5.60},   # LH -> hip 90, knee eski 100
    LEG_LF: {JOINT_HIP: 35.50,  JOINT_KNEE: 10.60},   # LF -> eski 90 / 90
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
# GAIT (YURUYUS) PARAMETRELERI
# =============================================================================
GAIT_STEP_LENGTH_X = 60.0    # mm, bir adimda ayak ne kadar ileri-geri savrulur
GAIT_STEP_HEIGHT_Z = 40.0    # mm, swing sirasinda ayak ne kadar yukseliyor
GAIT_PERIOD_S = 0.75         # saniye, tam cycle suresi

# =============================================================================
# PID PARAMETRELERI (IMU gelince kullanilacak)
# =============================================================================
BALANCE_PITCH_KP = 0.8
BALANCE_PITCH_KI = 0.0
BALANCE_PITCH_KD = 0.05

BALANCE_ROLL_KP = 0.8
BALANCE_ROLL_KI = 0.0
BALANCE_ROLL_KD = 0.05

BALANCE_CORRECTION_LIMIT_MM = 10.0
BALANCE_DEADBAND_DEG = 0.5
COMPLEMENTARY_ALPHA = 0.98

# IMU I2C ayarlari
IMU_I2C_BUS = 1
MPU6050_ADDR = 0x68