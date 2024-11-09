const int t = 1000;

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
    digitalWrite(pins[0], HIGH);
    digitalWrite(pins[1], HIGH);
    digitalWrite(pins[2], HIGH);
    digitalWrite(pins[3], HIGH);
    digitalWrite(pins[pinOn], LOW);
    if (nextOn) {
      digitalWrite(pins[(pinOn + 1) % 4], LOW);
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

void setup()
{
  Serial.begin(9600);
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
}

int firstGateZero = 0;
int secondGateZero = 0;

int firstGateSetpoint = 0;
int secondGateSetpoint = 0;

int stringDirection = 0;

const int gateTicksForClosed = 10;

void loop()
{
  if (Serial.available() > 0) {
    int command = Serial.read();
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
  Serial.println("Looping");
  for (int i = 1500; i >= 1; i--) {
    for (int phase = 0; phase <= 7; phase++) {
      stepper1.turnOn(phase);
      delayMicroseconds(t);
    }
  }
}
