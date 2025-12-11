import smbus2
import time
import json
import os
import sys
 
# --- I2C CONFIGURATION ---
MAX_SAFE_READ_LEN = 8  # CRITICAL FIX: Reduced from 32/16 to minimize I2C read timeouts.
 
def load_i2c_address(device_key: str) -> int:
    """
    Loads the I2C address for a device key from the centralized JSON map.
    This function ensures the Driver class (e.g., Heater) knows its current address.
    If the script is run directly, it needs to find the map file relative to the project root.
    """
    try:
        # 1. Determine the path to the project root (Thermial/2_controller)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        controller_dir = os.path.dirname(current_dir) # Moves up to 2_controller/
        project_root = os.path.dirname(controller_dir) # Moves up to Thermial/
        # 2. Define the path to the JSON file
        json_path = os.path.join(project_root, '0_configuration', 'i2c_map.json')
        with open(json_path, 'r') as f:
            i2c_map = json.load(f)
        # 3. Lookup the address using the device key
        address = i2c_map.get(device_key)
        if address is None:
            raise KeyError(f"Device key '{device_key}' not found in i2c_map.json.")
        return address
    except FileNotFoundError:
        # Handle the case where the file location is wrong during different types of execution
        print(f"Error: Configuration file not found at {json_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading I2C address for {device_key}: {e}")
        sys.exit(1)
 
 
def send_command(addr: int, id_byte: int, cmd: int, data: list = [], verbose: bool = False) -> bool:
    """
    Generic function to send I2C commands (SET commands) to the peripheral device (Pico).
    Returns True on success, False on failure.
    """
    bus = smbus2.SMBus(1)
    success = False
 
    try:
        if not data:
            # Use i2c_msg.write for commands without data (e.g., simple GET initiation)
            packet = bytes([id_byte, cmd, 0])
            write = smbus2.i2c_msg.write(addr, packet)
            bus.i2c_rdwr(write)
            if verbose: print(f"[I2C Base] Sent (msg.write): ADD={addr:02x}, CMD={cmd:02x}")
        else:
            # Use standard block_data logic for SET commands with data
            packet = [id_byte, cmd, len(data)] + data
            bus.write_i2c_block_data(addr, 0x00, packet)
            if verbose: print(f"[I2C Base] Sent (block_data): ADD={addr:02x}, CMD={cmd:02x}, DATA={data}")
        success = True
    except Exception as e:
        if verbose: print(f"[I2C Base] ERROR sending command to 0x{addr:02x}: {e}")
        success = False
    finally:
        # CRITICAL FIX: Ensure bus closes, even on success or failure
        try:
            bus.close()
        except:
            pass
    return success
 
 
def receive_response(addr: int, verbose: bool = False) -> tuple[int, list]:
    """
    Generic function to receive the I2C response (GET data) from the slave.
    Returns (response_cmd, payload_list) or (None, None) on failure.
    """
    bus = smbus2.SMBus(1)
    data = []
    try:
        # Read a safe, reduced block size (MAX_SAFE_READ_LEN)
        raw = smbus2.i2c_msg.read(addr, MAX_SAFE_READ_LEN)
        bus.i2c_rdwr(raw)
        data = list(raw)
        bus.close()
    except Exception as e:
        if verbose: print(f"[I2C Base] ERROR reading from 0x{addr:02x}: {e}. Returning None.")
        # CRITICAL FIX: Ensure bus closes on read error to prevent lockup
        try:
            bus.close()
        except:
            pass
        return None, None
    # Protocol Check: Minimum 3 bytes (ID, CMD, LEN)
    if len(data) < 3:
        if verbose: print(f"[I2C Base] Error at 0x{addr:02x}: Response too short for header (Read {len(data)} bytes).")
        return None, None
    # Header Extraction (ID, CMD, LEN)
    response_cmd = data[1]
    response_len = data[2]
    # Extract the payload based on the length reported by the Pico
    payload = data[3:3 + response_len]
    if len(payload) != response_len and verbose:
         print(f"[I2C Base] Warning at 0x{addr:02x}: Reported length ({response_len}) does not match payload size ({len(payload)}).")
    # Return command code and RAW payload data (the bytes that need scaling/decoding)
    return response_cmd, payload