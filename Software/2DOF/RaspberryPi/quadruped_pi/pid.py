"""
pid.py
======
Genel amaçlı PID kontrol sınıfı.

Bu dosya donanımdan bağımsızdır.
Şimdilik tek başına test edilir; daha sonra gyro.py içinde kullanılacak.

Kullanım örneği:
    pid = PIDController(kp=0.8, ki=0.0, kd=0.05)
    pid.set_target(0.0)
    correction = pid.update(input_value=current_pitch, dt=0.02)

Robot köpek için ilk kullanım:
    - IMU pitch/roll açısını oku
    - hedef açı = 0 derece
    - PID çıkışı = küçük denge düzeltmesi
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class PIDState:
    """PID'in son durumunu debug etmek için tutulur."""
    error: float = 0.0
    integral: float = 0.0
    derivative: float = 0.0
    output: float = 0.0


class PIDController:
    """
    Genel amaçlı PID kontrolcü.

    Parametreler:
        kp: proportional kazanç
        ki: integral kazanç
        kd: derivative kazanç
        target: hedef değer
        output_limits: çıkış sınırı, örnek (-10, 10)
        integral_limits: integral birikim sınırı
        deadband: hata bu değerin altındaysa 0 kabul edilir
    """

    def __init__(
        self,
        kp: float = 0.0,
        ki: float = 0.0,
        kd: float = 0.0,
        target: float = 0.0,
        output_limits: Optional[Tuple[Optional[float], Optional[float]]] = None,
        integral_limits: Optional[Tuple[Optional[float], Optional[float]]] = None,
        deadband: float = 0.0,
        derivative_on_measurement: bool = True,
    ):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)

        self.target = float(target)
        self.output_limits = output_limits
        self.integral_limits = integral_limits
        self.deadband = abs(float(deadband))
        self.derivative_on_measurement = derivative_on_measurement

        self._last_time: Optional[float] = None
        self._last_error: Optional[float] = None
        self._last_input: Optional[float] = None
        self._integral: float = 0.0

        self.state = PIDState()

    def set_target(self, target: float) -> None:
        """Hedef değeri değiştirir."""
        self.target = float(target)

    def set_gains(self, kp: float, ki: float, kd: float) -> None:
        """PID kazançlarını değiştirir."""
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)

    def set_output_limits(
        self,
        lower: Optional[float],
        upper: Optional[float],
    ) -> None:
        """PID çıkışını sınırlar."""
        self.output_limits = (lower, upper)

    def set_integral_limits(
        self,
        lower: Optional[float],
        upper: Optional[float],
    ) -> None:
        """Integral birikimini sınırlar."""
        self.integral_limits = (lower, upper)

    def reset(self) -> None:
        """PID hafızasını sıfırlar."""
        self._last_time = None
        self._last_error = None
        self._last_input = None
        self._integral = 0.0
        self.state = PIDState()

    def update(self, input_value: float, dt: Optional[float] = None) -> float:
        """
        PID çıkışını hesaplar.

        Parametreler:
            input_value:
                Mevcut ölçüm değeri. Örnek: mevcut pitch açısı.

            dt:
                Zaman adımı, saniye. 50 Hz için 0.02 verilir.
                None verilirse sistem zamanından hesaplanır.

        Dönen:
            PID çıkışı.
        """
        input_value = float(input_value)
        error = self.target - input_value

        if abs(error) < self.deadband:
            error = 0.0

        dt = self._resolve_dt(dt)

        if self._last_error is None:
            derivative = 0.0
        else:
            if self.derivative_on_measurement and self._last_input is not None:
                derivative = -(input_value - self._last_input) / dt
            else:
                derivative = (error - self._last_error) / dt

        self._integral += error * dt
        self._integral = self._clamp(self._integral, self.integral_limits)

        output = (
            self.kp * error +
            self.ki * self._integral +
            self.kd * derivative
        )

        output = self._clamp(output, self.output_limits)

        self._last_error = error
        self._last_input = input_value

        self.state = PIDState(
            error=error,
            integral=self._integral,
            derivative=derivative,
            output=output,
        )

        return output

    # ESP32 referans koddaki compute() ismine alışmak için alias.
    def compute(self, input_value: float, dt: Optional[float] = None) -> float:
        return self.update(input_value=input_value, dt=dt)

    def _resolve_dt(self, dt: Optional[float]) -> float:
        if dt is not None:
            dt = float(dt)
            if dt <= 0.0:
                raise ValueError("dt sıfırdan büyük olmalı.")
            return dt

        now = time.monotonic()

        if self._last_time is None:
            self._last_time = now
            return 1e-6

        resolved_dt = now - self._last_time
        self._last_time = now

        if resolved_dt <= 0.0:
            return 1e-6

        return resolved_dt

    @staticmethod
    def _clamp(
        value: float,
        limits: Optional[Tuple[Optional[float], Optional[float]]],
    ) -> float:
        if limits is None:
            return value

        lower, upper = limits

        if lower is not None and value < lower:
            value = lower

        if upper is not None and value > upper:
            value = upper

        return value

    def __repr__(self) -> str:
        return (
            f"PIDController(kp={self.kp}, ki={self.ki}, kd={self.kd}, "
            f"target={self.target})"
        )


if __name__ == "__main__":
    # Basit self-test:
    # Sanal pitch 10 dereceden başlıyor ve PID 0 dereceye yaklaştırıyor.
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
    print("PID SELF TEST")
    print("=" * 60)
    print(f"{'step':>4} | {'pitch':>8} | {'error':>8} | {'output':>8}")
    print("-" * 60)

    for i in range(30):
        output = pid.update(input_value=pitch, dt=dt)

        # Basit sanal sistem:
        # output negatif geldikçe pitch azalır.
        pitch += output * 0.04

        print(
            f"{i:4d} | "
            f"{pitch:8.3f} | "
            f"{pid.state.error:8.3f} | "
            f"{pid.state.output:8.3f}"
        )

    print("\n>>> PID self-test bitti.")
