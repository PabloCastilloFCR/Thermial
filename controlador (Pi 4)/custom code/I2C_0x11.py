import smbus2
import time

cmd_dict = {
    0x01: "SET",
    0x02: "GET", #Obtener valores sensores
    0x03: "GET_PWM",
    0x12: "TEMPERATURE",
    0x13: "FLOW",
    0x14: "LEVEL",
    0x15: "PWM"
}

def send_command(PICO_ADDRESS, id, cmd, data=[]):
    bus = smbus2.SMBus(1)  # I2C Bus der Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    cmd_str = "SET" if cmd == 0x01 else "GET"
    print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS):
    try:
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 8) #expectando 8 bytes
        print(f"Datos recibidos (sin procesar): {data}")
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len]

        if response_cmd in cmd_dict:
            response_cmd_str = cmd_dict[response_cmd]
        else:
            response_cmd_str = "UNKNOWN"

        if response_cmd == 0x12:  # Temperatur-Wert
            if len(response_data) == 4: #asegurarnos que recibimos 4 bytes
                temp1_value = response_data[0] + (response_data[1] << 8)
                temp2_value = response_data[2] + (response_data[3] << 8)
                temp1_value /= 100.0
                temp2_value /= 100.0
                print("bytes recibidos:", response_data)
                print(f"temperatura recibida: Temp1 = {temp1_value:.2f}°C, Temp2 = {temp2_value:.2f}°C")
            else:
                print(f"Error: datos incompletos, esperando 4 bytes pero recibo: {response_len}: {response_data}")
    except Exception as e:
            print(f"Error al leer la respuesta: {e}")
            
            
            if response_cmd == 0x15: # PWM-Wert
                pwm_value = response_data[0]
                print(f"PWM recibido: {pwm_value}%")

                print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")
            return response_id, response_cmd, response_data
        
    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None

if __name__ == "__main__":
    PICO_ADDRESSES = [0x11]
    bus = smbus2.SMBus(1)

    value = 0      # PWM para calentador (0-100%)
    increment = 10 # Pasos für PWM

    while True:
        for pico_add in PICO_ADDRESSES:
            # enviar consulta de temperatura (GET)
            send_command(pico_add, 0, 0x02)  # GET temperatura
            time.sleep(0.5)
            receive_response(pico_add)
            time.sleep(0.5)
            
            # enviar orden PWM (SET)
            send_command(pico_add, 0, 0x01, [value])  # GET PWM  
            time.sleep(5)
            
            
        # incrementar o disminuir valor PWM
        value += increment
        if value > 100 or value < 0:
            increment = -increment
            value += increment