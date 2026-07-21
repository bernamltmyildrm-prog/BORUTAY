"""
test_tcp_client.py
==================
main.py TCP server test client.

Once ayri terminalde main.py calistir:
    python main.py

Sonra bu dosyayi calistir:
    python test_tcp_client.py
"""

import json
import socket
import time


HOST = "127.0.0.1"
PORT = 5000


def send_command(data):
    message = json.dumps(data)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(2.0)
        client.connect((HOST, PORT))
        client.sendall(message.encode("utf-8"))

        try:
            response = client.recv(4096).decode("utf-8")
        except socket.timeout:
            response = ""

    print(f"GONDERILDI: {message}")
    print(f"CEVAP     : {response}")
    print("-" * 80)


commands = [
    {"cmd": "pose", "value": "stand", "sender": "TCP_TEST"},
    {"cmd": "pose", "value": "crouch", "sender": "TCP_TEST"},
    {"cmd": "walk", "value": "forward", "sender": "TCP_TEST"},
    {"cmd": "walk", "direction": "forward", "speed": 0.8, "sender": "TCP_TEST"},
    {"cmd": "pose", "value": "stand", "sender": "TCP_TEST"},
]

for cmd in commands:
    send_command(cmd)
    time.sleep(0.5)

print(">>> TCP client test bitti.")
