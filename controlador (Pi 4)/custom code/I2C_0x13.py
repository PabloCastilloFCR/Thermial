import smbus2
import time
from cmd_dictionary import cmd_dict
 
def send_command(addr, id_byte, cmd, verbose=False):
    bus = smbus2.SMBus(1)
    packet = bytes([id_byte, cmd, 0])
    write = smbus2.i2c_msg.write(addr, packet)
    bus.i2c_rdwr(write)
    bus.close()
    if verbose:
        print(f"Enviado: ADD={addr:02x}, CMD={cmd_dict.get(cmd,cmd)}, LEN=0, DATA=[]")
 
def receive_response(addr, verbose=False):
    # Leemos primero cabecera de 3 bytes
    bus=smbus2.SMBus(1)
    raw = smbus2.i2c_msg.read(addr, 8)
    bus.i2c_rdwr(raw)
    data = list(raw)
    bus.close()
    
    if len(data) < 3:
        print("Antwort zu kurz:", data)
        return

    response_id = data[0]
    response_cmd = data[1]
    response_len = data[2]

    if len(data) < 3 + response_len:
        print("Nicht genug Payload empfangen:", data)
        return

    payload = data[3:3 + response_len]

    if verbose:
        print(f"[DEBUG] payload = {payload} (hex: {[hex(b) for b in payload]})")

    if response_cmd == 0x12 and response_len == 4:
        t3 = (payload[0] | (payload[1] << 8)) / 100.0
        t4 = (payload[2] | (payload[3] << 8)) / 100.0
        if verbose:
            print(f"temperatura recibida: Temp3={t3:.2f}°C, Temp4={t4:.2f}°C")
    elif response_cmd == 0x14 and response_len == 2:
        lvl_raw = (payload[0] | (payload[1] << 8))
        lvl = lvl_raw / 10.0
        if verbose:
            print(f"nivel recibido: {lvl:.2f} cm")
    
    if verbose:
        print(f"Recibido: ID={response_id:02x}, ADD={addr:02x}, CMD={cmd_dict.get(response_cmd,response_cmd)}, LEN={response_len}, DATA={payload}")
    
    return response_cmd, payload

 
if __name__ == "__main__":
    PICO_ADDR = 0x13
    bus = smbus2.SMBus(1)
 
    while True:
        try:
            send_command(PICO_ADDR, 0, 0x02)   # GET temperatura
            time.sleep(0.5)
            receive_response(PICO_ADDR)
 
            send_command(PICO_ADDR, 0, 0x03)   # GET nivel
            time.sleep(0.5)
            receive_response(PICO_ADDR)
 
        except Exception as e:
            print("Error I2C:", e)
        time.sleep(5)

