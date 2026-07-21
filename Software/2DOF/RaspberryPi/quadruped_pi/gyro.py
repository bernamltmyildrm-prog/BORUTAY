"""
gyro.py
=======
MPU-6050 IMU icin gyro + accelerometer okuma katmani.

Bu dosya:
    - MPU-6050 accelerometer ve gyroscope verisini okur
    - Complementary filter ile roll/pitch hesaplar
    - PID ile pitch/roll correction uretir

Not:
    Bu dosya servo surmez.
    Sadece IMU acilarini ve denge duzeltmesini hesaplar.
    MPU-6050'de magnetometer YOK -> yaw sadece gyro integration ile
    hesaplanir (drift olur, ama denge icin pitch+roll yeterli).

Windows'ta veya IMU bagli degilken:
    - smbus2 bulunamazsa otomatik FakeGyro moduna gecer.

Raspberry Pi uzerinde:
    sudo raspi-config
        Interface Options -> I2C -> Enable

    sudo apt install -y i2c-tools
    pip install smbus2

    i2cdetect -y 1

Beklenen:
    0x68 veya 0x69 -> MPU-6050
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional

import config
from pid import PIDController


def _cfg(name: str, default):
    """config.py icinde deger varsa onu kullanir, yoksa default doner."""
    return getattr(config, name, default)


# =============================================================================
# I2C ADDRESS
# =============================================================================
I2C_BUS_ID = _cfg("IMU_I2C_BUS", 1)

# AD0 pini GND ise 0x68, VCC ise 0x69 olur.
# HW-579 modulunde varsayilan AD0 -> GND, yani 0x68.
MPU6050_ADDR = _cfg("MPU6050_ADDR", 0x68)


# =============================================================================
# MPU-6050 REGISTERS
# =============================================================================
REG_SMPLRT_DIV = 0x19
REG_CONFIG = 0x1A
REG_GYRO_CONFIG = 0x1B
REG_ACCEL_CONFIG = 0x1C
REG_ACCEL_XOUT_H = 0x3B
REG_GYRO_XOUT_H = 0x43
REG_PWR_MGMT_1 = 0x6B
REG_WHO_AM_I = 0x75

# Scale settings (varsayilan ayarlar):
# Accel +/-2g  -> 16384 LSB/g
# Gyro  +/-250 dps -> 131 LSB/(deg/s)
ACCEL_SCALE = 16384.0
GYRO_SCALE = 131.0


# =============================================================================
# FILTER + PID SETTINGS
# =============================================================================
COMPLEMENTARY_ALPHA = _cfg("COMPLEMENTARY_ALPHA", 0.98)

BALANCE_PITCH_KP = _cfg("BALANCE_PITCH_KP", 0.8)
BALANCE_PITCH_KI = _cfg("BALANCE_PITCH_KI", 0.0)
BALANCE_PITCH_KD = _cfg("BALANCE_PITCH_KD", 0.05)

BALANCE_ROLL_KP = _cfg("BALANCE_ROLL_KP", 0.8)
BALANCE_ROLL_KI = _cfg("BALANCE_ROLL_KI", 0.0)
BALANCE_ROLL_KD = _cfg("BALANCE_ROLL_KD", 0.05)

BALANCE_CORRECTION_LIMIT_MM = _cfg("BALANCE_CORRECTION_LIMIT_MM", 10.0)
BALANCE_DEADBAND_DEG = _cfg("BALANCE_DEADBAND_DEG", 0.5)


@dataclass
class IMUState:
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0  # MPU-6050'de magnetometer yok, sadece gyro int.

    accel_x_g: float = 0.0
    accel_y_g: float = 0.0
    accel_z_g: float = 1.0

    gyro_x_dps: float = 0.0
    gyro_y_dps: float = 0.0
    gyro_z_dps: float = 0.0

    pitch_correction_mm: float = 0.0
    roll_correction_mm: float = 0.0

    imu_ok: bool = False
    fake_mode: bool = False


class FakeGyro:
    """Donanim yokken test etmek icin sahte IMU."""

    def __init__(self):
        self.start_time = time.monotonic()
        self.state = IMUState(imu_ok=True, fake_mode=True)

    def update(self, dt: float) -> IMUState:
        t = time.monotonic() - self.start_time
        self.state.pitch_deg = 5.0 * math.sin(2.0 * math.pi * 0.20 * t)
        self.state.roll_deg = 3.0 * math.sin(2.0 * math.pi * 0.15 * t)
        self.state.yaw_deg = 0.0
        return self.state

    def close(self) -> None:
        pass


class GyroProc:
    """
    MPU-6050 IMU isleme sinifi.

    Hedef:
        - Roll/pitch degerlerini stabil okumak (denge icin)
        - PID correction uretmek
        - Yaw sadece gyro entegrasyonu (kullanmasak da olur)
    """

    def __init__(self, use_fake_if_missing: bool = True):
        self.use_fake_if_missing = use_fake_if_missing
        self.fake: Optional[FakeGyro] = None
        self.bus = None

        self.imu_available = False

        self.state = IMUState()
        self.last_time = time.monotonic()

        self.pitch_pid = PIDController(
            kp=BALANCE_PITCH_KP,
            ki=BALANCE_PITCH_KI,
            kd=BALANCE_PITCH_KD,
            target=0.0,
            output_limits=(-BALANCE_CORRECTION_LIMIT_MM, BALANCE_CORRECTION_LIMIT_MM),
            integral_limits=(-BALANCE_CORRECTION_LIMIT_MM, BALANCE_CORRECTION_LIMIT_MM),
            deadband=BALANCE_DEADBAND_DEG,
        )

        self.roll_pid = PIDController(
            kp=BALANCE_ROLL_KP,
            ki=BALANCE_ROLL_KI,
            kd=BALANCE_ROLL_KD,
            target=0.0,
            output_limits=(-BALANCE_CORRECTION_LIMIT_MM, BALANCE_CORRECTION_LIMIT_MM),
            integral_limits=(-BALANCE_CORRECTION_LIMIT_MM, BALANCE_CORRECTION_LIMIT_MM),
            deadband=BALANCE_DEADBAND_DEG,
        )

        self._init_bus_and_sensor()

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    def _init_bus_and_sensor(self) -> None:
        try:
            from smbus2 import SMBus

            self.bus = SMBus(I2C_BUS_ID)

            self._init_mpu6050()
            self.imu_available = True
            self.state.imu_ok = True

            print(">>> MPU-6050 baslatildi.")
            print(f">>> MPU address: 0x{MPU6050_ADDR:02X}")

        except Exception as exc:
            self.imu_available = False
            self.state.imu_ok = False

            print(f">>> MPU-6050 baslatilamadi: {exc}")

            if self.use_fake_if_missing:
                print(">>> FakeGyro moduna geciliyor. Donanim yokken test devam eder.")
                self.fake = FakeGyro()
            else:
                print(">>> FakeGyro kapali. IMU degerleri sifir kalacak.")

    def _init_mpu6050(self) -> None:
        # Reset cihaz
        self.bus.write_byte_data(MPU6050_ADDR, REG_PWR_MGMT_1, 0x80)
        time.sleep(0.1)

        # Wake up (sleep bit clear)
        self.bus.write_byte_data(MPU6050_ADDR, REG_PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # PLL with X gyro reference (daha stabil clock)
        self.bus.write_byte_data(MPU6050_ADDR, REG_PWR_MGMT_1, 0x01)
        time.sleep(0.05)

        # Sample rate divider: 1kHz / (1+7) = 125 Hz
        self.bus.write_byte_data(MPU6050_ADDR, REG_SMPLRT_DIV, 0x07)

        # Digital low pass filter: ~44 Hz bandwidth (gurultuyu azalt)
        self.bus.write_byte_data(MPU6050_ADDR, REG_CONFIG, 0x03)

        # Gyro full scale: +/-250 dps (en hassas)
        self.bus.write_byte_data(MPU6050_ADDR, REG_GYRO_CONFIG, 0x00)

        # Accel full scale: +/-2g (en hassas)
        self.bus.write_byte_data(MPU6050_ADDR, REG_ACCEL_CONFIG, 0x00)

        # WHO_AM_I check: MPU-6050 standart degeri 0x68
        # (bazi klon chip'lerde 0x70, 0x71, 0x72 da olabilir)
        who = self.bus.read_byte_data(MPU6050_ADDR, REG_WHO_AM_I)
        print(f">>> MPU WHO_AM_I = 0x{who:02X}")

        if who not in (0x68, 0x70, 0x71, 0x72, 0x98):
            print(f">>> UYARI: Beklenmedik WHO_AM_I degeri. Yine de devam ediliyor.")

    # -------------------------------------------------------------------------
    # Public update
    # -------------------------------------------------------------------------
    def update(self, dt: Optional[float] = None) -> IMUState:
        dt = self._resolve_dt(dt)

        if self.fake is not None:
            self.state = self.fake.update(dt)
            self._compute_pid_corrections(dt)
            return self.state

        if not self.imu_available:
            self.state = IMUState(imu_ok=False, fake_mode=False)
            return self.state

        try:
            ax, ay, az = self._read_accel_g()
            gx, gy, gz = self._read_gyro_dps()

            self.state.accel_x_g = ax
            self.state.accel_y_g = ay
            self.state.accel_z_g = az

            self.state.gyro_x_dps = gx
            self.state.gyro_y_dps = gy
            self.state.gyro_z_dps = gz

            # Accelerometer'dan aci tahmini (statik, gurultulu ama drift yok)
            accel_roll = math.degrees(math.atan2(ay, az))
            accel_pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

            # Gyro entegrasyonu (dinamik, hassas ama drift var)
            gyro_roll = self.state.roll_deg + gx * dt
            gyro_pitch = self.state.pitch_deg + gy * dt

            # Complementary filter: %98 gyro + %2 accel
            alpha = COMPLEMENTARY_ALPHA
            self.state.roll_deg = alpha * gyro_roll + (1.0 - alpha) * accel_roll
            self.state.pitch_deg = alpha * gyro_pitch + (1.0 - alpha) * accel_pitch

            # Yaw: sadece gyro integration (magnetometer yok, drift var)
            self.state.yaw_deg = self.state.yaw_deg + gz * dt

            self.state.imu_ok = True
            self.state.fake_mode = False

            self._compute_pid_corrections(dt)

        except Exception as exc:
            print(f">>> IMU okuma hatasi: {exc}")
            self.state.imu_ok = False
            self.state.pitch_correction_mm = 0.0
            self.state.roll_correction_mm = 0.0

        return self.state

    # -------------------------------------------------------------------------
    # PID correction
    # -------------------------------------------------------------------------
    def _compute_pid_corrections(self, dt: float) -> None:
        self.state.pitch_correction_mm = self.pitch_pid.update(
            input_value=self.state.pitch_deg,
            dt=dt,
        )

        self.state.roll_correction_mm = self.roll_pid.update(
            input_value=self.state.roll_deg,
            dt=dt,
        )

    # -------------------------------------------------------------------------
    # Sensor reads
    # -------------------------------------------------------------------------
    def _read_accel_g(self):
        data = self.bus.read_i2c_block_data(MPU6050_ADDR, REG_ACCEL_XOUT_H, 6)
        ax = self._combine_signed_be(data[0], data[1]) / ACCEL_SCALE
        ay = self._combine_signed_be(data[2], data[3]) / ACCEL_SCALE
        az = self._combine_signed_be(data[4], data[5]) / ACCEL_SCALE
        return ax, ay, az

    def _read_gyro_dps(self):
        data = self.bus.read_i2c_block_data(MPU6050_ADDR, REG_GYRO_XOUT_H, 6)
        gx = self._combine_signed_be(data[0], data[1]) / GYRO_SCALE
        gy = self._combine_signed_be(data[2], data[3]) / GYRO_SCALE
        gz = self._combine_signed_be(data[4], data[5]) / GYRO_SCALE
        return gx, gy, gz

    @staticmethod
    def _combine_signed_be(high: int, low: int) -> int:
        """Two's complement big-endian 16-bit signed value."""
        value = (high << 8) | low
        if value >= 32768:
            value -= 65536
        return value

    # -------------------------------------------------------------------------
    # Time / close
    # -------------------------------------------------------------------------
    def _resolve_dt(self, dt: Optional[float]) -> float:
        if dt is not None:
            dt = float(dt)
            if dt <= 0.0:
                return 1e-6
            return dt

        now = time.monotonic()
        resolved_dt = now - self.last_time
        self.last_time = now

        if resolved_dt <= 0.0:
            return 1e-6

        return resolved_dt

    def close(self) -> None:
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass

        if self.fake is not None:
            self.fake.close()


if __name__ == "__main__":
    gyro = GyroProc(use_fake_if_missing=True)

    print("=" * 85)
    print("MPU-6050 GYRO SELF TEST")
    print("=" * 85)
    print(
        f"{'step':>4} | {'roll':>8} | {'pitch':>8} | "
        f"{'yaw':>8} | {'pitch corr':>11} | {'roll corr':>10} | mode"
    )
    print("-" * 85)

    try:
        for i in range(100):
            state = gyro.update(dt=0.02)

            if i % 5 == 0:
                mode = "FAKE" if state.fake_mode else "REAL"
                print(
                    f"{i:4d} | "
                    f"{state.roll_deg:8.3f} | "
                    f"{state.pitch_deg:8.3f} | "
                    f"{state.yaw_deg:8.3f} | "
                    f"{state.pitch_correction_mm:11.3f} | "
                    f"{state.roll_correction_mm:10.3f} | "
                    f"{mode:>4}"
                )

            time.sleep(0.02)

    finally:
        gyro.close()

    print("\n>>> Gyro self-test bitti.")