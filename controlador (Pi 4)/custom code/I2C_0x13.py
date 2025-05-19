import smbus2
import time
 
cmd_dict = {
    0x01: "SET",
    0x02: "GET",
    0x03: "GET_LEVEL",
    0x12: "TEMPERATURE",
    0x13: "FLOW",
    0x14: "LEVEL",
    0x15: "PWM"
}
 
def send_command(addr, id_byte, cmd):
    packet = bytes([id_byte, cmd, 0])
    write = smbus2.i2c_msg.write(addr, packet)
    bus.i2c_rdwr(write)
    print(f"Enviado: ADD={addr:02x}, CMD={cmd_dict.get(cmd,cmd)}, LEN=0, DATA=[]")
 
def receive_response(addr):
    # Leemos primero cabecera de 3 bytes
    header = smbus2.i2c_msg.read(addr, 3)
    bus.i2c_rdwr(header)
    data3 = list(header)
    response_id, response_cmd, response_len = data3
    # Ahora leemos exactamente los response_len bytes
    body = smbus2.i2c_msg.read(addr, response_len)
    bus.i2c_rdwr(body)
    payload = list(body)
 
    if response_cmd == 0x12 and response_len == 4:
        t1 = (payload[0] | (payload[1] << 8)) / 100.0
        t2 = (payload[2] | (payload[3] << 8)) / 100.0
        print(f"temperatura recibida: Temp1={t1:.2f}°C, Temp2={t2:.2f}°C")
    elif response_cmd == 0x14 and response_len == 2:
        lvl = payload[0] | (payload[1] << 8)
        print(f"nivel recibido: {lvl} cm")
 
    print(f"Recibido: ID={response_id:02x}, ADD={addr:02x}, CMD={cmd_dict.get(response_cmd,response_cmd)}, LEN={response_len}, DATA={payload}")
 
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
