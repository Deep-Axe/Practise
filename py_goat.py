import serial
import csv
import time
import argparse
import os
import glob

def find_arduino_port():
    if os.name == 'nt':  # Windows
        ports = list(sorted(glob.glob("COM[0-9]*")))
        if ports:
            return ports[0]  
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Send CSV velocity data to Arduino')
    parser.add_argument('csv_file', type=str, help='Path to CSV file')
    parser.add_argument('--port', type=str, help='Serial port for Arduino (e.g., COM3)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    parser.add_argument('--interval', type=float, default=0.2, 
                      help='Interval between data points (seconds)')
    args = parser.parse_args()
    
    # Auto-detect port if not specified
    if not args.port:
        args.port = find_arduino_port()
        if not args.port:
            print("Arduino port not found automatically. Please specify with --port")
            return
    
    try:
        if not os.path.exists(args.csv_file):
            print(f"Error: CSV file '{args.csv_file}' not found")
            return
            
        print(f"Connecting to Arduino on {args.port} at {args.baud} baud...")
        arduino = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)  # Allow time for Arduino to reset
        print("Connected to Arduino!")
        
        response = arduino.readline().decode('utf-8', errors='ignore').strip()
        print(f"Arduino says: {response}")
        
        with open(args.csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            
            header = next(csv_reader)
            print(f"CSV Header: {header}")
            
            try:
                timestamp_idx = header.index('timestamp')
                target_velocity_idx = header.index('target_velocity')
                current_velocity_idx = header.index('current_velocity')
                acceleration_idx = header.index('acceleration')
                print(f"Found all required columns in CSV file")
            except ValueError as e:
                print(f"Error: CSV must have columns: timestamp, target_velocity, current_velocity, acceleration")
                print(f"Found columns: {header}")
                return
            
            print("\nStarting data transmission...")
            print("-" * 60)
            row_count = 0
            
            for row in csv_reader:
                if len(row) <= max(timestamp_idx, target_velocity_idx, current_velocity_idx, acceleration_idx):
                    print(f"Skipping invalid row: {row}")
                    continue
                
                try:
                    timestamp = row[timestamp_idx]
                    target_velocity = float(row[target_velocity_idx])
                    current_velocity = float(row[current_velocity_id
                    command = f"{target_velocity},{current_velocity}\n"
                    arduino.write(command.encode())
                    
                    print(f"Row {row_count+1}: Target={target_velocity}, Current={current_velocity}")
                    
                    time.sleep(0.1)
                    if arduino.in_waiting > 0:
                        response = arduino.readline().decode('utf-8', errors='ignore').strip()
                        print(f"  → {response}")
                    
                    row_count += 1

                    time.sleep(args.interval)
                    
                except ValueError as e:
                    print(f"Error parsing row {row_count+1}: {e}")
                except Exception as e:
                    print(f"Error processing row {row_count+1}: {e}")
            
            print("-" * 60)
            print(f"Processed {row_count} rows from CSV file")
    
    except serial.SerialException as e:
        print(f"Serial error: {e}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'arduino' in locals():
            arduino.close()
            print("Serial connection closed")

if __name__ == "__main__":
    main()
