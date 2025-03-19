import socket
import json
import threading
import time
import hashlib
import os
import random
import string
import config
from Network import local_network

# Constants for network authentication
AUTH_PORT = 17289  # Dedicated authentication port
WS_PORT = config.AppConfiguration.HTTPServer['Port']  # WebSocket server port
BROADCAST_ADDR = '255.255.255.255'
AUTH_MESSAGE_TIMEOUT = 30  

class NetworkAuthBroadcaster:
    def __init__(self, system_log_function):
        """
        Initialize network auth broadcaster
        
        Args:
            system_log_function: Function to use for logging
        """
        self.system_log = system_log_function
        self.processed_messages = set()
        self.is_listening = False
        self.listen_thread = None
        self.instance_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        self.ws_host = config.AppConfiguration.WebsocketServer['Host']
        
        # Try to get the real local IP address
        try:
            self.local_ip = local_network.currentSystem()[0]
        except Exception:
            self.local_ip = "127.0.0.1"
            
        self.system_log(f"Network authentication system initialized with instance ID: {self.instance_id}")
        self.system_log(f"WebSocket server: {self.ws_host}:{WS_PORT}, Local IP: {self.local_ip}")
        
    def broadcast_auth_status(self, user_key):
        """
        Securely broadcast authentication status using hash-based verification
        
        Args:
            user_key: The user key to authenticate with
        """
        try:
           
            salt = os.urandom(16).hex()
            timestamp = str(int(time.time()))
            
            # Create hash of user_key + salt + timestamp

            auth_hash = hashlib.sha256(f"{user_key}{salt}{timestamp}".encode()).hexdigest()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            message = {
                'app': 'encrypta_auth',
                'auth_hash': auth_hash,
                'salt': salt,
                'timestamp': timestamp,
                'hostname': socket.gethostname(),
                'instance_id': self.instance_id,
                
            }
            
            message_bytes = json.dumps(message).encode()
            sent_count = 0
            
            # 1st opn: Send to network broadcast address (reaches all devices)
            try:
                sock.sendto(message_bytes, (BROADCAST_ADDR, AUTH_PORT))
                sent_count += 1
                self.system_log(f"Authentication broadcast sent to {BROADCAST_ADDR}:{AUTH_PORT}")
            except Exception as e:
                self.system_log(f"Failed to send broadcast: {e}")
                
            # 2nd opn: WebSocket host if it's not localhost
            if self.ws_host not in ['localhost', '127.0.0.1']:
                try:
                    sock.sendto(message_bytes, (self.ws_host, AUTH_PORT))
                    sent_count += 1
                    self.system_log(f"Authentication sent directly to WebSocket host: {self.ws_host}:{AUTH_PORT}")
                except Exception as e:
                    self.system_log(f"Failed to send to WebSocket host: {e}")
            
            # 3rd opn: Send to local IP if different from WebSocket host
            if self.local_ip not in ['localhost', '127.0.0.1'] and self.local_ip != self.ws_host:
                try:
                    sock.sendto(message_bytes, (self.local_ip, AUTH_PORT))
                    sent_count += 1
                    self.system_log(f"Authentication sent to local IP: {self.local_ip}:{AUTH_PORT}")
                except Exception as e:
                    self.system_log(f"Failed to send to local IP: {e}")
            
            sock.close()
            
            if sent_count > 0:
                self.system_log(f"Authentication broadcasts sent via {sent_count} methods")
                return True
            else:
                self.system_log("Failed to send authentication broadcast through any method")
                return False
        except Exception as e:
            self.system_log(f"Error broadcasting authentication: {e}")
            return False
    
    def start_listening(self, application_session, on_auth_callback):
        """
        Start listening for authentication broadcasts
        
        Args:
            application_session: Application session object with user_key
            on_auth_callback: Function to call when valid auth is received
        """
        if self.is_listening:
            return False
            
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_for_broadcasts,
            args=(application_session, on_auth_callback),
            daemon=True
        )
        self.listen_thread.start()
        self.system_log(f"Network authentication listener started on port {AUTH_PORT}")
        return True
    
    def stop_listening(self):
        """Stop the  authentication listener"""
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(1)
        self.system_log("Network authentication listener stopped")
    
    def _listen_for_broadcasts(self, application_session, on_auth_callback):
        """Background thread that listens for auth broadcasts"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5) 
            
            # bind to the dedicated auth port
            try:
                sock.bind(('', AUTH_PORT))
                self.system_log(f"Network auth listener bound to dedicated port {AUTH_PORT}")
            except OSError as e:
                self.system_log(f"Error binding to dedicated port {AUTH_PORT}: {e}")
                
                # use the WebSocket port as fallback
                try:
                    sock.bind(('', WS_PORT))
                    self.system_log(f"Network auth listener bound to WebSocket port {WS_PORT} as fallback")
                except OSError as e2:
                    self.system_log(f"Error binding to WebSocket port {WS_PORT}: {e2}")
                    
                    alt_port = AUTH_PORT + 1000
                    try:
                        sock.bind(('', alt_port))
                        self.system_log(f"Network auth listener bound to alternative port {alt_port}")
                    except OSError as e3:
                        self.system_log(f"Failed to bind to any port: {e3}")
                        return
                
            while self.is_listening:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._process_broadcast(data, addr, application_session, on_auth_callback)
                except socket.timeout:
                    
                    continue
                except Exception as e:
                    self.system_log(f"Error receiving broadcast: {e}")
                    time.sleep(1)
            
            sock.close()
        except Exception as e:
            self.system_log(f"Fatal error in network listener: {e}")
    
    def _process_broadcast(self, data, addr, application_session, on_auth_callback):
        """Process received broadcast message"""
        try:
            message = json.loads(data.decode())
            
            # Validate it's our application's message
            if message.get('app') != 'encrypta_auth':
                return
                
            # Get message type (auth or ack)
            message_type = message.get('type', 'auth')
            
            # Handle acknowledgment messages
            if message_type == 'ack':
                target_id = message.get('target_instance_id')
                if target_id == self.instance_id:
                    hostname = message.get('hostname', 'unknown')
                    self.system_log(f"Received authentication acknowledgment from {hostname} ({addr[0]})")
                    print("RECEIVED ACKNOWLEDGMENT")
                return
            
            # Extract message fields
            auth_hash = message.get('auth_hash')
            salt = message.get('salt')
            timestamp = message.get('timestamp')
            hostname = message.get('hostname', 'unknown')
            instance_id = message.get('instance_id', '')
            
            # Skip our own broadcasts
            if instance_id == self.instance_id:
                return
                
            # Create unique message ID to avoid duplicates
            message_id = f"{addr[0]}:{auth_hash}:{timestamp}"
            if message_id in self.processed_messages:
                return
                
            self.processed_messages.add(message_id)
            if len(self.processed_messages) > 100:
                self.processed_messages = set(list(self.processed_messages)[-50:])
                
            # Check if timestamp is recent enough
            current_time = int(time.time())
            if abs(current_time - int(timestamp)) > AUTH_MESSAGE_TIMEOUT:
                self.system_log(f"Skipping outdated auth message from {addr[0]}")
                return
                
            self.system_log(f"Received auth broadcast from {addr[0]} ({hostname})")
            print("RECEIVED AUTH BROADCAST")
            
            # Verify hash if we have a UserKey
            if hasattr(application_session, 'UserKey') and application_session.UserKey:
                expected_hash = hashlib.sha256(
                    f"{application_session.UserKey}{salt}{timestamp}".encode()
                ).hexdigest()
                
                if auth_hash == expected_hash:
                    self.system_log(f"Verified authentication from {hostname} ({addr[0]})")
                    
                    # Call the callback with source IP and hostname
                    if on_auth_callback:
                        on_auth_callback(addr[0], hostname)
                        
                    # Send acknowledgment
                    self._send_acknowledgment(addr[0], AUTH_PORT, instance_id)
                else:
                    self.system_log(f"Authentication failed - hash mismatch from {hostname}")
        except json.JSONDecodeError:
            # Not JSON, ignore silently
            pass
        except Exception as e:
            self.system_log(f"Error processing auth broadcast: {e}")
            
    def _send_acknowledgment(self, target_ip, target_port, target_instance_id):
        """Send acknowledgment back to the broadcaster"""
        try:
            ack_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_message = {
                'app': 'encrypta_auth',
                'type': 'ack',
                'timestamp': str(int(time.time())),
                'hostname': socket.gethostname(),
                'instance_id': self.instance_id,
                'target_instance_id': target_instance_id
            }
            ack_sock.sendto(json.dumps(ack_message).encode(), (target_ip, target_port))
            ack_sock.close()
            self.system_log(f"Sent authentication acknowledgment to {target_ip}:{target_port}")
        except Exception as e:
            self.system_log(f"Failed to send acknowledgment: {e}")

network_auth = NetworkAuthBroadcaster(lambda msg: print(f"[NetworkAuth] {msg}"))


def initialize_network_auth(system_log_function):
    global network_auth
    network_auth = NetworkAuthBroadcaster(system_log_function)
    return network_auth
