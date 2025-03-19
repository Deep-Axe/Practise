import socket
import subprocess
import ipaddress
import concurrent.futures
import platform
import time

def get_network_devices(scan_timeout=5):
    """Discover all devices on the local network including mobile devices"""
    
    # Get current machine's IP and subnet
    def get_local_ip_and_subnet():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't actually connect, just determines routing
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
            subnet = '.'.join(ip.split('.')[0:3]) + '.0/24'  # Assume /24 subnet
            return ip, subnet
        except Exception:
            return '127.0.0.1', '127.0.0.0/24'
        finally:
            s.close()
    
    # Get hostname for an IP
    def get_device_hostname(ip):
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror):
            return ""
    
    # Check if a port is open on a device
    def check_port(ip, port, timeout=0.3):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            result = s.connect_ex((ip, port))
            s.close()
            return result == 0
        except:
            s.close()
            return False
    
    # Mobile devices often have these ports open
    mobile_ports = [
        62078,  # iOS lockdown service
        5353,   # mDNS/Bonjour
        8080,   # Common HTTP proxy port
        8009,   # Chromecast
        1900,   # DLNA/UPnP
        32768,  # Common ephemeral port range start
        49152,  # Another common ephemeral port range
        # Android debug bridge and other services
        5555, 7000, 9000
    ]
    
    common_ports = [80, 443, 22, 445, 139, 8080]
    
    # Ping a device to see if it's online
    def ping(ip):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '1', ip]
        
        try:
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1)
            return output.returncode == 0
        except:
            return False
    
    # Force ARP cache update
    def update_arp_cache(subnet):
        """Send packets to force devices to appear in ARP cache"""
        print("Warming up ARP cache by sending packets to all IPs in subnet...")
        network = ipaddress.IPv4Network(subnet, strict=False)
        
        # Function to check single IP quickly
        def check_ip(ip):
            # Try to connect to port 80 just to trigger ARP
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            try:
                s.connect((str(ip), 80))
            except:
                pass
            finally:
                s.close()
        
        # Use threading to speed up the process
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            list(executor.map(check_ip, list(network.hosts())))
        print("ARP cache warming complete")
    
    # Method 1: ARP table scanning
    def get_arp_devices():
        devices = []
        try:
            # Run ARP command
            command = 'arp -a' if platform.system().lower() != 'linux' else 'ip neigh'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            # Parse output
            for line in result.stdout.splitlines():
                if platform.system().lower() == 'windows':
                    parts = line.split()
                    if len(parts) >= 2:
                        # Skip header lines
                        if parts[0] == "Interface:" or parts[0] == "Internet":
                            continue
                        
                        ip = parts[0]
                        mac = parts[1]
                        
                        # Skip invalid or broadcast MACs
                        if mac == "ff-ff-ff-ff-ff-ff" or mac == "00-00-00-00-00-00":
                            continue
                            
                        hostname = get_device_hostname(ip)
                        devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'method': 'arp'})
                else:  # Linux
                    if 'lladdr' in line.lower():
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[0]
                            mac = parts[4]
                            hostname = get_device_hostname(ip)
                            devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'method': 'arp'})
        except Exception as e:
            print(f"ARP scan error: {e}")
        
        return devices
    
    # Method 2: Port scan with common mobile ports
    def port_scan(subnet):
        devices = []
        local_ip, _ = get_local_ip_and_subnet()
        
        def check_host(ip):
            if ip == local_ip:  # Skip ourselves
                return None
            
            # Test standard ports first (faster check)
            standard_open = False
            for port in common_ports:
                if check_port(ip, port):
                    standard_open = True
                    break
            
            if standard_open or ping(ip):
                # Device responds to standard methods
                open_ports = []
                for port in common_ports + mobile_ports:
                    if check_port(ip, port, timeout=0.5):
                        open_ports.append(port)
                
                # Estimate device type
                device_type = estimate_device_type(ip, open_ports)
                
                # Try to get hostname
                hostname = get_device_hostname(ip)
                
                return {'ip': ip, 'hostname': hostname, 'open_ports': open_ports, 
                        'method': 'port_scan', 'likely_type': device_type}
            else:
                # If no standard ports are open, quickly check just mobile ports
                for port in mobile_ports:
                    if check_port(ip, port, timeout=0.3):
                        hostname = get_device_hostname(ip)
                        return {'ip': ip, 'hostname': hostname, 'open_ports': [port], 
                                'method': 'mobile_port', 'likely_type': 'mobile'}
            return None
        
        network = ipaddress.IPv4Network(subnet, strict=False)
        
        # Use a thread pool for faster scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_host, str(ip)) for ip in network.hosts()]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    devices.append(result)
        
        return devices
    
    # Method 3: Advanced detection specific for smartphones  
    def estimate_device_type(ip, open_ports):
        """Try to determine if a device is likely a mobile device based on open ports"""
        # Check for common mobile device ports
        mobile_fingerprint = set(open_ports).intersection(set(mobile_ports))
        
        if 62078 in open_ports:  # iOS specific
            return "iOS device"
        elif 5555 in open_ports:  # ADB
            return "Android device"
        elif len(mobile_fingerprint) >= 1:
            return "Likely mobile device"
        elif 445 in open_ports and 139 in open_ports:
            return "Windows/Server"
        elif 22 in open_ports:
            return "Linux/Mac/Network device"
        else:
            return "Unknown device"
    
    local_ip, local_subnet = get_local_ip_and_subnet()
    print(f"Scanning network from {local_ip} (subnet: {local_subnet})...")
    
    update_arp_cache(local_subnet)
    all_devices = []
    
    arp_devices = get_arp_devices()
    all_devices.extend(arp_devices)
    
    print("Starting port scan - this may take a few minutes...")
    port_scan_devices = port_scan(local_subnet)
    
    existing_ips = set(device['ip'] for device in all_devices)
    for device in port_scan_devices:
        if device['ip'] not in existing_ips:
            all_devices.append(device)
            existing_ips.add(device['ip'])
        else:
            for existing_device in all_devices:
                if existing_device['ip'] == device['ip']:
                    if 'open_ports' not in existing_device:
                        existing_device['open_ports'] = []
                    if 'open_ports' in device:
                        existing_device['open_ports'] = list(set(existing_device.get('open_ports', []) + device['open_ports']))
                    if 'likely_type' in device:
                        existing_device['likely_type'] = device['likely_type']
    
    # Add this device
    hostname = socket.gethostname()
    self_device = {
        'ip': local_ip,
        'hostname': hostname,
        'is_self': True,
        'method': 'self',
        'likely_type': 'This Computer'
    }
    
    # Check if self is already in the list
    if local_ip not in existing_ips:
        all_devices.append(self_device)
    
    print(f"Found {len(all_devices)} devices on the network")
    return all_devices

if __name__ == "__main__":
    print("Starting comprehensive network device scan (including mobile devices)...")
    print("This may take a few minutes to complete...")
    devices = get_network_devices()
    
    # Group devices by likely type for better readability
    devices_by_type = {}
    for device in devices:
        device_type = device.get('likely_type', 'Unknown')
        if device_type not in devices_by_type:
            devices_by_type[device_type] = []
        devices_by_type[device_type].append(device)
    
    # Print results grouped by device type
    print("\n=== NETWORK SCAN RESULTS ===")
    for device_type, device_list in devices_by_type.items():
        print(f"\n## {device_type.upper()} ({len(device_list)} found)")
        for device in device_list:
            print(f"IP: {device['ip']:<15} Hostname: {device.get('hostname', 'Unknown'):<30} "
                  f"Method: {device['method']}")
            if 'open_ports' in device and device['open_ports']:
                print(f"  Open ports: {device['open_ports']}")
            if 'mac' in device:
                print(f"  MAC: {device['mac']}")
            print()