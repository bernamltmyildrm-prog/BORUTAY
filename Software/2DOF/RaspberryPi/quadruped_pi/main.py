"""
main.py
=======
Robot kopek ana programi.

Bu dosya:
    - QuadRuped          -> matematiksel beyin
    - GyroProc           -> MPU-6050 IMU + denge
    - HardwareController -> PCA9685 + servolar
    - CommandHandler     -> terminal / GUI JSON komut yorumlama
    - TCP Server         -> PyQt6 arayuzden komut alma

katmanlarini birlestirir ve 50 Hz kontrol dongusunde calistirir.

Kullanim:
    Windows / donanimsiz test:
        python main.py

    Raspberry Pi / gercek donanim:
        python main.py --real

    IMU kapali test:
        python main.py --no-imu

    TCP server kapali test:
        python main.py --no-tcp

    TCP port degistirme:
        python main.py --tcp-port 5000
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
import threading
from typing import Optional

import config
from quadruped import QuadRuped
from gyro import GyroProc
from hardware import HardwareController
from command_handler import CommandHandler


# =============================================================================
# Klavye okuma (cross-platform, non-blocking)
# =============================================================================
class KeyboardReader:
    """Klavye girisini engellemeden okumak icin platforma gore secim yapar."""

    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        self.disabled = False

        if self.is_windows:
            import msvcrt
            self._msvcrt = msvcrt
            self._old_settings = None
        else:
            import termios
            import tty
            import select
            self._termios = termios
            self._tty = tty
            self._select = select

            if not sys.stdin.isatty():
                self.disabled = True
                self._old_settings = None
                print(">>> stdin bir TTY degil, klavye girisi pasif. Cikis icin Ctrl+C kullan.")
                return

            self._fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)

    def get_key(self) -> Optional[str]:
        if self.disabled:
            return None

        if self.is_windows:
            if self._msvcrt.kbhit():
                ch = self._msvcrt.getch()
                try:
                    return ch.decode("utf-8")
                except UnicodeDecodeError:
                    return None
            return None

        readable, _, _ = self._select.select([sys.stdin], [], [], 0)
        if readable:
            return sys.stdin.read(1)
        return None

    def restore(self) -> None:
        if self.disabled:
            return

        if not self.is_windows and self._old_settings is not None:
            self._termios.tcsetattr(
                self._fd,
                self._termios.TCSADRAIN,
                self._old_settings,
            )


# =============================================================================
# TCP Server
# =============================================================================
class TCPCommandServer:
    """
    PyQt6 arayuzden gelen JSON komutlarini alan TCP server.

    GUI client:
        socket.connect((PI_IP, 5000))
        socket.send(json.dumps(data).encode("utf-8"))
        socket.close()
    """

    def __init__(self, app, host: str = "0.0.0.0", port: int = 5000):
        self.app = app
        self.host = host
        self.port = int(port)

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.server_socket: Optional[socket.socket] = None

    def start(self) -> None:
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f">>> TCP server baslatiliyor: {self.host}:{self.port}")

    def stop(self) -> None:
        self.running = False

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass

        self.server_socket = None

    def _run_server(self) -> None:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(5)
            srv.settimeout(0.5)

            self.server_socket = srv
            print(f">>> TCP server dinlemede: {self.host}:{self.port}")

            while self.running and self.app.running:
                try:
                    client, addr = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                with client:
                    client.settimeout(1.0)
                    try:
                        text = self._recv_text(client)
                        if not text:
                            continue

                        result = self.app.handle_external_command(text)

                        response = {
                            "ok": result.ok,
                            "message": result.message,
                            "mode": self.app.dog.mode,
                            "height": self.app.dog.body_height,
                            "speed": self.app.dog.speed_scale,
                            "direction": self.app.command_handler.last_direction,
                        }

                        client.sendall(json.dumps(response).encode("utf-8"))

                        print(f">>> TCP {addr}: {text}")
                        print(f">>> TCP response: {response}")

                    except Exception as exc:
                        error_response = {
                            "ok": False,
                            "message": f"TCP command error: {exc}",
                        }
                        try:
                            client.sendall(json.dumps(error_response).encode("utf-8"))
                        except Exception:
                            pass
                        print(f">>> TCP hata: {exc}")

        except Exception as exc:
            print(f">>> TCP server baslatilamadi: {exc}")

        finally:
            try:
                if self.server_socket is not None:
                    self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
            print(">>> TCP server kapandi.")

    @staticmethod
    def _recv_text(client: socket.socket) -> str:
        chunks = []

        while True:
            try:
                data = client.recv(4096)
            except socket.timeout:
                break

            if not data:
                break

            chunks.append(data)

            joined = b"".join(chunks)
            if joined.strip().endswith(b"}"):
                break

        return b"".join(chunks).decode("utf-8").strip()


# =============================================================================
# Ana kontrol uygulamasi
# =============================================================================
class Application:
    def __init__(
        self,
        real_hardware: bool = False,
        enable_imu: bool = True,
        enable_tcp: bool = True,
        tcp_host: str = "0.0.0.0",
        tcp_port: int = 5000,
        verbose_hw: bool = False,
    ):
        self.real_hardware = real_hardware
        self.enable_imu = enable_imu
        self.enable_tcp = enable_tcp
        self.tcp_host = tcp_host
        self.tcp_port = int(tcp_port)

        self.state_lock = threading.Lock()

        self.hw = HardwareController(real=real_hardware, verbose=verbose_hw)

        if enable_imu:
            self.gyro = GyroProc(use_fake_if_missing=True)
        else:
            self.gyro = None

        self.dog = QuadRuped(gyro=self.gyro)
        self.dog.stand()

        self.command_handler = CommandHandler(self.dog, verbose=True)

        self.tcp_server: Optional[TCPCommandServer] = None
        if enable_tcp:
            self.tcp_server = TCPCommandServer(
                app=self,
                host=tcp_host,
                port=tcp_port,
            )

        self.running = True
        self.dt = config.CONTROL_LOOP_DT
        self.print_period_s = 0.5
        self._last_print_time = 0.0
        self._step_count = 0

        self._print_help()

    def _print_help(self) -> None:
        print()
        print("=" * 70)
        print("ROBOT KOPEK KONTROL")
        print("=" * 70)
        print(f"  Donanim modu : {'REAL (PCA9685)' if self.real_hardware else 'SIM'}")
        print(f"  IMU          : {'ACIK' if self.gyro is not None else 'KAPALI'}")
        print(f"  TCP Server   : {'ACIK' if self.enable_tcp else 'KAPALI'}")
        if self.enable_tcp:
            print(f"  TCP Address  : {self.tcp_host}:{self.tcp_port}")
        print(f"  Kontrol freq : {config.CONTROL_LOOP_HZ} Hz")
        print()
        print("  Klavye tuslari:")
        print("    SPACE  : stand <-> idle")
        print("    w      : walk forward")
        print("    g      : walk backward")
        print("    s      : stop / stand")
        print("    c      : crouch / idle")
        print("    b      : IMU denge ac/kapat")
        print("    +/-    : govde yuksekligi +/- 5 mm")
        print("    1/2    : yuruyus hizi -/+")
        print("    h      : bu yardimi tekrar goster")
        print("    q      : cikis")
        print()
        print("  GUI JSON ornekleri:")
        print('    {"cmd": "walk", "value": "forward", "sender": "BÖRÜTAY_GUI"}')
        print('    {"cmd": "pose", "value": "stand", "sender": "BÖRÜTAY_GUI"}')
        print("=" * 70)
        print()

    def handle_external_command(self, text: str):
        with self.state_lock:
            result = self.command_handler.handle_json_text(text)
        return result

    def _handle_key(self, key: str) -> None:
        if key in ("q", "\x03"):
            self.running = False
            return

        if key == " ":
            with self.state_lock:
                if self.dog.mode == self.dog.MODE_STAND:
                    self.dog.idle()
                    print(">>> mode: IDLE")
                else:
                    self.dog.stand()
                    print(">>> mode: STAND")
            return

        key_map = {
            "w": "g",
            "g": "w",
            "s": "s",
            "c": "c",
            "+": "+",
            "-": "-",
        }

        if key in key_map:
            with self.state_lock:
                self.command_handler.handle(key_map[key])
            return

        if key == "b":
            with self.state_lock:
                new_state = not self.dog.balance_enabled
                self.dog.enable_balance(new_state)
            print(f">>> IMU balance: {'ACIK' if new_state else 'KAPALI'}")
            return

        if key == "1":
            with self.state_lock:
                self.dog.speed_scale = max(0.3, self.dog.speed_scale - 0.1)
                speed = self.dog.speed_scale
            print(f">>> speed: {speed:.2f}")
            return

        if key == "2":
            with self.state_lock:
                self.dog.speed_scale = min(1.2, self.dog.speed_scale + 0.1)
                speed = self.dog.speed_scale
            print(f">>> speed: {speed:.2f}")
            return

        if key == "h":
            self._print_help()
            return

    def _maybe_print_status(self, now: float) -> None:
        if now - self._last_print_time < self.print_period_s:
            return

        self._last_print_time = now

        balance_txt = "ON" if self.dog.balance_enabled else "OFF"
        imu_txt = ""

        if self.dog.imu_state is not None:
            imu_txt = (
                f" | imu: roll={self.dog.imu_state.roll_deg:+5.1f} "
                f"pitch={self.dog.imu_state.pitch_deg:+5.1f}"
            )

        print(
            f"[{self._step_count:5d}] "
            f"mode={self.dog.mode:<5} "
            f"height={self.dog.body_height:5.1f}mm "
            f"speed={self.dog.speed_scale:3.1f} "
            f"balance={balance_txt}"
            f"{imu_txt}"
        )

    def run(self) -> None:
        keyboard = KeyboardReader()

        if self.tcp_server is not None:
            self.tcp_server.start()

        try:
            next_tick = time.monotonic()

            while self.running:
                loop_start = time.monotonic()

                while True:
                    key = keyboard.get_key()
                    if key is None:
                        break
                    self._handle_key(key)

                with self.state_lock:
                    targets = self.dog.update(dt=self.dt)

                self.hw.apply_targets(targets)
                self._maybe_print_status(loop_start)

                self._step_count += 1

                next_tick += self.dt
                sleep_time = next_tick - time.monotonic()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_tick = time.monotonic()

        except KeyboardInterrupt:
            print("\n>>> Ctrl+C alindi, cikiliyor...")

        finally:
            keyboard.restore()
            self._shutdown()

    def _shutdown(self) -> None:
        print(">>> Robot durduruluyor...")

        self.running = False

        if self.tcp_server is not None:
            self.tcp_server.stop()

        try:
            with self.state_lock:
                self.dog.stand()
                targets = self.dog.update(dt=self.dt)
            self.hw.apply_targets(targets)
            time.sleep(0.3)
        except Exception as exc:
            print(f">>> stand komutu hata verdi: {exc}")

        try:
            self.hw.release_all()
        except Exception as exc:
            print(f">>> release_all hata verdi: {exc}")

        if self.gyro is not None:
            try:
                self.gyro.close()
            except Exception:
                pass

        print(">>> Cikildi. Hosca kal.")


def parse_args():
    parser = argparse.ArgumentParser(description="Robot kopek ana programi.")

    parser.add_argument(
        "--real",
        action="store_true",
        help="Gercek donanim modu (PCA9685). Varsayilan SIM moddur.",
    )

    parser.add_argument(
        "--no-imu",
        action="store_true",
        help="IMU'yu tamamen devre disi birak.",
    )

    parser.add_argument(
        "--no-tcp",
        action="store_true",
        help="TCP server'i kapat.",
    )

    parser.add_argument(
        "--tcp-host",
        default="0.0.0.0",
        help="TCP server host. Varsayilan: 0.0.0.0",
    )

    parser.add_argument(
        "--tcp-port",
        type=int,
        default=5000,
        help="TCP server port. Varsayilan: 5000",
    )

    parser.add_argument(
        "--verbose-hw",
        action="store_true",
        help="Her servo komutunu ekrana yaz.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    app = Application(
        real_hardware=args.real,
        enable_imu=not args.no_imu,
        enable_tcp=not args.no_tcp,
        tcp_host=args.tcp_host,
        tcp_port=args.tcp_port,
        verbose_hw=args.verbose_hw,
    )

    app.run()


if __name__ == "__main__":
    main()
