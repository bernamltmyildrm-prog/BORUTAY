# BORUTAY

**BORUTAY** is a modular quadruped robot platform developed by the Electrical and Electronics Engineering students of **OSTİM Technical University**.

The project is designed as a disaster support robotic platform capable of operating in hazardous environments through wireless remote control. BORUTAY combines inverse kinematics, embedded systems, computer vision, MQTT communication, and modular hardware architecture into a single robotic platform.

The current version is a **2-DOF quadruped robot** powered by **Raspberry Pi 5**. Future versions will introduce **3-DOF legs, wheel-assisted locomotion, robotic arm integration, RFID identification, OLED interface, Deneyap Kart, and micro-ROS support.**

---

# Project Overview

BORUTAY aims to provide a flexible robotic platform capable of operating in environments where human access is difficult or dangerous.

The current prototype demonstrates:

- Stable standing posture
- Quadruped walking gait
- Wireless MQTT communication
- Desktop Ground Control Station
- Live camera streaming
- Inverse kinematics based leg control
- Real-time servo control

The project continues to evolve toward a more autonomous and intelligent robotic platform.

---

# Current Features

- 2 DOF per leg (8 Servo Motors)
- Raspberry Pi 5 Main Controller
- MQTT Communication
- PyQt6 Ground Control Station
- Live Camera Streaming
- Inverse Kinematics
- Trot Gait
- Servo Calibration
- Hardware & Simulation Modes
- Modular Software Architecture

---

# Planned Features

- 3 DOF Leg Upgrade
- Robot Arm Integration
- Wheel-Leg Hybrid Locomotion
- micro-ROS Architecture
- Deneyap Kart Integration
- RFID Module
- OLED Display
- IMU Integration
- Autonomous Navigation
- Obstacle Detection
- Computer Vision Assisted Mobility

---

# Hardware

## Main Controller

- Raspberry Pi 5

## Communication

- MikroTik RouterBOARD Metal 52ac (x2)

## Servo Driver

- PCA9685

## Actuators

- DS3218 Servo Motors

## Power System

- 3S Li-Ion Battery
- XL4016 DC-DC Converter

## Sensors

Current

- Raspberry Pi Camera Module

Planned

- IMU
- RFID PN532
- OLED Display

---

# Software

Current Software

- Python 3
- PyQt6
- OpenCV
- NumPy
- MQTT (Mosquitto)
- Paho MQTT
- Raspberry Pi OS

Future Software

- micro-ROS
- Deneyap SDK

---

# Software Architecture

```text
              +------------------------+
              |      Desktop GUI       |
              |        (PyQt6)         |
              +-----------+------------+
                          |
                        MQTT
                          |
              +-----------v------------+
              |    robot_listener.py   |
              +-----------+------------+
                          |
              +-----------v------------+
              |    Quadruped Control   |
              +-----------+------------+
                          |
          +---------------+----------------+
          |               |                |
      Inverse IK       Gait Planner    Hardware
          |               |            Controller
          +---------------+----------------+
                          |
                     PCA9685 Driver
                          |
                     Servo Motors
```

---

# Repository Structure

```text
BORUTAY
│
├── CAD
│   └── SolidWorks
│
├── Documents
│   ├── Graduation_Project
│   └── TEKNOFEST
│
├── quadruped_pi
│   ├── main.py
│   ├── robot_listener.py
│   ├── camera_stream.py
│   ├── hardware.py
│   ├── quadruped.py
│   ├── gait.py
│   ├── leg.py
│   ├── config.py
│   ├── pid.py
│   └── ...
│
├── GUI
│
├── README.md
│
├── LICENSE
│
└── .gitignore
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/bernamltmyildrm-prog/BORUTAY.git
```

Enter the project

```bash
cd BORUTAY
```

Install Python dependencies

```bash
pip install -r requirements.txt
```

---

# Running

Start Robot Listener

```bash
python robot_listener.py
```

Start Camera Stream

```bash
python camera_stream.py
```

Launch Ground Control Station

```bash
python main.py
```

---

# Future Roadmap

The BORUTAY platform is actively being expanded with several new capabilities.

Upcoming developments include:

- 3 DOF Quadruped Design
- Robot Arm Mechanism
- Wheel Assisted Walking
- Deneyap Kart Integration
- RFID Authentication
- OLED Information Display
- micro-ROS Communication
- Autonomous Obstacle Avoidance
- Vision-Based Navigation
- SLAM Integration
- AI Assisted Decision Making

---

# Team

## BORUTAY Team

- **Berna Meltem Yıldırım**
- **Ahmet Emirhan Göktürk**
- **Uygar Baş**
- **Sıla Özdemir**

---

## Academic Advisor

**Dr. Şenol Gülgönül**

Department of Electrical and Electronics Engineering

OSTİM Technical University

---

# License

This project is licensed under the MIT License.
