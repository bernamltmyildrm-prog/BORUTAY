"""
test_pid.py
===========
pid.py için hızlı test dosyası.

Çalıştırma:
    python test_pid.py

Beklenen:
    pitch değeri 10 dereceden başlayıp yavaş yavaş 0 dereceye yaklaşmalı.
"""

from pid import PIDController


pid = PIDController(
    kp=0.95,
    ki=0.35,
    kd=0.0,
    target=0.0,
    output_limits=(-30.0, 30.0),
    integral_limits=(-20.0, 20.0),
    deadband=0.05,
)

pitch = 10.0
dt = 0.02

print("=" * 60)
print("PIDController test")
print("=" * 60)
print(f"{'step':>4} | {'pitch':>8} | {'error':>8} | {'output':>8}")
print("-" * 60)

for i in range(30):
    output = pid.update(input_value=pitch, dt=dt)

    # Çok basit sanal sistem modeli:
    # output negatifse pitch azalır.
    pitch += output * 0.04

    print(
        f"{i:4d} | "
        f"{pitch:8.3f} | "
        f"{pid.state.error:8.3f} | "
        f"{pid.state.output:8.3f}"
    )

print("\n>>> Test bitti.")
