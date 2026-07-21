"""
command_handler.py
==================
Terminal / TCP arayuz / GUI komutlarini robot modlarina ceviren katman.

Bu dosya servo surmez, gait hesaplamaz. Sadece komutu yorumlar ve QuadRuped
nesnesine uygular.

Desteklenen ana komutlar:
    forward / ileri  -> ileri yuru
    backward / geri  -> geri yuru
    stand / kalk     -> kalk / stand
    crouch / comel   -> comel / idle

GUI JSON ornekleri:
    {"cmd": "walk", "value": "forward", "sender": "BÖRÜTAY_GUI"}
    {"cmd": "walk", "value": "backward", "sender": "BÖRÜTAY_GUI"}
    {"cmd": "pose", "value": "stand", "sender": "BÖRÜTAY_GUI"}
    {"cmd": "pose", "value": "crouch", "sender": "BÖRÜTAY_GUI"}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import config


def _cfg(name: str, default):
    return getattr(config, name, default)


HEIGHT_STEP_MM = _cfg("HEIGHT_STEP_MM", 10.0)
MIN_BODY_HEIGHT_MM = _cfg("MIN_BODY_HEIGHT_MM", config.BODY_IDLE_HEIGHT)
MAX_BODY_HEIGHT_MM = _cfg(
    "MAX_BODY_HEIGHT_MM",
    config.FEMUR_LENGTH + config.TIBIA_LENGTH - 10.0,
)
MIN_SPEED_SCALE = _cfg("MIN_SPEED_SCALE", 0.0)
MAX_SPEED_SCALE = _cfg("MAX_SPEED_SCALE", 2.0)


@dataclass
class CommandResult:
    ok: bool
    message: str
    should_quit: bool = False
    raw_command: Optional[Any] = None


class CommandHandler:
    """
    QuadRuped uzerinde yuksek seviye komutlari uygular.
    Bu sinif dogrudan hardware.py kullanmaz.
    """

    def __init__(self, dog, verbose: bool = True):
        self.dog = dog
        self.verbose = verbose
        self.last_direction = "none"
        self.last_command = None

    def handle(self, command: Any) -> CommandResult:
        self.last_command = command

        if isinstance(command, dict):
            return self._handle_dict(command)

        if isinstance(command, str):
            text = command.strip()

            if not text:
                return CommandResult(False, "Bos komut.", raw_command=command)

            if text.startswith("{") and text.endswith("}"):
                try:
                    return self._handle_dict(json.loads(text))
                except json.JSONDecodeError as exc:
                    return CommandResult(False, f"JSON parse hatasi: {exc}", raw_command=command)

            return self._handle_text(text)

        return CommandResult(False, f"Desteklenmeyen komut tipi: {type(command)}", raw_command=command)

    def handle_json_text(self, text: str) -> CommandResult:
        return self.handle(text)

    def _handle_text(self, text: str) -> CommandResult:
        cmd = text.lower()

        aliases = {
            "w": "walk_forward",
            "forward": "walk_forward",
            "walk": "walk_forward",
            "ileri": "walk_forward",

            # main.py'da b IMU balance icin kullanildigi icin klavye geri komutu olarak g onerilir.
            "g": "walk_backward",
            "back": "walk_backward",
            "backward": "walk_backward",
            "geri": "walk_backward",

            "a": "left",
            "left": "left",
            "sol": "left",

            "d": "right",
            "right": "right",
            "sag": "right",
            "sağ": "right",

            "s": "stand",
            "stand": "stand",
            "kalk": "stand",

            "c": "crouch",
            "crouch": "crouch",
            "idle": "crouch",
            "comel": "crouch",
            "çömel": "crouch",

            "x": "stop",
            "stop": "stop",

            "+": "height_up",
            "height_up": "height_up",

            "-": "height_down",
            "height_down": "height_down",

            "q": "quit",
            "quit": "quit",
            "exit": "quit",
        }

        action = aliases.get(cmd)

        if action is None:
            return CommandResult(False, f"Bilinmeyen terminal komutu: {text}", raw_command=text)

        return self._apply_action(action, raw=text)

    def _handle_dict(self, data: Dict[str, Any]) -> CommandResult:
        cmd = str(data.get("cmd", "")).lower().strip()
        value = str(data.get("value", "")).lower().strip()
        direction = str(data.get("direction", value)).lower().strip()
        action_value = str(data.get("action", value)).lower().strip()
        speed = data.get("speed", None)
        height = data.get("height", None)

        if cmd == "walk":
            return self._handle_walk(direction, speed, data)

        if cmd == "pose":
            return self._handle_pose(action_value, height, data)

        if cmd == "stop":
            return self._apply_action("stop", raw=data)

        if cmd == "height":
            return self._handle_height(value, height, data)

        if cmd == "speed":
            return self._handle_speed(value, speed, data)

        if cmd in ["quit", "exit"]:
            return CommandResult(True, "Quit komutu alindi.", should_quit=True, raw_command=data)

        return CommandResult(False, f"Bilinmeyen JSON cmd: {cmd}", raw_command=data)

    def _handle_walk(self, direction: str, speed: Any, data: Dict[str, Any]) -> CommandResult:
        if speed is not None:
            try:
                self.dog.speed_scale = self._clamp(float(speed), MIN_SPEED_SCALE, MAX_SPEED_SCALE)
            except Exception:
                return CommandResult(False, f"Gecersiz speed degeri: {speed}", raw_command=data)

        if direction in ["forward", "fwd", "ileri", ""]:
            return self._apply_action("walk_forward", raw=data)

        if direction in ["backward", "back", "geri"]:
            return self._apply_action("walk_backward", raw=data)

        if direction in ["left", "sol"]:
            return self._apply_action("left", raw=data)

        if direction in ["right", "sag", "sağ"]:
            return self._apply_action("right", raw=data)

        return CommandResult(False, f"Bilinmeyen walk direction: {direction}", raw_command=data)

    def _handle_pose(self, action: str, height: Any, data: Dict[str, Any]) -> CommandResult:
        if action in ["stand", "kalk"]:
            result = self._apply_action("stand", raw=data)
        elif action in ["crouch", "idle", "comel", "çömel"]:
            result = self._apply_action("crouch", raw=data)
        else:
            return CommandResult(False, f"Bilinmeyen pose action: {action}", raw_command=data)

        if height is not None and str(height).lower() != "default":
            try:
                self.dog.set_body_height(float(height))
                return CommandResult(
                    True,
                    f"{result.message} Height={self.dog.body_height:.1f} mm",
                    raw_command=data,
                )
            except Exception:
                return CommandResult(False, f"Gecersiz height degeri: {height}", raw_command=data)

        return result

    def _handle_height(self, value: str, height: Any, data: Dict[str, Any]) -> CommandResult:
        if value in ["up", "+", "increase"]:
            return self._apply_action("height_up", raw=data)

        if value in ["down", "-", "decrease"]:
            return self._apply_action("height_down", raw=data)

        if height is not None:
            try:
                self.dog.set_body_height(float(height))
                return CommandResult(True, f"Body height set: {self.dog.body_height:.1f} mm", raw_command=data)
            except Exception:
                return CommandResult(False, f"Gecersiz height degeri: {height}", raw_command=data)

        return CommandResult(False, "Height komutu eksik.", raw_command=data)

    def _handle_speed(self, value: str, speed: Any, data: Dict[str, Any]) -> CommandResult:
        current = getattr(self.dog, "speed_scale", 1.0)

        if value in ["up", "+", "increase"]:
            self.dog.speed_scale = self._clamp(current + 0.1, MIN_SPEED_SCALE, MAX_SPEED_SCALE)
            return CommandResult(True, f"Speed scale: {self.dog.speed_scale:.2f}", raw_command=data)

        if value in ["down", "-", "decrease"]:
            self.dog.speed_scale = self._clamp(current - 0.1, MIN_SPEED_SCALE, MAX_SPEED_SCALE)
            return CommandResult(True, f"Speed scale: {self.dog.speed_scale:.2f}", raw_command=data)

        if speed is not None:
            try:
                self.dog.speed_scale = self._clamp(float(speed), MIN_SPEED_SCALE, MAX_SPEED_SCALE)
                return CommandResult(True, f"Speed scale: {self.dog.speed_scale:.2f}", raw_command=data)
            except Exception:
                return CommandResult(False, f"Gecersiz speed degeri: {speed}", raw_command=data)

        return CommandResult(False, "Speed komutu eksik.", raw_command=data)

    def _apply_action(self, action: str, raw: Any = None) -> CommandResult:
        if action == "walk_forward":
            self.last_direction = "forward"

            if hasattr(self.dog, "walk_forward"):
                self.dog.walk_forward(speed_scale=getattr(self.dog, "speed_scale", 1.0))
            else:
                self.dog.walk(speed_scale=getattr(self.dog, "speed_scale", 1.0))

            return self._ok(f"Walk forward aktif. speed={self.dog.speed_scale:.2f}", raw)

        if action == "walk_backward":
            self.last_direction = "backward"

            if hasattr(self.dog, "walk_backward"):
                self.dog.walk_backward(speed_scale=getattr(self.dog, "speed_scale", 1.0))
            else:
                self.dog.walk(speed_scale=getattr(self.dog, "speed_scale", 1.0))

            return self._ok(f"Walk backward aktif. speed={self.dog.speed_scale:.2f}", raw)

        if action == "left":
            self.last_direction = "left"
            return self._ok("Left komutu alindi. 2-DOF sistemde strafe desteklenmiyor.", raw)

        if action == "right":
            self.last_direction = "right"
            return self._ok("Right komutu alindi. 2-DOF sistemde strafe desteklenmiyor.", raw)

        if action == "stand":
            self.last_direction = "none"
            self.dog.stand()
            return self._ok(f"Stand/KALK modu. height={self.dog.body_height:.1f} mm", raw)

        if action == "crouch":
            self.last_direction = "none"
            self.dog.idle()
            return self._ok(f"Crouch/COMEL modu. height={self.dog.body_height:.1f} mm", raw)

        if action == "stop":
            self.last_direction = "none"
            self.dog.stand()
            return self._ok("Stop komutu: robot stand moduna alindi.", raw)

        if action == "height_up":
            new_height = self._clamp(
                self.dog.body_height + HEIGHT_STEP_MM,
                MIN_BODY_HEIGHT_MM,
                MAX_BODY_HEIGHT_MM,
            )
            self.dog.set_body_height(new_height)
            return self._ok(f"Height up: {self.dog.body_height:.1f} mm", raw)

        if action == "height_down":
            new_height = self._clamp(
                self.dog.body_height - HEIGHT_STEP_MM,
                MIN_BODY_HEIGHT_MM,
                MAX_BODY_HEIGHT_MM,
            )
            self.dog.set_body_height(new_height)
            return self._ok(f"Height down: {self.dog.body_height:.1f} mm", raw)

        if action == "quit":
            return CommandResult(True, "Quit komutu alindi.", should_quit=True, raw_command=raw)

        return CommandResult(False, f"Bilinmeyen action: {action}", raw_command=raw)

    def _ok(self, message: str, raw: Any = None) -> CommandResult:
        if self.verbose:
            print(f">>> {message}")
        return CommandResult(True, message, raw_command=raw)

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))


if __name__ == "__main__":
    from quadruped import QuadRuped

    dog = QuadRuped()
    handler = CommandHandler(dog, verbose=True)

    commands = [
        '{"cmd": "walk", "value": "forward", "sender": "TEST"}',
        '{"cmd": "walk", "value": "backward", "sender": "TEST"}',
        "w",
        "g",
        "s",
        "c",
    ]

    print("=" * 80)
    print("COMMAND HANDLER SELF TEST - FORWARD/BACKWARD")
    print("=" * 80)

    for cmd in commands:
        print(f"\nCMD: {cmd}")
        result = handler.handle(cmd)
        print(f"ok={result.ok}, message={result.message}")
        print(f"mode={dog.mode}, direction={getattr(dog, 'walk_direction_name', 'n/a')}, last_dir={handler.last_direction}")
