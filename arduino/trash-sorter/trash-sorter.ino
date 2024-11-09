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

void loop()
{
  Serial.println("Looping");
  for (int i = 1500; i >= 1; i--) {
    for (int phase = 0; phase <= 7; phase++) {
      stepper1.turnOn(phase);
      delayMicroseconds(t);
    }
  }
}
