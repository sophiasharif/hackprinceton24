const int stepperDelayMicros = 1300;

struct Stepper {
  int pins[4];
  Stepper(int a, int b, int c, int d) {
    pins[0] = a;
    pins[1] = b;
    pins[2] = c;
    pins[3] = d;
  }

  // phase ranges from 0 to 7 and wraps around.
  void turnOn(int phase) {
    int pinOn = phase / 2;
    bool nextOn = (phase % 2) == 1;
    digitalWrite(pins[0], LOW);
    digitalWrite(pins[1], LOW);
    digitalWrite(pins[2], LOW);
    digitalWrite(pins[3], LOW);
    digitalWrite(pins[pinOn], HIGH);
    if (nextOn) {
      digitalWrite(pins[(pinOn + 1) % 4], HIGH);
    }
  }

  void turnOff() {
    digitalWrite(pins[0], HIGH);
    digitalWrite(pins[1], HIGH);
    digitalWrite(pins[2], HIGH);
    digitalWrite(pins[3], HIGH);
  }
};

Stepper stepper1(2, 3, 4, 5);
Stepper stepper2(6, 7, 8, 9);
Stepper stepper3(10, 11, 12, 13);

void setup()
{
  Serial.begin(9600);
  for (int pin = 2; pin <= 13; pin++) {
    pinMode(pin, OUTPUT);
  }
}

int firstGateZero = 0;
int firstGatePosition = 0;
int firstGateSetpoint = 0;

int secondGateZero = 0;
int secondGatePosition = 0;
int secondGateSetpoint = 0;

int stringDirection = 0;
int stringPhase = 0;

const int gateTicksForClosed = 1000;

void loop()
{
  if (Serial.available() > 0) {
    int command = Serial.read();
    Serial.print("Got ");
    Serial.println((char)command);
    switch (command) {
      // TODO commands for manual control of the gates

      case '0': // sort to the first category (first gate closed, second open)
        firstGateSetpoint = firstGateZero + gateTicksForClosed;
        secondGateSetpoint = secondGateZero;
        break;
      case '1': // sort to the second category (second gate closed, first open)
        firstGateSetpoint = firstGateZero;
        secondGateSetpoint = secondGateZero + gateTicksForClosed;
        break;
      case '2': // sort to the third category (both gates open)
        firstGateSetpoint = firstGateZero;
        secondGateSetpoint = secondGateZero;
        break;
      case '+': // let out the string
        stringDirection = 1;
        break;
      case '-': // pull in the string
        stringDirection = -1;
        break;
      case '/': // hold the string
        stringDirection = 0;
        break;
    }
  }

  if (firstGatePosition < firstGateSetpoint) {
    firstGatePosition++;
    stepper1.turnOn((8 + firstGatePosition % 8) % 8);
  }
  else if (firstGatePosition > firstGateSetpoint) {
    firstGatePosition--;
    stepper1.turnOn((8 + firstGatePosition % 8) % 8);
  }

  if (secondGatePosition < secondGateSetpoint) {
    secondGatePosition++;
    stepper2.turnOn((8 + secondGatePosition % 8) % 8);
  }
  else if (secondGatePosition > secondGateSetpoint) {
    secondGatePosition--;
    stepper2.turnOn((8 + secondGatePosition % 8) % 8);
  }

  if (stringDirection == 1) {
    stringPhase = (stringPhase == 7) ? 0 : (stringPhase + 1);
    stepper3.turnOn(stringPhase);
  }
  else if (stringDirection == -1) {
    stringPhase = (stringPhase == 0) ? 7 : (stringPhase - 1);
    stepper3.turnOn(stringPhase);
  }

  delayMicroseconds(stepperDelayMicros);
}
