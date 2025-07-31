#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <Stepper.h>

// === PCA9685 Setup ===
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x41); // I2C address

// === TB6612 DC Motor Pins 
#define AIN2 5
#define AIN1 6
#define BIN1 7
#define BIN2 8
#define PWMA 9
#define PWMB 10

// === Stepper Motor Pins
#define DIR_PIN 11
#define STEP_PIN 12

const int STEPS_PER_REVOLUTION = 200;
Stepper myStepper(STEPS_PER_REVOLUTION, STEP_PIN, DIR_PIN);

// === Servo Setup ===
int servo0Pos = 300; // Starting positions
int servo1Pos = 300;
const int SERVO_MIN = 150;
const int SERVO_MAX = 600;

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(60); 

  // DC Motor Setup
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMB, OUTPUT);

  // Stepper Setup
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();

    if (command == 'D') { // Servo 0 move right
      servo0Pos += 5;
      if (servo0Pos > SERVO_MAX) servo0Pos = SERVO_MAX;
      pwm.setPWM(0, 0, servo0Pos);

    } else if (command == 'A') { // Servo 0 move left
      servo0Pos -= 5;
      if (servo0Pos < SERVO_MIN) servo0Pos = SERVO_MIN;
      pwm.setPWM(0, 0, servo0Pos);

    } else if (command == 'W') { // Servo 1 move right
      servo1Pos += 5;
      if (servo1Pos > SERVO_MAX) servo1Pos = SERVO_MAX;
      pwm.setPWM(1, 0, servo1Pos);

    } else if (command == 'S') { // Servo 1 move left
      servo1Pos -= 5;
      if (servo1Pos < SERVO_MIN) servo1Pos = SERVO_MIN;
      pwm.setPWM(1, 0, servo1Pos);

    } else if (command == 'E') { // ENTER pressed: run DC motors and stepper
      // Run DC motors forward
      digitalWrite(AIN1, HIGH);
      digitalWrite(AIN2, LOW);
      analogWrite(PWMA, 255);  // Full speed

      digitalWrite(BIN1, HIGH);
      digitalWrite(BIN2, LOW);
      analogWrite(PWMB, 255);  // Full speed

      delay(2000);  // Run motors for 2 seconds

      // Stop DC motors
      analogWrite(PWMA, 0);
      analogWrite(PWMB, 0);

      // Move stepper motor 30 steps forward
      digitalWrite(DIR_PIN, HIGH); // Choose direction
      for (int i = 0; i < 30; i++) {
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(500); // Adjust speed as needed
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(500);
      }
    }
  }
}