"""
gait.py - Trot yuruyusu icin ayak ucu yorunge ureteci.
"""

import math
import config


class GaitTrot:
    """
    Trot yuruyusu: diagonal ciftler ayni anda swing/stance yapar.
    Cift A: RF + LH (faz offset = 0.0)
    Cift B: LF + RH (faz offset = 0.5)
    """

    PHASE_OFFSETS = {
        config.LEG_RF: 0.0,
        config.LEG_LH: 0.0,
        config.LEG_LF: 0.5,
        config.LEG_RH: 0.5,
    }

    def __init__(self, step_length=None, step_height=None,
                 stand_z=None, swing_ratio=0.5):
        self.step_length = step_length if step_length is not None else config.GAIT_STEP_LENGTH_X
        self.step_height = step_height if step_height is not None else config.GAIT_STEP_HEIGHT_Z
        self.stand_z = stand_z if stand_z is not None else -config.BODY_STAND_HEIGHT
        self.swing_ratio = swing_ratio

    def foot_position(self, leg_index, t):
        """Bacak ve cycle zamani (t, 0..1) icin ayak ucu (x, z) doner."""
        local_t = (t + self.PHASE_OFFSETS[leg_index]) % 1.0

        if local_t < self.swing_ratio:
            # SWING fazi: ayak havada, eliptik yorunge
            s = local_t / self.swing_ratio
            x = -self.step_length / 2.0 + self.step_length * s
            z = self.stand_z + self.step_height * math.sin(math.pi * s)
        else:
            # STANCE fazi: ayak yerde, ileriden geriye
            s = (local_t - self.swing_ratio) / (1.0 - self.swing_ratio)
            x = self.step_length / 2.0 - self.step_length * s
            z = self.stand_z

        return (x, z)


if __name__ == "__main__":
    gait = GaitTrot()

    print(f"GaitTrot parametreleri:")
    print(f"  step_length = {gait.step_length} mm")
    print(f"  step_height = {gait.step_height} mm")
    print(f"  stand_z     = {gait.stand_z} mm")
    print()

    print(f"{'t':>6} | {'RF (x, z)':>17} | {'RH (x, z)':>17} | "
          f"{'LH (x, z)':>17} | {'LF (x, z)':>17}")
    print("-" * 90)

    for i in range(11):
        t = i / 10.0
        rf = gait.foot_position(config.LEG_RF, t)
        rh = gait.foot_position(config.LEG_RH, t)
        lh = gait.foot_position(config.LEG_LH, t)
        lf = gait.foot_position(config.LEG_LF, t)
        print(f"{t:6.2f} | "
              f"({rf[0]:+6.1f}, {rf[1]:+7.1f}) | "
              f"({rh[0]:+6.1f}, {rh[1]:+7.1f}) | "
              f"({lh[0]:+6.1f}, {lh[1]:+7.1f}) | "
              f"({lf[0]:+6.1f}, {lf[1]:+7.1f})")

    print()
    print(">>> RF + LH ayni fazda (diagonal cift A)")
    print(">>> RH + LF ayni fazda (diagonal cift B)")