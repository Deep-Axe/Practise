import socket, serial, time, threading

UDP_PORT   = 4210
STM32_PORT = "/dev/ttyUSB0"   # adjust: ls /dev/ttyUSB* or /dev/ttyACM*
TEENSY_PORT = "/dev/ttyUSB1"  # adjust: the Teensy USB serial device
BAUD       = 115200
WATCHDOG_MS = 300             # zero everything if no packet for this long

stm32  = serial.Serial(STM32_PORT,  BAUD, timeout=1)
teensy = serial.Serial(TEENSY_PORT, BAUD, timeout=1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.settimeout(0.1)

last_rx = time.time()

def send_stm32(dac_val):
    """Send throttle DAC value to STM32."""
    stm32.write(f"DAC:{dac_val}\n".encode())

def send_teensy_steer(angle):
    """Send steer angle to Teensy servo on pin 39."""
    teensy.write(f"S:{angle}\n".encode())

def send_teensy_brake(state: bool):
    """Send motor brake command to Teensy pin 32."""
    teensy.write(f"B:{1 if state else 0}\n".encode())

def safe_stop():
    """Zero all outputs — used by watchdog and STOP command."""
    send_stm32(0)
    send_teensy_steer(135)   # servo to center
    send_teensy_brake(False)

def watchdog():
    while True:
        if time.time() - last_rx > WATCHDOG_MS / 1000.0:
            safe_stop()
        time.sleep(0.05)

t = threading.Thread(target=watchdog, daemon=True)
t.start()

print(f"Listening on UDP {UDP_PORT} | STM32={STM32_PORT} | Teensy={TEENSY_PORT}")

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
        except socket.timeout:
            continue

        last_rx = time.time()
        msg = data.decode().strip()

        if msg == "STOP":
            safe_stop()
            print("\rSTOP                              ", end="", flush=True)
            continue

        try:
            parts = dict(p.split(":") for p in msg.split(","))
            dac   = int(parts["T"])
            steer = int(parts["S"])
            brake = parts.get("B", "0") == "1"   # motor brake flag from sender

            dac   = max(0, min(4096, dac))
            steer = max(0, min(270, steer))

            send_stm32(dac)
            send_teensy_steer(steer)
            send_teensy_brake(brake)

            print(f"\rDAC={dac:4d}  Steer={steer:3d}  Brake={'ON ' if brake else 'OFF'}", end="", flush=True)

        except (KeyError, ValueError) as e:
            print(f"\nParse error: {msg} — {e}")

except KeyboardInterrupt:
    safe_stop()
    print("\nClean exit.")
finally:
    sock.close()
    stm32.close()
    teensy.close()
