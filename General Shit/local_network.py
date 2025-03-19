import subprocess
import socket
import platform, sys, psutil

def get_hostname(ip_address):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except socket.herror:
        return ""

def currentSystem():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return  (IP, '', socket.gethostname(), f'[{platform.system()} {platform.release()}; {sys.platform}; {platform.architecture()[0]}]', {'PS_BATTERY': psutil.sensors_battery() if psutil.sensors_battery() is not None else 'AC POWER SUPPLY', 'PLATFORM': {'WINDOWS': psutil.WINDOWS, 'LINUX': psutil.LINUX, 'MACOS': psutil.MACOS, 'POSIX': psutil.POSIX}})


def get_local_devices():
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        devices = []
        for line in lines[3:]:
            parts = line.split()
            if len(parts) == 3:
                if parts[2] == 'dynamic':
                    hostname = get_hostname(parts[0])
                    devices.append((parts[0], parts[1], hostname))
        devices.append(currentSystem())
        return devices

    except subprocess.CalledProcessError as e:
        print(f"Error executing 'arp -a': {e}")
        return []
