#include <Arduino.h>

#define RXD2 16   // ESP32 RX pin (connect to Drive TX pin 3)
#define TXD2 17   // ESP32 TX pin (connect to Drive RX pin 2)

byte slaveID = 1;   // Default Slave ID (can be 1–7 depending on jumper)

byte calcLRC(const String &payload) {
  byte lrc = 0;
  for (int i = 0; i < payload.length(); i += 2) {
    char hexByte[3] = {payload[i], payload[i+1], '\0'};
    lrc += strtol(hexByte, NULL, 16);
  }
  lrc = ((~lrc) + 1) & 0xFF;
  return lrc;
}

/// Send a Modbus ASCII command
void sendModbusASCII(String payload) {
  byte lrc = calcLRC(payload);
  Serial2.print(":");              // Start
  Serial2.print(payload);          // Payload
  if (lrc < 0x10) Serial2.print("0");
  Serial2.print(String(lrc, HEX)); // Append LRC
  Serial2.print("\r\n");           // End
}

/// Write single register (function 06)
void writeRegister(uint16_t reg, uint16_t value) {

  char buffer[20];
  sprintf(buffer, "%02X06%04X%04X", slaveID, reg, value);
  sendModbusASCII(String(buffer));
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  delay(2000);
  Serial.println("ESP32 BLDC Control via Modbus ASCII");

  writeRegister(6, 40);

  writeRegister(2, 0x0101);

}

void loop() {
  delay(5000);

  // CCW direction
  writeRegister(2, 0x0109);
  Serial.println("Motor running CCW...");

  delay(5000);

  writeRegister(2, 0x0101);
  Serial.println("Motor running CW...");
}
