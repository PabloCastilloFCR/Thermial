import smbus2
import time

MAX_SAFE_READ_LEN = 32  # Maximum size for the read buffer
 
def send_command(addr, id_byte, cmd, data=[], verbose=False):
    """
    Generic function to send I2C commands to the peripherie device.
    """
    bus = smbus2.SMBus(1)
    # Use i2c_msg.write logic if no data is sent (as seen in the original 0x13.py)
    if not data:
        packet = bytes([id_byte, cmd, 0])
        write = smbus2.i2c_msg.write(addr, packet)
        try:
            bus.i2c_rdwr(write)
            if verbose: print(f"[I2C Base] Sent (msg.write): ADD={addr:02x}, CMD={cmd:02x}")
        except Exception as e:
            if verbose: print(f"[I2C Base] ERROR sending (msg.write) to 0x{addr:02x}: {e}")
    else:
        # Use standard block_data logic for SET commands (as seen in 0x10.py, 0x11.py, etc.)
        packet = [id_byte, cmd, len(data)] + data
        try:
            bus.write_i2c_block_data(addr, 0x00, packet)
            if verbose: print(f"[I2C Base] Sent (block_data): ADD={addr:02x}, CMD={cmd:02x}, DATA={data}")
        except Exception as e:
            if verbose: print(f"[I2C Base] ERROR sending (block_data) to 0x{addr:02x}: {e}")
    bus.close()
 
def receive_response(addr, verbose=False):
    """
    Generic function to receive the I2C response from the slave.
    Reads up to MAX_SAFE_READ_LEN bytes.
    """
    bus=smbus2.SMBus(1)
    try:
        # Read a maximal block size (MAX_SAFE_READ_LEN)
        raw = smbus2.i2c_msg.read(addr, MAX_SAFE_READ_LEN)
        bus.i2c_rdwr(raw)
        data = list(raw)
        bus.close()
    except Exception as e:
        if verbose: print(f"[I2C Base] ERROR reading from 0x{addr:02x}: {e}")
        return None, None
    # Protocol Check: Minimum 3 bytes (ID, CMD, LEN)
    if len(data) < 3:
        if verbose: print("[I2C Base] Error: Response too short for header.")
        return None, None
 
    # Header Extraction
    response_cmd = data[1]
    response_len = data[2]
    # Extract the payload based on the length reported by the Pico (data[2])
    payload = data[3:3 + response_len]
    # Return command code and raw payload data
    return response_cmd, payload