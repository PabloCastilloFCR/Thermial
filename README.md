# 🌡️ Thermal System Control

This project implements a **dual-loop control system** for a complex, modeled thermal circulation system (e.g., solar thermal or similar) using a **Multi-Raspberry Pi architecture** and relying on **I2C/MQTT communication**.

It facilitates both local (I2C) and wireless (MQTT) monitoring and control of key actuators (pumps, heaters) and sensors (flow, temperature) within a closed water circuit.

---

## 🏛️ System Architecture Overview

The system is structured in two communication layers: a low-level hardware control layer and a network-level remote access layer. 

| Component | Role | Communication Protocol | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Controller (Raspberry Pi 4)** | **I2C Master** and **MQTT Server/Client** | I2C & MQTT | Executes control logic, handles data logging, and manages network communication with external clients. |
| **Modules (Raspberry Pi Pico/Zero)** | **I2C Peripherals (Slaves)** | I2C | Provides the physical interface to actuators (pumps, heaters) and sensors (flow, temperature). |
| **External Clients** | Monitoring and Control | MQTT (Local/Cloud) | Allows remote operation, monitoring, and data acquisition. |

---

## 🌳 Branch Structure

The repository is organized into two main branches to clearly separate the core hardware control logic from the network communication extension.

### `main` Branch (I2C Base Control)
This is the stable foundation of the project. It contains the **complete I2C control logic** for direct hardware management.

* **Core Function:** Direct, synchronous communication between the Raspberry Pi 4 (Master) and the Pi Picos/Zeros (Peripherals) via the I2C protocol.
* **Data Handling:** Measurement data is collected, logged to the `shared_data_log` list, and can be exported to a local CSV file.
* **Technologies:** Python (Pi 4), Arduino C/C++ (Pi Picos/Zeros), I2C Protocol.

### `MQTT-communication` Branch (Network Extension)
This branch **extends** the I2C base by integrating a wireless communication layer using **MQTT**. This enables remote control and monitoring of the system.

* **Core Function:** Implementation of a robust message-passing system for control commands and data via MQTT.
* **Additional Components:**
    * **MQTT Broker (`server.py`):** Responsible for listening, receiving, and publishing control commands and sensor data.
    * **HiveMQ Integration:** Supports communication with remote clients outside the local network (LAN) using a public HiveMQ broker (including specific port and browser ID logic).

---

## 📂 Repository File Structure

The project organizes code based on the hardware platform it runs on:

| Folder | Platform | Role | Description | Code Example |
| :--- | :--- | :--- | :--- | :--- |
| **`controlador (Pi 4)`** | Raspberry Pi 4 | **Controller Logic** | Contains all Python scripts for system initialization, control execution, and I2C management. | `wrapper_sistema_completo_dos_bombas.py` |
| > `custom code` | | | Core system logic, including the dual-loop structure and logging. | `wrapper_sistema_completo_dos_bombas.py` |
| > `base code` | | | Lower-level I2C communication interface. | `i2c_0x10.py` |
| **`modulos (Pi Zero)`** | Raspberry Pi Pico/Zero | **Peripheral Logic** | Contains the Arduino IDE source codes that run on the I2C peripherals to handle commands and manage hardware (e.g., setting pump power). | Arduino C/C++ Files |
| **`MQTT`** | Raspberry Pi 4 | **Network Logic** | Contains the scripts that implement the MQTT broker and client communication logic (e.g., connecting to the HiveMQ service). | `server.py` (Example) |

---

### ⏭️ Next Step

Would you like me to draft a short **Getting Started** section for the `main` branch, outlining the necessary steps to run the core I2C system?
