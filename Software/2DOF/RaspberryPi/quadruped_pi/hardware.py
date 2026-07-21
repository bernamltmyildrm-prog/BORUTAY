"""
hardware.py
===========
PCA9685 + DS3235 servo kontrol katmani.

config.py ile uyumlu guncel surum.
"""

from __future__ import annotations

import time
from typing import Dict, Optional

import config


# =============================================================================
# PCA9685 / SERVO AYARLARI - config.py ile uyumlu
# =============================================================================
PCA9685_ADDRESS = config.PCA9685_I2C_ADDRESS
PCA9685_CHANNELS = 16

SERVO_FREQ_HZ = config.PCA9685_FREQ_HZ

SERVO_MIN_PULSE_US = config.SERVO_PULSE_MIN_US
SERVO_MAX_PULSE_US = config.SERVO_PULSE_MAX_US
SERVO_ACTUATION_RANGE_DEG = int(config.SERVO_RANGE_DEG)

SERVO_MIN_ANGLE_DEG = config.SERVO_MIN_ANGLE_DEG
SERVO_MAX_ANGLE_DEG = config.SERVO_MAX_ANGLE_DEG

DEFAULT_SERVO_CENTER_DEG = 90.0
COMMAND_DELAY_S = getattr(config, "HARDWARE_COMMAND_DELAY_S", 0.0)


# =============================================================================
# Yardimci fonksiyonlar
# =============================================================================
def _nested_get(mapping_name: str, leg: int, joint: int, default):
    mapping = getattr(config, mapping_name, None)

    if mapping is None:
        return default

    try:
        return mapping[leg][joint]
    except Exception:
        return default


class HardwareController:
    """
    real=False:
        Simulasyon modu. Servo surmez, sadece komutlari ekrana yazar.

    real=True:
        Raspberry Pi + PCA9685 uzerinden gercek servo surer.
    """

    def __init__(self, real: bool = False, verbose: bool = True):
        self.real = bool(real)
        self.verbose = bool(verbose)

        self.kit = None
        self.last_servo_angles: Dict[int, float] = {}

        if self.real:
            self._init_real_hardware()
        else:
            if self.verbose:
                print(">>> HardwareController SIM mode.")
                print(">>> Gercek servo surulmuyor, sadece komutlar yazdirilir.")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    def _init_real_hardware(self) -> None:
        try:
            from adafruit_servokit import ServoKit

            self.kit = ServoKit(
                channels=PCA9685_CHANNELS,
                address=PCA9685_ADDRESS,
            )

            for channel in self._used_channels():
                servo = self.kit.servo[channel]
                servo.set_pulse_width_range(
                    SERVO_MIN_PULSE_US,
                    SERVO_MAX_PULSE_US,
                )
                servo.actuation_range = SERVO_ACTUATION_RANGE_DEG

            if self.verbose:
                print(">>> PCA9685 baglantisi basarili.")
                print(f">>> Address: 0x{PCA9685_ADDRESS:02X}")
                print(f">>> Servo freq: {SERVO_FREQ_HZ} Hz")
                print(f">>> Pulse range: {SERVO_MIN_PULSE_US}-{SERVO_MAX_PULSE_US} us")
                print(f">>> Actuation range: {SERVO_ACTUATION_RANGE_DEG} deg")
                print(f">>> Used channels: {self._used_channels()}")

        except Exception as exc:
            self.kit = None
            self.real = False
            print(f">>> PCA9685/ServoKit baslatilamadi: {exc}")
            print(">>> SIM mode'a gecildi. Servo surulmuyor.")

    def _used_channels(self):
        channels = []

        for leg in range(config.NUM_LEGS):
            for joint in range(config.NUM_JOINTS):
                channel = config.SERVO_CHANNELS[leg][joint]
                channels.append(channel)

        return sorted(set(channels))

    # -------------------------------------------------------------------------
    # Angle conversion
    # -------------------------------------------------------------------------
    def ik_to_servo_angle(self, leg: int, joint: int, ik_angle_deg: float) -> float:
        """
        IK acisini servo acisina cevirir.

        Formul:
            servo_angle = center + direction * ik_angle + offset
        """
        center = _nested_get("SERVO_CENTER", leg, joint, DEFAULT_SERVO_CENTER_DEG)
        direction = _nested_get("SERVO_DIRECTION", leg, joint, +1)
        offset = _nested_get("SERVO_OFFSET", leg, joint, 0.0)

        servo_angle = center + direction * ik_angle_deg + offset
        servo_angle = self._clamp(
            servo_angle,
            SERVO_MIN_ANGLE_DEG,
            SERVO_MAX_ANGLE_DEG,
        )

        return servo_angle

    # -------------------------------------------------------------------------
    # Public servo commands
    # -------------------------------------------------------------------------
    def set_joint_angle(self, leg: int, joint: int, ik_angle_deg: float) -> float:
        channel = config.SERVO_CHANNELS[leg][joint]
        servo_angle = self.ik_to_servo_angle(leg, joint, ik_angle_deg)

        self.last_servo_angles[channel] = servo_angle

        if self.real and self.kit is not None:
            self.kit.servo[channel].angle = servo_angle
            if self.verbose:
                print(
                    f"[REAL] {config.LEG_NAMES[leg]} "
                    f"{self._joint_name(joint):>4} | "
                    f"IK={ik_angle_deg:+8.2f} deg -> "
                    f"servo={servo_angle:7.2f} deg | "
                    f"channel={channel}"
                )
        else:
            if self.verbose:
                print(
                    f"[SIM] {config.LEG_NAMES[leg]} "
                    f"{self._joint_name(joint):>4} | "
                    f"IK={ik_angle_deg:+8.2f} deg -> "
                    f"servo={servo_angle:7.2f} deg | "
                    f"channel={channel}"
                )

        if COMMAND_DELAY_S > 0.0:
            time.sleep(COMMAND_DELAY_S)

        return servo_angle

    def set_servo_angle_direct(self, channel: int, angle_deg: float) -> float:
        """
        IK donusumu yapmadan dogrudan servo acisi yollar.
        Neutral/horn kalibrasyonu icin kullanilir.
        """
        angle = self._clamp(angle_deg, SERVO_MIN_ANGLE_DEG, SERVO_MAX_ANGLE_DEG)
        self.last_servo_angles[channel] = angle

        if self.real and self.kit is not None:
            self.kit.servo[channel].angle = angle
            if self.verbose:
                print(f"[REAL] direct servo={angle:7.2f} deg | channel={channel}")
        else:
            if self.verbose:
                print(f"[SIM] direct servo={angle:7.2f} deg | channel={channel}")

        return angle

    def set_leg_angles(
        self,
        leg: int,
        hip_deg: Optional[float],
        knee_deg: Optional[float],
    ) -> None:
        if hip_deg is None or knee_deg is None:
            if self.verbose:
                print(f">>> {config.LEG_NAMES[leg]} hedef acisi None, komut atlandi.")
            return

        self.set_joint_angle(leg, config.JOINT_HIP, hip_deg)
        self.set_joint_angle(leg, config.JOINT_KNEE, knee_deg)

    def apply_targets(self, targets) -> None:
        for leg, target in targets.items():
            if not getattr(target, "reachable", False):
                if self.verbose:
                    print(f">>> {config.LEG_NAMES[leg]} reachable=False, komut atlandi.")
                continue

            self.set_leg_angles(
                leg=leg,
                hip_deg=target.hip_deg,
                knee_deg=target.knee_deg,
            )

    def stand_all_neutral(self) -> None:
        for leg in range(config.NUM_LEGS):
            for joint in range(config.NUM_JOINTS):
                channel = config.SERVO_CHANNELS[leg][joint]
                center = _nested_get("SERVO_CENTER", leg, joint, DEFAULT_SERVO_CENTER_DEG)
                self.set_servo_angle_direct(channel, center)

    def release_all(self) -> None:
        for channel in self._used_channels():
            if self.real and self.kit is not None:
                self.kit.servo[channel].angle = None

            if self.verbose:
                print(f">>> channel {channel} PWM released")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        if value < lower:
            return lower
        if value > upper:
            return upper
        return value

    @staticmethod
    def _joint_name(joint: int) -> str:
        if joint == config.JOINT_HIP:
            return "HIP"
        if joint == config.JOINT_KNEE:
            return "KNEE"
        return f"J{joint}"


if __name__ == "__main__":
    from quadruped import QuadRuped

    dog = QuadRuped()
    hw = HardwareController(real=False, verbose=True)

    print("\n>>> STAND hedefleri SIM olarak uygulanıyor")
    dog.stand()
    targets = dog.update(dt=0.02)
    hw.apply_targets(targets)

    print("\n>>> WALK hedefleri SIM olarak uygulanıyor")
    dog.walk(speed_scale=1.0)

    for i in range(3):
        print(f"\n--- walk step {i + 1} ---")
        targets = dog.update(dt=0.02)
        hw.apply_targets(targets)