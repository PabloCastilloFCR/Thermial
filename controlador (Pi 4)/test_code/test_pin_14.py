import smbus2
import time

# I2C-Bus auf dem Pi 4 (Bus 1)
bus = smbus2.SMBus(1)

# Adresse des Pico
PICO_ADDRESS = 0x11

# Befehl, um MOSFET ein/aus zu schalten
CMD_SET = 0x01

while True:
    try:
        # Sende Befehl an Pico
        bus.write_byte(PICO_ADDRESS, CMD_SET)
        print("Befehl gesendet: MOSFET ein/aus blink")
        time.sleep(1)  # 1 Sekunde warten
    except Exception as e:
        print("Fehler bei I2C-Kommunikation:", e)
        break
