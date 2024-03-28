// #include <EEPROM.h>

// Define the EEPROM address where the byte will be stored
// const int eepromAddress = 0;

const int pwmPin = 9; // PWM output pin
int dutyCycle = 0;

void setup() {
  pinMode(pwmPin, OUTPUT); // Set pin 9 as output
  Serial.begin(9600);
  // byte storedDutyCycle = EEPROM.read(eepromAddress);
  // Serial.print("Loaded value: ");
  // Serial.println(storedDutyCycle);
  // dutyCycle = storedDutyCycle;
}
void loop() {
  if (Serial.available() > 0) {
    String inputString = Serial.readStringUntil('\n'); // Read the incoming string until newline
    inputString.trim(); // Remove any leading/trailing whitespace
    if (inputString.length() > 0) {
      int inputValue = inputString.toInt(); // Convert the string to an integer
      if (inputValue >= 0 && inputValue <= 255) { // Ensure the value is within byte range
        byte newDutyCycle = (byte)inputValue; // Convert the integer to a byte
        // EEPROM.update(eepromAddress, newDutyCycle);
        dutyCycle = newDutyCycle;
        Serial.print("Stored value: ");
        Serial.println(newDutyCycle);
      } else {
        Serial.println("Input out of byte range. Please enter a number between 0 and 255.");
      }
    }
  }
  analogWrite(pwmPin, dutyCycle); // Set PWM duty cycle
  Serial.print(dutyCycle);
  delay(1000); // Delay for 1 second (adjust as needed)
}























