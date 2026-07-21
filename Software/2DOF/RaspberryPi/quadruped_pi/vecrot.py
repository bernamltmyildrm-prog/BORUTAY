"""
vecrot.py
=========
Two simple data classes used everywhere:

    Vector  - a position or displacement in 3D space  (x, y, z)
    Rotator - an orientation in 3D space              (yaw, pitch, roll)

Why our own class instead of plain tuples or numpy arrays?
    1. Named fields are clearer: foot.x is more readable than foot[0].
    2. We can pretty-print them (handy for debugging).
    3. Matches the PingguSoft C++ API one-to-one, so anyone comparing
       the two codebases sees the same names.

These are intentionally minimal — almost just struct-like containers.
For heavy math (matrix multiplications etc.) we'll use numpy directly.
"""

from dataclasses import dataclass


@dataclass
class Vector:
    """A point or displacement in 3D space, in millimeters."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def copy(self) -> "Vector":
        return Vector(self.x, self.y, self.z)

    def set(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def zero(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vector":
        return self.__mul__(scalar)

    def __repr__(self) -> str:
        return f"Vector(x={self.x:7.2f}, y={self.y:7.2f}, z={self.z:7.2f})"


@dataclass
class Rotator:
    """An orientation in 3D space, in degrees.

    yaw   = rotation around vertical Z axis  (turning left/right)
    pitch = rotation around lateral Y axis   (nodding forward/back)
    roll  = rotation around longitudinal X axis  (tilting side to side)
    """
    yaw:   float = 0.0
    pitch: float = 0.0
    roll:  float = 0.0

    def copy(self) -> "Rotator":
        return Rotator(self.yaw, self.pitch, self.roll)

    def set(self, yaw: float, pitch: float, roll: float) -> None:
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def zero(self) -> None:
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0

    def __repr__(self) -> str:
        return f"Rotator(yaw={self.yaw:6.2f}, pitch={self.pitch:6.2f}, roll={self.roll:6.2f})"


# Quick self-test if you run this file directly.
if __name__ == "__main__":
    v = Vector(10, 20, 30)
    print(v)

    v2 = v + Vector(1, 1, 1)
    print(v2)

    r = Rotator(yaw=0, pitch=5, roll=-2)
    print(r)