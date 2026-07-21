"""
quadruped.py
============
4 bacakli 2-DOF robot kopek ana kontrol sinifi.

Bu dosya donanima komut gondermez.
gyro.py -> IMU okur, gait.py -> ayak ucu hedefleri, leg.py -> IK hesaplar.

Desteklenen hareketler:
    - stand / kalk
    - idle / crouch / comel
    - walk forward
    - walk backward

Davranis:
    - Forward/backward komutlari tek gait cycle calisir.
    - Bir cycle tamamlaninca robot otomatik stand moduna doner.
"""

from dataclasses import dataclass
from typing import Dict, Optional

import config
from vecrot import Vector
from gait import GaitTrot
from leg import inverse_kinematics


@dataclass
class JointTarget:
    """Tek bacagin hedef acilari ve ayak pozisyonu."""
    foot: Vector
    hip_deg: Optional[float]
    knee_deg: Optional[float]
    reachable: bool


class QuadRuped:
    MODE_IDLE = "idle"
    MODE_STAND = "stand"
    MODE_WALK = "walk"

    DIRECTION_FORWARD = "forward"
    DIRECTION_BACKWARD = "backward"

    def __init__(self, gyro=None):
        self.mode = self.MODE_STAND

        self.gait = GaitTrot()
        self.phase = 0.0

        self.body_height = config.BODY_STAND_HEIGHT

        # Guvenli-normal varsayilan hiz.
        self.speed_scale = 0.8

        # +1.0 ileri, -1.0 geri.
        self.walk_direction = +1.0
        self.walk_direction_name = self.DIRECTION_FORWARD

        # Tek komut = tek gait cycle = sonra stand.
        self.walk_auto_stop = True
        self.walk_cycles_target = 1.0
        self.walk_cycles_done = 0.0

        self.last_targets: Dict[int, JointTarget] = {}

        self.gyro = gyro
        self.imu_state = None
        self.balance_enabled = gyro is not None

        self.last_pitch_correction_mm = 0.0
        self.last_roll_correction_mm = 0.0

    # ------------------------------------------------------------------
    # Public commands
    # ------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        if mode not in [self.MODE_IDLE, self.MODE_STAND, self.MODE_WALK]:
            raise ValueError(f"Gecersiz mod: {mode}")

        self.mode = mode

        if mode == self.MODE_IDLE:
            self.body_height = config.BODY_IDLE_HEIGHT
        elif mode == self.MODE_STAND:
            self.body_height = config.BODY_STAND_HEIGHT
        elif mode == self.MODE_WALK:
            self.body_height = config.BODY_STAND_HEIGHT

    def stand(self) -> None:
        self.set_mode(self.MODE_STAND)
        self.phase = 0.0

    def idle(self) -> None:
        self.set_mode(self.MODE_IDLE)
        self.phase = 0.0

    def walk(
        self,
        speed_scale: Optional[float] = None,
        direction: str = "forward",
        auto_stop: bool = True,
        cycles: float = 1.0,
    ) -> None:
        """
        Yuruyus moduna alir.

        auto_stop=True ise belirtilen cycle kadar yurur ve sonra stand moduna gecer.
        """
        old_direction = self.walk_direction_name

        if speed_scale is None:
            speed_scale = self.speed_scale

        self.speed_scale = max(0.0, min(2.0, float(speed_scale)))
        self.set_walk_direction(direction)

        # Yeni yuruyus komutunda veya yon degisiminde phase'i temiz baslat.
        if self.mode != self.MODE_WALK or old_direction != self.walk_direction_name:
            self.phase = 0.0

        self.walk_auto_stop = bool(auto_stop)
        self.walk_cycles_target = max(0.1, float(cycles))
        self.walk_cycles_done = 0.0

        self.set_mode(self.MODE_WALK)

    def set_walk_direction(self, direction: str) -> None:
        direction = str(direction).lower().strip()

        if direction in ["forward", "fwd", "ileri", "+", "1"]:
            self.walk_direction = +1.0
            self.walk_direction_name = self.DIRECTION_FORWARD
            return

        if direction in ["backward", "back", "geri", "-", "-1"]:
            self.walk_direction = -1.0
            self.walk_direction_name = self.DIRECTION_BACKWARD
            return

        self.walk_direction = +1.0
        self.walk_direction_name = self.DIRECTION_FORWARD

    def walk_forward(self, speed_scale: Optional[float] = None) -> None:
        self.walk(
            speed_scale=speed_scale,
            direction=self.DIRECTION_FORWARD,
            auto_stop=True,
            cycles=1.0,
        )

    def walk_backward(self, speed_scale: Optional[float] = None) -> None:
        self.walk(
            speed_scale=speed_scale,
            direction=self.DIRECTION_BACKWARD,
            auto_stop=True,
            cycles=1.0,
        )

    def set_body_height(self, height_mm: float) -> None:
        min_h = config.BODY_IDLE_HEIGHT
        max_h = config.FEMUR_LENGTH + config.TIBIA_LENGTH - 10.0
        self.body_height = max(min_h, min(max_h, float(height_mm)))

    def enable_balance(self, enabled: bool = True) -> None:
        if self.gyro is None:
            self.balance_enabled = False
        else:
            self.balance_enabled = bool(enabled)

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> Dict[int, JointTarget]:
        pitch_corr_mm = 0.0

        if self.balance_enabled and self.gyro is not None:
            self.imu_state = self.gyro.update(dt=dt)
            pitch_corr_mm = self.imu_state.pitch_correction_mm

        self.last_pitch_correction_mm = pitch_corr_mm

        if self.imu_state is not None:
            self.last_roll_correction_mm = self.imu_state.roll_correction_mm

        if self.mode == self.MODE_WALK:
            self._advance_phase(dt)

        targets = {}

        for leg in self._leg_order():
            foot = self._target_foot_for_leg(leg)

            if pitch_corr_mm != 0.0:
                if config.is_front_leg(leg):
                    foot.z += pitch_corr_mm
                else:
                    foot.z -= pitch_corr_mm

            hip_deg, knee_deg = inverse_kinematics(foot.x, foot.z)

            reachable = hip_deg is not None and knee_deg is not None
            if reachable:
                reachable = self._inside_joint_limits(hip_deg, knee_deg)

            targets[leg] = JointTarget(
                foot=foot,
                hip_deg=hip_deg,
                knee_deg=knee_deg,
                reachable=reachable,
            )

        self.last_targets = targets
        return targets

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _advance_phase(self, dt: float) -> None:
        if config.GAIT_PERIOD_S <= 0:
            return

        old_phase = self.phase

        phase_step = (dt / config.GAIT_PERIOD_S) * self.speed_scale
        self.phase = (self.phase + phase_step) % 1.0

        # Phase basa sardiginda bir gait cycle tamamlandi.
        if self.phase < old_phase:
            self.walk_cycles_done += 1.0

            if self.walk_auto_stop and self.walk_cycles_done >= self.walk_cycles_target:
                self.stand()

    def _target_foot_for_leg(self, leg: int) -> Vector:
        if self.mode == self.MODE_IDLE:
            return Vector(0.0, self._leg_y_offset(leg), -self.body_height)

        if self.mode == self.MODE_STAND:
            return Vector(0.0, self._leg_y_offset(leg), -self.body_height)

        if self.mode == self.MODE_WALK:
            self.gait.stand_z = -self.body_height
            x, z = self.gait.foot_position(leg, self.phase)

            # forward -> x ayni, backward -> x ters.
            x = x * self.walk_direction

            return Vector(x, self._leg_y_offset(leg), z)

        return Vector(0.0, self._leg_y_offset(leg), -config.BODY_STAND_HEIGHT)

    def _leg_y_offset(self, leg: int) -> float:
        half_w = config.BODY_WIDTH / 2.0
        return -half_w if config.is_right_leg(leg) else +half_w

    def _inside_joint_limits(self, hip_deg: float, knee_deg: float) -> bool:
        hip_ok = config.HIP_MIN_DEG <= hip_deg <= config.HIP_MAX_DEG
        knee_ok = config.KNEE_MIN_DEG <= knee_deg <= config.KNEE_MAX_DEG
        return hip_ok and knee_ok

    def _leg_order(self):
        return [config.LEG_RF, config.LEG_RH, config.LEG_LH, config.LEG_LF]

    # ------------------------------------------------------------------
    # Debug/print helpers
    # ------------------------------------------------------------------
    def print_targets(self, targets: Optional[Dict[int, JointTarget]] = None) -> None:
        if targets is None:
            targets = self.last_targets

        balance_txt = "ON" if self.balance_enabled else "OFF"
        pitch_corr_txt = f"{self.last_pitch_correction_mm:+.2f}mm"

        print(
            f"Mode={self.mode} | phase={self.phase:.3f} | "
            f"height={self.body_height:.1f}mm | "
            f"speed={self.speed_scale:.2f} | "
            f"dir={self.walk_direction_name} | "
            f"balance={balance_txt} | pitch_corr={pitch_corr_txt}"
        )
        print("-" * 86)
        print(f"{'Leg':>4} | {'Foot x':>8} | {'Foot z':>8} | {'Hip':>9} | {'Knee':>9} | OK")
        print("-" * 86)

        for leg in self._leg_order():
            t = targets[leg]
            hip_txt = "None" if t.hip_deg is None else f"{t.hip_deg:+8.2f}"
            knee_txt = "None" if t.knee_deg is None else f"{t.knee_deg:+8.2f}"
            print(
                f"{config.LEG_NAMES[leg]:>4} | "
                f"{t.foot.x:+8.1f} | "
                f"{t.foot.z:+8.1f} | "
                f"{hip_txt:>9} | "
                f"{knee_txt:>9} | "
                f"{'YES' if t.reachable else 'NO'}"
            )


if __name__ == "__main__":
    print("\n>>> TEST 1: STAND")
    dog = QuadRuped()
    dog.stand()
    targets = dog.update(config.CONTROL_LOOP_DT)
    dog.print_targets(targets)

    print("\n>>> TEST 2: WALK FORWARD - one cycle auto-stop")
    dog.walk_forward()
    for i in range(80):
        targets = dog.update(config.CONTROL_LOOP_DT)
        if i % 10 == 0:
            print(f"\nForward step {i}")
            dog.print_targets(targets)

    print("\n>>> TEST 3: WALK BACKWARD - one cycle auto-stop")
    dog.walk_backward()
    for i in range(80):
        targets = dog.update(config.CONTROL_LOOP_DT)
        if i % 10 == 0:
            print(f"\nBackward step {i}")
            dog.print_targets(targets)
