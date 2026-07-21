"""
test_command_handler.py
=======================
command_handler.py icin hizli test.

Calistirma:
    python test_command_handler.py
"""

from quadruped import QuadRuped
from command_handler import CommandHandler


dog = QuadRuped()
handler = CommandHandler(dog, verbose=True)

commands = [
    "s",
    "c",
    "w",
    '{"cmd": "walk", "value": "forward", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "walk", "value": "backward", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "walk", "value": "left", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "walk", "value": "right", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "pose", "value": "stand", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "pose", "value": "crouch", "sender": "BÖRÜTAY_GUI"}',
    '{"cmd": "walk", "direction": "forward", "speed": 0.8}',
    "+",
    "-",
    "x",
]

print("=" * 80)
print("COMMAND HANDLER TEST")
print("=" * 80)

for cmd in commands:
    print(f"\nCMD: {cmd}")
    result = handler.handle(cmd)

    print(f"ok       : {result.ok}")
    print(f"message  : {result.message}")
    print(f"mode     : {dog.mode}")
    print(f"height   : {dog.body_height:.1f} mm")
    print(f"speed    : {dog.speed_scale:.2f}")
    print(f"direction: {handler.last_direction}")

print("\n>>> Test bitti.")
