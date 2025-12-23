from smbus2 import SMBus, i2c_msg
import time

def get_level(addr=0x13):
    bus = SMBus(1)
    # Command senden (CMD = 0x03 für Level)
    write = i2c_msg.write(addr, [0x00, 0x03, 0])
    bus.i2c_rdwr(write)
    time.sleep(0.1)
    # Antwort lesen
    read = i2c_msg.read(addr, 8)
    bus.i2c_rdwr(read)
    data = list(read)
    bus.close()

    print(f"[DEBUG] Raw: {data}")
    if len(data) < 5:
        print("Antwort zu kurz")
        return

    payload = data[3:5]
    lvl_raw = payload[0] + (payload[1] << 8)
    lvl = lvl_raw / 10.0
    print(f"Level = {lvl} cm (raw: {lvl_raw})")

while True:
    get_level()
    time.sleep(5)


