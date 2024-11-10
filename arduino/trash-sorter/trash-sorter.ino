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

void incrementPhase(int& x) {
  x = (x >= 7) ? 0 : (x + 1);
}

void decrementPhase(int& x) {
  x = (x <= 0) ? 7 : (x - 1);
}

const int kickTicks = 1000;
void doKick(int& setpoint, int& phase, bool& kicking, Stepper& stepper) {
  if (setpoint > 0) {
    setpoint--;
    decrementPhase(phase);
    stepper.turnOn(phase);
    if (setpoint == 0 && kicking) {
      setpoint = -kickTicks;
      kicking = false;
    }
  }
  else if (setpoint < 0) {
    setpoint++;
    incrementPhase(phase);
    stepper.turnOn(phase);
  }
  else {
    stepper.turnOff();
  }
}

Stepper stepper1(2, 3, 4, 5);
Stepper stepper2(6, 7, 8, 9);
Stepper stepper3(10, 11, 12, 13);

void setup()
{
  for (int pin = 2; pin <= 13; pin++) {
    pinMode(pin, OUTPUT);
  }
  stepper1.turnOff();
  stepper2.turnOff();
  stepper3.turnOff();
  Serial.begin(9600);
}

bool firstGateKicking = false;
int firstGateSetpoint = 0;
int firstGatePhase = 0;

bool secondGateKicking = false;
int secondGateSetpoint = 0;
int secondGatePhase = 0;

int stringDirection = 0;
int stringPhase = 0;

void loop()
{
  if (Serial.available() > 0) {
    int command = Serial.read();
    Serial.print("Got ");
    Serial.println((char)command);
    switch (command) {
      // stepper 1 adjustment
      case 'a':
        firstGateSetpoint += 100;
        break;
      case 'A':
        firstGateSetpoint -= 100;
        break;
      // stepper 2 adjustment
      case 'b':
        secondGateSetpoint += 100;
        break;
      case 'B':
        secondGateSetpoint -= 100;
        break;
      // TODO stepper 3 adjustment
      
      // TODO remove + and - and / and just include the string movement in the kick
      // (so the only commands will be manual control or a whole sort)

      case '0': // kick out into the first category
        firstGateKicking = true;
        firstGateSetpoint = kickTicks;
        break;
      case '1': // kick out into the second category
        secondGateKicking = true;
        secondGateSetpoint = kickTicks;
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

  doKick(firstGateSetpoint, firstGatePhase, firstGateKicking, stepper1);
  doKick(secondGateSetpoint, secondGatePhase, secondGateKicking, stepper2);

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
