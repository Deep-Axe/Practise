// Arduino Mega 2560 - Battery Precharge + AIR + Discharge Controller
// With full serial simulation (type commands in Serial Monitor @ 115200 baud)

#define PRECHARGE_INPUT_PIN   2
#define DISCHARGE_INPUT_PIN   3

#define PRECHARGE_RELAY_PIN   12 
#define AIR_PLUS_PIN          8 
#define AIR_MINUS_PIN         10
#define DISCHARGE_RELAY_PIN   7

const unsigned long PRECHARGE_TIME = 5000;

enum State {
  STATE_OFF,
  STATE_PRECHARGE,
  STATE_IDLE,
  STATE_FORCED_DISCHARGE
};

State currentState = STATE_OFF;
unsigned long prechargeStartTime = 0;

// Simulated inputs via serial
bool simPrecharge = false;
bool simDischarge = false;

void setup() {
  Serial.begin(115200);
  while (!Serial);  // Wait for serial monitor

  // Inputs
  pinMode(PRECHARGE_INPUT_PIN, INPUT_PULLUP);  // Most switches are active LOW
  pinMode(DISCHARGE_INPUT_PIN, INPUT_PULLUP);

  // Outputs
  pinMode(PRECHARGE_RELAY_PIN, OUTPUT);
  pinMode(AIR_PLUS_PIN,        OUTPUT);
  pinMode(AIR_MINUS_PIN,       OUTPUT);
  pinMode(DISCHARGE_RELAY_PIN, OUTPUT);

  // Start in safest state
  allRelaysSafeOff();
  currentState = STATE_OFF;

  Serial.println(F("\nArduino Mega Precharge + AIR + Discharge Controller"));
  Serial.println(F("Commands (send with Newline):"));
  Serial.println(F("  1     = Start precharge (simulate ON signal)"));
  Serial.println(F("  0     = Remove precharge signal"));
  Serial.println(F("  d     = Force discharge / emergency stop"));
  Serial.println(F("  s     = Show current status"));
  Serial.println(F("  r     = Reset to OFF"));
  Serial.println(F("Ready! Waiting for command...\n"));
}

void loop() {
  // // === Read serial simulation commands ===
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();

    if (cmd == "1") {
      simPrecharge = true;
      simDischarge = false;
      Serial.println(F("Simulated PRECHARGE REQUEST = ON"));
    }
    else if (cmd == "0") {
      simPrecharge = false;
      Serial.println(F("Simulated PRECHARGE REQUEST = OFF"));
    }
    else if (cmd == "d" || cmd == "2") {
      simDischarge = true;
      Serial.println(F("FORCED DISCHARGE COMMAND RECEIVED"));
    }
    else if (cmd == "s") {
      printStatus();
      return;
    }
    else if (cmd == "r") {
      simPrecharge = false;
      simDischarge = false;
      goToOff();
      Serial.println(F("System reset to OFF"));
      return;
    }
    else {
      Serial.println(F("Unknown command"));
    }
  }

  // === Read real hardware inputs ===
  bool hwPrecharge = (digitalRead(PRECHARGE_INPUT_PIN) == LOW);  // Active low
  bool hwDischarge = (digitalRead(DISCHARGE_INPUT_PIN) == LOW);

  bool prechargeRequested = simPrecharge || hwPrecharge;
  bool dischargeRequested = simDischarge || hwDischarge;

  // === Priority 1: Forced discharge wins everything ===
  if (dischargeRequested) {
    goToForcedDischarge();
    return;
  }

  // === Normal state machine ===
  switch (currentState) {
    case STATE_OFF:
      if (prechargeRequested) {
        startPrecharge();
      }
      break;

    case STATE_PRECHARGE:
      if (millis() - prechargeStartTime >= PRECHARGE_TIME) {
        goToIdle();
      }
      if (!prechargeRequested) {
        goToOff();
      }
      break;

    case STATE_IDLE:
      if (!prechargeRequested) {
        goToOff();  // Lost run signal → safe shutdown
      }
      break;

    case STATE_FORCED_DISCHARGE:
      // Stay here until power cycle or manual reset
      break;
  }

  delay(10);
}

// ========================================
// Relay Control Functions
// ========================================

void allRelaysSafeOff() {
  digitalWrite(PRECHARGE_RELAY_PIN, LOW);   // Open
  digitalWrite(AIR_PLUS_PIN,        LOW);   // Open
  digitalWrite(AIR_MINUS_PIN,       LOW);   // Open
  digitalWrite(DISCHARGE_RELAY_PIN, LOW);   // CLOSED (NC) → discharge active
}

void goToOff() {
  currentState = STATE_OFF;
  allRelaysSafeOff();
  // Precharge open, AIRs open, discharge CLOSED (active)
  Serial.println(F("STATE → OFF (discharge active, all contactors open)"));
}

void startPrecharge() {
  currentState = STATE_PRECHARGE;
  prechargeStartTime = millis();

  digitalWrite(PRECHARGE_RELAY_PIN, HIGH);  // Close precharge
  digitalWrite(AIR_PLUS_PIN,        LOW);   // AIR+ open
  digitalWrite(AIR_MINUS_PIN,       HIGH);   // AIR- open
  digitalWrite(DISCHARGE_RELAY_PIN, HIGH);   // Discharge closed (safe)

  Serial.println(F("STATE → PRECHARGE (5 sec timer started)"));
  Serial.println(F("   Precharge relay: CLOSED | AIR+/-: OPEN | Discharge: ACTIVE"));
}

void goToIdle() {
  currentState = STATE_IDLE;

  digitalWrite(PRECHARGE_RELAY_PIN, LOW);   // Open precharge
  digitalWrite(AIR_PLUS_PIN,       HIGH);  // Close main +
  digitalWrite(AIR_MINUS_PIN,      HIGH);  // Close main –
  digitalWrite(DISCHARGE_RELAY_PIN, HIGH);  // Still closed (NC)

  Serial.println(F("STATE → IDLE / RUNNING"));
  Serial.println(F("Precharge: OPEN | AIR+ & AIR-: CLOSED | Discharge: ACTIVE"));
}

void goToForcedDischarge() {
  if (currentState != STATE_FORCED_DISCHARGE) {
    currentState = STATE_FORCED_DISCHARGE;

    digitalWrite(PRECHARGE_RELAY_PIN, LOW);
    digitalWrite(AIR_PLUS_PIN,        LOW);
    digitalWrite(AIR_MINUS_PIN,       LOW);
    digitalWrite(DISCHARGE_RELAY_PIN, HIGH);  // OPEN the NC relay → active discharge!

    Serial.println(F("FORCED DISCHARGE! ALL CONTACTORS OPEN, DISCHARGE RELAY FORCED OPEN"));
  }
}

void printStatus() {
  Serial.println(F("\n========== CURRENT STATUS =========="));
  Serial.print(F("State: "));
  switch (currentState) {
    case STATE_OFF:              Serial.println(F("OFF (Safe)")); break;
    case STATE_PRECHARGE:        Serial.println(F("PRECHARGE")); break;
    case STATE_IDLE:             Serial.println(F("IDLE / RUNNING")); break;
    case STATE_FORCED_DISCHARGE: Serial.println(F("FORCED DISCHARGE")); break;
  }

  Serial.print(F("Precharge Relay : ")); Serial.println(digitalRead(PRECHARGE_RELAY_PIN) ? "CLOSED" : "OPEN");
  Serial.print(F("AIR+ (Main +)   : ")); Serial.println(digitalRead(AIR_PLUS_PIN) ? "CLOSED" : "OPEN");
  Serial.print(F("AIR- (Main –)   : ")); Serial.println(digitalRead(AIR_MINUS_PIN) ? "CLOSED" : "OPEN");
  Serial.print(F("Discharge Relay : ")); 
  if (digitalRead(DISCHARGE_RELAY_PIN)) Serial.println(F("OPEN → DISCHARGE ACTIVE!"));
  else Serial.println(F("CLOSED (normal, passive)"));

  if (currentState == STATE_PRECHARGE) {
    unsigned long elapsed = millis() - prechargeStartTime;
    unsigned long remaining = (elapsed < PRECHARGE_TIME) ? (PRECHARGE_TIME - elapsed) : 0;
    Serial.print(F("Precharge time left: "));
    Serial.print(remaining / 1000.0, 1);
    Serial.println(F(" seconds"));
  }
  Serial.println(F("===================================\n"));
}
