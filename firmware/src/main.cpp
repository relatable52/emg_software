#include <Arduino.h>

#define SENSOR_1 A0
#define SENSOR_2 A5

unsigned long interval = 1000;  // microseconds between samples (set dynamically)
unsigned long lastSampleTime = 0;
bool recording = false;
unsigned long recordStartMillis = 0;
unsigned long recordDurationMs = 0;

void setup() {
  Serial.begin(115200);
  while(!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }
  Serial.println("Serial Initialized");
}

void loop() {
  int sensorValue1 = 0;
  int sensorValue2 = 0;
  
  while (!recording) {
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      command.trim();

      if (command.startsWith("START")) {
        int firstComma = command.indexOf(',');
        int secondComma = command.indexOf(',', firstComma + 1);

        if (firstComma > 0 && secondComma > firstComma) {
          int sampleRate = command.substring(firstComma + 1, secondComma).toInt();
          int durationSec = command.substring(secondComma + 1).toInt();

          if (sampleRate > 0 && durationSec > 0) {
            interval = 1000000UL / sampleRate;
            recordDurationMs = (unsigned long)durationSec * 1000UL;
            recording = true;
            recordStartMillis = millis();

            Serial.print("RECORDING ");
            Serial.print(sampleRate);
            Serial.print("Hz for ");
            Serial.print(durationSec);
            Serial.println("s");
          } else {
            Serial.println("ERROR: Invalid parameters");
          }

          Serial.println("Reading Started");
        }
      }
    }
  }
  while (recording) {
    unsigned long currentMicros = micros();
    if (currentMicros - lastSampleTime >= interval) {
      lastSampleTime = currentMicros;

      sensorValue1 = analogRead(SENSOR_1);
      sensorValue2 = analogRead(SENSOR_2);

      Serial.print(currentMicros);
      Serial.print(",");
      Serial.print(sensorValue1);
      Serial.print(",");
      Serial.println(sensorValue2);

      if (millis() - recordStartMillis >= recordDurationMs) {
        recording = false;
        Serial.println("DONE");
      }
    }
  }
}