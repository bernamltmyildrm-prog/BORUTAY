<p align="center">
  <img src="Documents/Images/robot.jpeg" width="900">
</p>

<h1 align="center">BÖRÜTAY</h1>

<p align="center">
Hybrid Quadruped Robot Platform for Disaster Response and Autonomous Robotics
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red)
![ROS2](https://img.shields.io/badge/ROS2-Micro--ROS-blue)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

---

# Overview

**BÖRÜTAY** is a hybrid quadruped robot platform developed by undergraduate Electrical and Electronics Engineering students at **OSTİM Technical University**.

The project is designed as a modular robotic platform capable of operating in disaster environments. It combines legged locomotion, wheeled mobility, embedded control systems, computer vision, wireless communication and autonomous navigation within a single architecture.

The current version of the robot uses a **2-DOF leg mechanism**, while the next-generation platform is being developed with **3-DOF legs**, wheel modules, robotic arm integration and Micro-ROS based distributed control.

---

# Project Goals

- Hybrid quadruped robot
- Disaster response support platform
- Stable walking algorithm
- Real-time remote control
- Embedded Linux control architecture
- Computer vision
- Modular electronic architecture
- Future autonomous navigation support

---

# Current Features

- 2-DOF Quadruped Walking
- Raspberry Pi 5 Main Controller
- MQTT Communication
- PyQt6 Ground Control Station
- Real-Time Camera Streaming
- Servo Based Inverse Kinematics
- Trot Gait
- Live Robot Status Monitoring

---

# Future Features

- 3-DOF Leg Structure
- Wheel-Leg Hybrid Motion
- Robotic Arm
- RFID Module
- OLED Status Display
- Deneyap Controller Integration
- micro-ROS Communication
- Autonomous Navigation
- SLAM Support
- Object Detection
- Obstacle Avoidance

---

# Hardware

## Main Controller

- Raspberry Pi 5

## Low-Level Controller

- Deneyap Kart

## Servo Motors

- DS3218 Digital Servo Motors

## Motor Driver

- PCA9685 Servo Driver

## Wireless Communication

- Dual MikroTik RouterBOARD Metal 52ac

## Sensors

- Pi Camera Module
- IMU
- RFID
- OLED Display

## Future Actuators

- DC Gear Motors
- Robotic Arm

---

# Software

- Python
- PyQt6
- OpenCV
- MQTT
- Mosquitto
- Raspberry Pi OS
- Micro-ROS (planned)
- Embedded Linux

---

# Repository Structure

```
BORUTAY
│
├── CAD
│   ├── SolidWorks
│   ├── STL
│   └── Assembly
│
├── Documents
│   ├── Graduation_Project
│   ├── TEKNOFEST
│   └── Images
│
├── quadruped_pi
│   ├── gait.py
│   ├── leg.py
│   ├── quadruped.py
│   ├── hardware.py
│   ├── robot_listener.py
│   ├── camera_stream.py
│   ├── config.py
│   └── main.py
│
├── GUI
│
└── README.md
```

---

# Robot Architecture

```
                 GUI (PyQt6)
                      │
               MQTT Communication
                      │
             Raspberry Pi 5
        ┌──────────┼──────────┐
        │          │          │
     Camera      PCA9685     micro-ROS
        │          │          │
     OpenCV      Servos   Deneyap Kart
                              │
                     DC Motors
                     Robotic Arm
                     RFID
                     OLED
```

---

# Computer Vision

The robot streams live video from the Raspberry Pi camera to the Ground Control Station.

Current capabilities:

- Live Camera Feed
- Low-Latency Streaming
- Remote Monitoring

Future capabilities:

- YOLO Object Detection
- Obstacle Detection
- Human Detection
- Autonomous Decision Making

---

# Motion Control

Current locomotion:

- Inverse Kinematics
- Trot Gait
- Servo Angle Calibration
- Smooth Motion Profiles

Future locomotion:

- 3-DOF Leg Kinematics
- Dynamic Walking
- Terrain Adaptation
- Wheel-Leg Hybrid Control

---

# Communication

Current

- MQTT
- TCP/IP Camera Streaming

Future

- micro-ROS
- ROS2 Topics
- Distributed Embedded Nodes

---

# Images

## Robot Platform

<p align="center">
<img src="Documents/Images/robot.jpeg" width="700">
</p>

---

## Mission Control Center

<p align="center">
<img src="Documents/Images/gui.jpeg" width="850">
</p>

---

## Project Team

<p align="center">
<img src="Documents/Images/team1.png" width="800">
</p>

<p align="center">
<img src="Documents/Images/team2.png" width="800">
</p>

---

# Development Roadmap

- ✅ Mechanical Design
- ✅ Electronic Design
- ✅ 2-DOF Walking Robot
- ✅ Raspberry Pi Integration
- ✅ GUI Development
- ✅ MQTT Communication
- ✅ Camera Streaming
- 🚧 3-DOF Upgrade
- 🚧 Wheel Integration
- 🚧 Robotic Arm
- 🚧 RFID
- 🚧 OLED Display
- 🚧 Deneyap Integration
- 🚧 micro-ROS
- 🚧 Autonomous Navigation

---

# Team

## BÖRÜTAY Team

- Berna Meltem Yıldırım
- Ahmet Emirhan Göktürk
- Uygar Baş
- Sıla Özdemir
- Secem Uğus

---

# Advisor

**Dr. Şenol Gülgönül**

Department of Electrical and Electronics Engineering

OSTİM Technical University

---

# License

This project is released under the MIT License.
