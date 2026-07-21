"""
BÖRÜTAY Raspberry Pi - Robot Kontrol Servisi (MQTT LISTENER)
===========================================================

TCP kullanmaz.
main.py dosyasındaki Application sınıfını içe aktarır.
MQTT komutlarını doğrudan robot uygulamasına iletir.
IMU aktif edilmez; arayüz için fake IMU telemetri gönderilir.
"""

import json
import math
import time
import threading

import paho.mqtt.client as mqtt

from main import Application


class MQTTListener:
    def __init__(
        self,
        robot_app,
        broker_ip="localhost",
        port=1883,
        username="borutay",
        password="borutay2025",
    ):
        self.app = robot_app
        self.broker_ip = broker_ip
        self.port = int(port)
        self.username = username
        self.password = password

        self.last_seq = {}
        self.running = True

        # Simülasyon başlangıç değerleri
        self.start_time = time.time()
        self.sim_battery_percent = 81.0
        self.sim_motor_temp = 15.0

        self.client = mqtt.Client(
            client_id="BORUTAY_PI_LISTENER",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        # Mosquitto şifreli olduğu için aktif olmalı
        self.client.username_pw_set(self.username, self.password)

        self.client.will_set(
            "borutay/status/pi",
            json.dumps({"online": False, "reason": "unexpected"}),
            qos=1,
            retain=True,
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self):
        try:
            self.client.connect(self.broker_ip, self.port, keepalive=30)
            self.client.loop_start()

            threading.Thread(target=self.telemetry_loop, daemon=True).start()

            print(">>> MQTT Listener başladı.")
            print(">>> TCP KAPALI. Komutlar doğrudan main.Application içine gidiyor.")

        except Exception as e:
            print(f">>> [HATA] MQTT Broker'a bağlanılamadı: {e}")

    def stop(self):
        self.running = False

        try:
            self.client.publish(
                "borutay/status/pi",
                json.dumps({"online": False, "reason": "shutdown"}),
                qos=1,
                retain=True,
            )
            time.sleep(0.1)
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

        print(">>> MQTT Listener kapatıldı.")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(">>> MQTT bağlantısı başarılı.")
            print(">>> Dinlenen topic: borutay/cmd/#")

            client.subscribe("borutay/cmd/#", qos=1)

            client.publish(
                "borutay/status/pi",
                json.dumps({"online": True, "ts": time.time()}),
                qos=1,
                retain=True,
            )
        else:
            print(f">>> MQTT bağlantı reddedildi. rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload_text = msg.payload.decode("utf-8").strip()

            try:
                payload = json.loads(payload_text) if payload_text else {}
            except json.JSONDecodeError:
                payload = {"value": payload_text}

            cmd_type = msg.topic.split("/")[-1]
            seq = payload.get("seq", None)
            value = payload.get("value")

            print(f">>> [MQTT] topic={msg.topic}, payload={payload}")

            # Sequence kontrolü sadece seq varsa yapılsın.
            # GUI seq göndermiyorsa komutlar engellenmesin.
            if seq is not None:
                if cmd_type in self.last_seq and seq <= self.last_seq[cmd_type]:
                    print(">>> [MQTT] Eski seq komutu atlandı.")
                    return
                self.last_seq[cmd_type] = seq

            # Emergency
            if cmd_type == "emergency":
                print("\n>>> [MQTT] ACİL DURDURMA ALINDI!\n")

                with self.app.state_lock:
                    # Güvenli duruş: stand/stop
                    self.app.command_handler.handle("s")

                return

            # GUI ileri/geri gönderiyor ama fiziksel yön ters olduğu için burada çeviriyoruz.
            if cmd_type == "walk":
                if value == "forward":
                    value = "backward"
                elif value == "backward":
                    value = "forward"
                elif value in ("left", "right"):
                    print(f">>> [MQTT] '{value}' komutu şu an desteklenmiyor, yok sayıldı.")
                    return

            # GUI speed up/down gönderiyor.
            # CommandHandler klavye mantığında 1/2 destekliyorsa bunu direkt handle ile yapıyoruz.
            if cmd_type == "speed":
                with self.app.state_lock:
                    if value == "down":
                        self.app.command_handler.handle("1")
                    elif value == "up":
                        self.app.command_handler.handle("2")
                    else:
                        print(f">>> [MQTT] Bilinmeyen speed value: {value}")
                return

            # Normal command_handler JSON formatı
            simulated_json = json.dumps({
                "cmd": cmd_type,
                "value": value,
                "sender": "GUI_MQTT",
            })

            result = self.app.handle_external_command(simulated_json)

            print(
                f">>> [MQTT] Komut işlendi: {simulated_json} | "
                f"ok={result.ok} msg={result.message}"
            )

        except Exception as e:
            print(f">>> [MQTT HATA] Mesaj işlenemedi: {e}")

    def telemetry_loop(self):
        """
        Arayüze telemetri gönderir.
        IMU aktif değil; fake IMU değerleri gönderilir.
        """
        while self.running and self.app.running:
            try:
                now = time.time()
                elapsed = now - self.start_time

                # Heartbeat
                self.client.publish(
                    "borutay/status/heartbeat",
                    json.dumps({"ts": now}),
                    qos=0,
                )

                # Fake IMU
                fake_pitch = 2.0 * math.sin(elapsed * 0.7)
                fake_roll = 1.5 * math.sin(elapsed * 0.5)
                fake_yaw = 0.0

                self.client.publish(
                    "borutay/telemetry/imu",
                    json.dumps({
                        "pitch": round(fake_pitch, 1),
                        "roll": round(fake_roll, 1),
                        "yaw": round(fake_yaw, 1),
                    }),
                    qos=0,
                )

                # Batarya simülasyonu
                battery_drops = int(elapsed // 180)
                current_battery_percent = max(
                    0.0,
                    self.sim_battery_percent - battery_drops,
                )
                current_voltage = 10.0 + (current_battery_percent / 100.0) * 2.6

                self.client.publish(
                    "borutay/telemetry/battery",
                    json.dumps({
                        "voltage": round(current_voltage, 1),
                        "percent": round(current_battery_percent, 1),
                    }),
                    qos=0,
                )

                # Motor sıcaklığı simülasyonu
                temp_steps = int(elapsed // 30)
                current_temp = min(
                    60.0,
                    self.sim_motor_temp + (temp_steps * 5.0),
                )

                self.client.publish(
                    "borutay/telemetry/temperature",
                    json.dumps({
                        "motor_temp": round(current_temp, 1),
                    }),
                    qos=0,
                )

                # Robot durum bilgisi
                self.client.publish(
                    "borutay/status/robot",
                    json.dumps({
                        "mode": self.app.dog.mode,
                        "height": round(self.app.dog.body_height, 1),
                        "speed": round(self.app.dog.speed_scale, 2),
                        "ts": now,
                    }),
                    qos=0,
                )

            except Exception as e:
                print(f">>> [TELEMETRI HATA] {e}")

            time.sleep(1)


if __name__ == "__main__":
    # IMU devrede bağlı olabilir ama yazılımsal olarak aktif etmiyoruz.
    # TCP kullanmıyoruz.
    robot_app = Application(
        real_hardware=True,
        enable_imu=False,
        enable_tcp=False,
    )

    listener = MQTTListener(
        robot_app=robot_app,
        broker_ip="localhost",
        port=1883,
        username="borutay",
        password="borutay2025",
    )

    listener.start()

    try:
        robot_app.run()
    finally:
        listener.stop()