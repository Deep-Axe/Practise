#include <Servo.h>

#define SERVO_PIN 9

#define VELOCITY_HISTORY_SIZE 3
#define BUFFER_SIZE 64

Servo motorServo;
float currentVelocities[VELOCITY_HISTORY_SIZE] = {0.0, 0.0, 0.0};
int velocityIndex = 0;
float targetVelocity = 0.0;
float currentVelocity = 0.0;
char inputBuffer[BUFFER_SIZE];
int bufferIndex = 0;
bool newDataReady = false;

void setup() {
  // Initialize serial
  Serial.begin(115200);
  
  motorServo.attach(SERVO_PIN);
  motorServo.write(90);  
  delay(1000);
  
  Serial.println("Arduino ready to receive velocity data");
}

void loop() {
  while (Serial.available() > 0 && !newDataReady) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n') {
      inputBuffer[bufferIndex] = '\0'; // Null terminate the string
      newDataReady = true;
      bufferIndex = 0;
    } else if (bufferIndex < BUFFER_SIZE - 1) {
      inputBuffer[bufferIndex++] = inChar;
    }
  }
  
  if (newDataReady) {
    processCommand(inputBuffer);
    newDataReady = false;
  }
}

void processCommand(char* buffer) {
  char* targetStr = strtok(buffer, ",");
  char* currentStr = strtok(NULL, ",");
  
  if (targetStr != NULL && currentStr != NULL) {
    targetVelocity = atof(targetStr);
    currentVelocity = atof(currentStr);
    
    updateVelocityHistory(currentVelocity);
    
    float avgVelocity = calculateAverageVelocity();
    
    float ratio = 0;
    if (avgVelocity > 0) {
      ratio = targetVelocity / avgVelocity;
    }
    
    int servoAngle = calculateServoAngleFromRatio(ratio);
    
    motorServo.write(servoAngle);
    
    // Send feedback
    Serial.print("Avg Velocity: ");
    Serial.print(avgVelocity, 4);
    Serial.print(", Target: ");
    Serial.print(targetVelocity, 4);
    Serial.print(", Ratio: ");
    Serial.print(ratio, 4);
    Serial.print(", Angle: ");
    Serial.println(servoAngle);
  }
}

void updateVelocityHistory(float newVelocity) {
  // Add new velocity to rolling history
  currentVelocities[velocityIndex] = newVelocity;
  velocityIndex = (velocityIndex + 1) % VELOCITY_HISTORY_SIZE;
}

float calculateAverageVelocity() {
  float sum = 0.0;
  for (int i = 0; i < VELOCITY_HISTORY_SIZE; i++) {
    sum += currentVelocities[i];
  }
  return sum / VELOCITY_HISTORY_SIZE;
}

int calculateServoAngleFromRatio(float ratio) {
  if (ratio < 0.25) {
    return 180; // Less than 0.25 of average -> 180 degrees
  } else if (ratio < 0.5) {
    return 90;  // Between 0.25 and 0.5 -> 90 degrees
  } else if (ratio < 0.75) {
    return 45;  // Between 0.5 and 0.75 -> 45 degrees
  } else if (ratio < 1.0) {
    return 10;  // Between 0.75 and 1.0 -> 10 degrees
  } else {
    return 0;   // Greater than 1.0 -> 0 degrees
  }
}
