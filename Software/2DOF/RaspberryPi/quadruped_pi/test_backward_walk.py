"""
test_backward_walk.py
=====================
Ileri/geri yuruyus yonu testi.

Calistirma:
    python test_backward_walk.py

Beklenen:
    Forward ve backward modda ayni fazda foot.x isaretleri ters olmalidir.
"""

import config
from quadruped import QuadRuped


def print_step(label, dog):
    targets = dog.update(config.CONTROL_LOOP_DT)
    rf_x = targets[config.LEG_RF].foot.x
    rh_x = targets[config.LEG_RH].foot.x
    lh_x = targets[config.LEG_LH].foot.x
    lf_x = targets[config.LEG_LF].foot.x

    print(
        f"{label:<10} | "
        f"dir={dog.walk_direction_name:<8} | "
        f"phase={dog.phase:.3f} | "
        f"RF x={rf_x:+6.1f} | RH x={rh_x:+6.1f} | "
        f"LH x={lh_x:+6.1f} | LF x={lf_x:+6.1f}"
    )


dog_fwd = QuadRuped()
dog_bwd = QuadRuped()

dog_fwd.walk_forward(speed_scale=1.0)
dog_bwd.walk_backward(speed_scale=1.0)

print("=" * 100)
print("FORWARD / BACKWARD GAIT TEST")
print("=" * 100)

for i in range(8):
    print_step("FORWARD", dog_fwd)
    print_step("BACKWARD", dog_bwd)
    print("-" * 100)
