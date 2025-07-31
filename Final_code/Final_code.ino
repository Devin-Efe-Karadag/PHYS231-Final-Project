#include <Servo.h>

// === DC Motor Pins (TB6612) ===
#define AIN2 2
#define AIN1 4
#define BIN1 7
#define BIN2 8
#define PWMA 3
#define PWMB 10

// === Stepper Motor Pins ===
#define DIR_PIN 11
#define STEP_PIN 12

// === Servo Setup ===
Servo servo0;
Servo servo1;
Servo servo2;
#define SERVO0_PIN 6
#define SERVO1_PIN 5
#define SERVO2_PIN 9

// Servo position variables and limits
int servo0Pos = 90; // Starting position (degrees) - changed to middle position
int servo1Pos = 65; // Starting position (degrees) - changed to middle position
int servo2Pos = 90; // Starting position (degrees) - changed to middle position
const int SERVO_MIN = 0;   // Minimum servo angle
const int SERVO_MAX = 180; // Maximum servo angle

// State variable to track if motors are stopped
bool isStopped = false;

// Variables for position reporting
unsigned long lastReportTime = 0;
const unsigned long REPORT_INTERVAL = 1000; // Report position every 1 second

void setup() {
  Serial.begin(9600);

  // Attach servos
  servo0.attach(SERVO0_PIN);
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  
  // Initialize servos to middle position
  servo0.write(servo0Pos);
  servo1.write(servo1Pos);
  servo2.write(servo2Pos);

  // Set up DC motor pins
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMB, OUTPUT);

  // Set up stepper motor pins
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);

  // Initialize motors to stopped state
  stopAllMotors();
  
  Serial.println("System initialized");
  Serial.println("Servo Positions - S0: 90°, S1: 65°, S2: 90°");
}

void stopAllMotors() {
  // Stop DC motors
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMA, 0);
  analogWrite(PWMB, 0);

  // Stop stepper motor
  digitalWrite(STEP_PIN, LOW);

  // Servos remain at current position (no write needed)
  Serial.println("Motors stopped");
}

// Function to report current servo positions
void reportServoPositions() {
  Serial.print("Servo Positions - S0: ");
  Serial.print(servo0Pos);
  Serial.print("°, S1: ");
  Serial.print(servo1Pos);
  Serial.print("°, S2: ");
  Serial.print(servo2Pos);
  Serial.println("°");
}

void loop() {
  // Regularly report servo positions
  unsigned long currentTime = millis();
  if (currentTime - lastReportTime >= REPORT_INTERVAL) {
    reportServoPositions();
    lastReportTime = currentTime;
  }
  
  if (Serial.available()) {
    char command = Serial.read();
    Serial.print("Received: ");
    Serial.println(command); // Debug command receipt

    if (command == 'Q') {
      isStopped = true;
      stopAllMotors();
      reportServoPositions(); // Report positions when stopped
      while (Serial.available()) Serial.read(); // Clear serial buffer
      return; // Exit loop to ensure no further processing
    } else {
      isStopped = false;
    }

    if (!isStopped) {
      if (command == 'D') { // Servo 0 move right
        servo0Pos -= 5;
        if (servo0Pos < SERVO_MIN) servo0Pos = SERVO_MIN;
        servo0.write(servo0Pos);
        Serial.print("Servo 0 right: ");
        Serial.println(servo0Pos);

      } else if (command == 'A') { // Servo 0 move left
        servo0Pos += 5;
        if (servo0Pos > SERVO_MAX) servo0Pos = SERVO_MAX;
        servo0.write(servo0Pos);
        Serial.print("Servo 0 left: ");
        Serial.println(servo0Pos);

      } else if (command == 'W') { // Servo 1 move right
        servo1Pos += 5;
        if (servo1Pos > SERVO_MAX) servo1Pos = SERVO_MAX;
        servo1.write(servo1Pos);
        Serial.print("Servo 1 right: ");
        Serial.println(servo1Pos);

      } else if (command == 'S') { // Servo 1 move left
        servo1Pos -= 5;
        if (servo1Pos < SERVO_MIN) servo1Pos = SERVO_MIN;
        servo1.write(servo1Pos);
        Serial.print("Servo 1 left: ");
        Serial.println(servo1Pos);

      } else if (command == 'E') { // Run DC motors and stepper
        // Report positions before starting sequence
        reportServoPositions();
        
        // Run DC motors forward
        digitalWrite(AIN1, HIGH);
        digitalWrite(AIN2, LOW);
        digitalWrite(BIN1, HIGH);
        digitalWrite(BIN2, LOW);
        analogWrite(PWMA, 220);
        analogWrite(PWMB, 220
        
        
        
        
        );
        Serial.println("DC motors running");

        // Run for 2 seconds, checking for 'Q' every 100ms
        unsigned long startTime = millis();
        while (millis() - startTime < 2000) {
          if (Serial.available() && Serial.read() == 'Q') {
            stopAllMotors();
            isStopped = true;
            Serial.println("Stopped during DC run");
            reportServoPositions();
            return;
          }
          delay(100); // Check every 100ms
        }

        // Stop DC motors
        stopAllMotors();

        // Delay 1 second, checking for 'Q'
        startTime = millis();
        while (millis() - startTime < 1000) {
          if (Serial.available() && Serial.read() == 'Q') {
            stopAllMotors();
            isStopped = true;
            Serial.println("Stopped during delay");
            reportServoPositions();
            return;
          }
          delay(100);
        }

        // Move stepper motor 20 steps forward
        digitalWrite(DIR_PIN, HIGH);
        for (int i = 0; i < 20; i++) {
          if (Serial.available() && Serial.read() == 'Q') {
            stopAllMotors();
            isStopped = true;
            Serial.println("Stopped during stepper");
            reportServoPositions();
            return;
          }
          digitalWrite(STEP_PIN, HIGH);
          delayMicroseconds(2000);
          digitalWrite(STEP_PIN, LOW);
          delayMicroseconds(2000);
        }
        Serial.println("Stepper completed");
        
        // Report positions after sequence completes
        reportServoPositions();
      } else if (command == 'P') { // Added command to manually request position report
        reportServoPositions();
      } else if (command >= '0' && command <= '9') { // Control servo2 with numbers 0-9
        // Map 0-9 to servo range in 18-degree increments (0° to 180°)
        int position = (command - '0') * 18;
        servo2Pos = position;
        servo2.write(servo2Pos);
        Serial.print("Servo 2 set to: ");
        Serial.println(servo2Pos);
      }
    }
  }
}