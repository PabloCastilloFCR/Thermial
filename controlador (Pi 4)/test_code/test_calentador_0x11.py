import smbus2
import time

PICO_ADDRESS = 0x11
bus = smbus2.SMBus(1)

def send_pwm(value):
    value = max(0, min(100, value))  # 0–100%
    try:
        bus.write_byte(PICO_ADDRESS, value)  # Nur ein Byte senden
        print(f"PWM gesendet: {value}%")
    except Exception as e:
        print("Fehler:", e)

if __name__ == "__main__":
    try:
        while True:
            for val in range(0,101,10):
                send_pwm(val)
                time.sleep(0.5)
            for val in range(100,-1,-10):
                send_pwm(val)
                time.sleep(0.5)
    except KeyboardInterrupt:
        bus.close()
        print("Beendet")
