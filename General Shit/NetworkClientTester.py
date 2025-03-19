import socket
import json
import threading
import time
import hashlib
import os
import random
import string
import argparse
import sys
import datetime

# Constants for network communication
BROADCAST_PORT = 17289
BROADCAST_ADDR = '255.255.255.255'
AUTH_MESSAGE_TIMEOUT = 30  # Seconds before a message is considered expired

class ColorPrint:
    """Helper class for colored console output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def print(text, color=None):
        if color:
            print(f"{color}{text}{ColorPrint.ENDC}")
        else:
            print(text)

def get_timestamp():
    """Return current timestamp string"""
    return datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

class NetworkAuthTester:
    def __init__(self, user_key=None):
        """Initialize the network auth test client"""
        self.user_key = user_key or ''.join(random.choice(string.ascii_letters) for _ in range(30))
        self.processed_messages = set()
        self.is_listening = False
        self.listen_thread = None
        self.instance_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        self.hostname = socket.gethostname()
        ColorPrint.print(f"[{get_timestamp()}] Network authentication test client initialized", ColorPrint.HEADER)
        ColorPrint.print(f"[{get_timestamp()}] Instance ID: {self.instance_id}", ColorPrint.BLUE)
        if user_key:
            ColorPrint.print(f"[{get_timestamp()}] Using provided user key: {self.user_key[:6]}...{self.user_key[-6:]}", ColorPrint.YELLOW)
        else:
            ColorPrint.print(f"[{get_timestamp()}] Using generated user key: {self.user_key[:6]}...{self.user_key[-6:]}", ColorPrint.YELLOW)
        
    def broadcast_auth_status(self):
        """Securely broadcast authentication status using hash-based verification"""
        try:
            # Generate random salt and timestamp
            salt = os.urandom(16).hex()
            timestamp = str(int(time.time()))
            
            # Create hash of user_key + salt + timestamp
            # This allows verification without exposing the key
            auth_hash = hashlib.sha256(f"{self.user_key}{salt}{timestamp}".encode()).hexdigest()
            
            # Create UDP socket for broadcasting
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Create message with hash, salt and timestamp
            message = {
                'app': 'encrypta_auth',
                'auth_hash': auth_hash,
                'salt': salt,
                'timestamp': timestamp,
                'hostname': self.hostname,
                'instance_id': self.instance_id
            }
            
            # Send the broadcast
            sock.sendto(json.dumps(message).encode(), (BROADCAST_ADDR, BROADCAST_PORT))
            sock.close()
            
            ColorPrint.print(f"[{get_timestamp()}] Authentication broadcast sent to network", ColorPrint.GREEN)
            return True
        except Exception as e:
            ColorPrint.print(f"[{get_timestamp()}] Error broadcasting authentication: {e}", ColorPrint.RED)
            return False
    
    def start_listening(self):
        """Start listening for authentication broadcasts"""
        if self.is_listening:
            return False
            
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_for_broadcasts,
            daemon=True
        )
        self.listen_thread.start()
        ColorPrint.print(f"[{get_timestamp()}] Network authentication listener started", ColorPrint.GREEN)
        return True
    
    def stop_listening(self):
        """Stop the network authentication listener"""
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(1)
        ColorPrint.print(f"[{get_timestamp()}] Network authentication listener stopped", ColorPrint.YELLOW)
    
    def _listen_for_broadcasts(self):
        """Background thread that listens for auth broadcasts"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)  # Short timeout to check is_listening flag
            
            try:
                sock.bind(('', BROADCAST_PORT))
                ColorPrint.print(f"[{get_timestamp()}] Network auth listener bound to port {BROADCAST_PORT}", ColorPrint.BLUE)
            except OSError as e:
                ColorPrint.print(f"[{get_timestamp()}] Error binding to port {BROADCAST_PORT}: {e}", ColorPrint.RED)
                return
                
            while self.is_listening:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._process_broadcast(data, addr)
                except socket.timeout:
                    # This is expected due to the timeout we set
                    continue
                except Exception as e:
                    ColorPrint.print(f"[{get_timestamp()}] Error receiving broadcast: {e}", ColorPrint.RED)
                    time.sleep(1)
            
            sock.close()
        except Exception as e:
            ColorPrint.print(f"[{get_timestamp()}] Fatal error in network listener: {e}", ColorPrint.RED)
    
    def _process_broadcast(self, data, addr):
        """Process received broadcast message"""
        try:
            message = json.loads(data.decode())
            
            # Verify it's our application's message
            if message.get('app') != 'encrypta_auth':
                return
                
            # Extract message data
            auth_hash = message.get('auth_hash')
            salt = message.get('salt')
            timestamp = message.get('timestamp')
            hostname = message.get('hostname', 'unknown')
            instance_id = message.get('instance_id', '')
            
            # Skip our own broadcasts
            if instance_id == self.instance_id:
                return
                
            # Generate message ID to avoid processing duplicates
            message_id = f"{addr[0]}:{auth_hash}:{timestamp}"
            if message_id in self.processed_messages:
                return
                
            self.processed_messages.add(message_id)
            # Limit cache size to prevent memory issues
            if len(self.processed_messages) > 100:
                self.processed_messages = set(list(self.processed_messages)[-50:])
                
            # Check if timestamp is recent enough
            current_time = int(time.time())
            if abs(current_time - int(timestamp)) > AUTH_MESSAGE_TIMEOUT:
                ColorPrint.print(f"[{get_timestamp()}] Skipping outdated auth message from {addr[0]}", ColorPrint.YELLOW)
                return
                
            ColorPrint.print(f"[{get_timestamp()}] Received auth broadcast from {addr[0]} ({hostname})", ColorPrint.BLUE)
            
            # Calculate expected hash using our user key
            expected_hash = hashlib.sha256(
                f"{self.user_key}{salt}{timestamp}".encode()
            ).hexdigest()
            
            # If hashes match, authentication is verified
            if auth_hash == expected_hash:
                ColorPrint.print(f"[{get_timestamp()}] ✅ Verified authentication from {addr[0]} ({hostname})", ColorPrint.GREEN)
                ColorPrint.print(f"[{get_timestamp()}] 🔑 User key matches! Cross-device authentication successful.", ColorPrint.GREEN + ColorPrint.BOLD)
            else:
                ColorPrint.print(f"[{get_timestamp()}] ❌ Authentication verification failed from {addr[0]} ({hostname})", ColorPrint.RED)
                ColorPrint.print(f"[{get_timestamp()}] 🔒 User key doesn't match. Different user or incorrect implementation.", ColorPrint.RED)
            
        except json.JSONDecodeError:
            # Not a JSON message, ignore
            pass
        except Exception as e:
            ColorPrint.print(f"[{get_timestamp()}] Error processing auth broadcast: {e}", ColorPrint.RED)

def show_help():
    """Show interactive help"""
    ColorPrint.print("\n=== Encrypta Auth Network Test Client ===", ColorPrint.HEADER + ColorPrint.BOLD)
    ColorPrint.print("Available commands:", ColorPrint.BOLD)
    ColorPrint.print("  send     - Broadcast authentication to network")
    ColorPrint.print("  status   - Show current status")
    ColorPrint.print("  userkey  - Show/update current user key")
    ColorPrint.print("  key      - Set new user key")
    ColorPrint.print("  help     - Show this help")
    ColorPrint.print("  exit     - Exit the test client")
    print()

def main():
    parser = argparse.ArgumentParser(description='Encrypta Auth Network Test Client')
    parser.add_argument('-k', '--key', help='User key for authentication')
    args = parser.parse_args()
    
    tester = NetworkAuthTester(args.key)
    tester.start_listening()
    
    show_help()
    
    try:
        while True:
            command = input("\nEnter command (help for commands): ").strip().lower()
            
            if command == 'send':
                tester.broadcast_auth_status()
            elif command == 'status':
                ColorPrint.print(f"[{get_timestamp()}] Test client status:", ColorPrint.HEADER)
                ColorPrint.print(f"  Instance ID: {tester.instance_id}", ColorPrint.BLUE)
                ColorPrint.print(f"  Hostname: {tester.hostname}", ColorPrint.BLUE)
                ColorPrint.print(f"  User key: {tester.user_key[:6]}...{tester.user_key[-6:]}", ColorPrint.YELLOW)
                ColorPrint.print(f"  Listening: {tester.is_listening}", ColorPrint.GREEN if tester.is_listening else ColorPrint.RED)
            elif command == 'userkey':
                ColorPrint.print(f"[{get_timestamp()}] Current user key: {tester.user_key}", ColorPrint.YELLOW)
            elif command == 'key':
                new_key = input("Enter new user key: ").strip()
                if new_key:
                    tester.user_key = new_key
                    ColorPrint.print(f"[{get_timestamp()}] User key updated: {tester.user_key[:6]}...{tester.user_key[-6:]}", ColorPrint.GREEN)
                else:
                    ColorPrint.print(f"[{get_timestamp()}] Key not updated (empty input)", ColorPrint.RED)
            elif command == 'help':
                show_help()
            elif command == 'exit':
                break
            else:
                ColorPrint.print(f"[{get_timestamp()}] Unknown command: {command}", ColorPrint.RED)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        tester.stop_listening()
        print("Goodbye!")

if __name__ == "__main__":
    main()