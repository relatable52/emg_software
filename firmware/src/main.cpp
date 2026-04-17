#include <Arduino.h>

// --- Configuration ---
const int SENSOR_PINS[8] = {26, 36, 39, 34, 35, 32, 33, 25};

// --- Protocol Definitions ---
const uint8_t CMD_HEADER = 0xAA;
const uint8_t CMD_START  = 0x01;
const uint8_t CMD_STOP   = 0x02;

// The struct receiving data FROM the PC
struct __attribute__((packed)) CommandPacket {
    uint8_t header;       // Should be 0xAA
    uint8_t type;         // 0x01 = Start, 0x02 = Stop
    uint32_t sampleRate;  // e.g., 1000
    uint32_t durationMs;  // e.g., 10000 (0 for infinite)
};

// The struct sending data TO the PC
struct __attribute__((packed)) DataPacket {
    uint32_t timestamp;
    uint16_t values[8]; 
    uint16_t terminator;
};

// --- Globals ---
volatile bool triggerSample = false;  // Flag from Interrupt
bool isStreaming = false;             // State variable
unsigned long streamStartTime = 0;
uint32_t streamDuration = 0;

DataPacket txPacket;
hw_timer_t *timer = NULL;

// --- Interrupt ---
void IRAM_ATTR onTimer() {
    if (isStreaming) {
        triggerSample = true;
    }
}

// --- Forward Declarations ---
void handleIncomingSerial();
void startStreaming(uint32_t rate, uint32_t duration);
void stopStreaming();
void sendStopPacket(); // <--- NEW

void setup() {
    Serial.begin(921600);
    
    // Setup Pins
    for(int i=0; i<8; i++) pinMode(SENSOR_PINS[i], INPUT);
    
    // Setup Timer (Initialized but not running high freq yet)
    // ESP32 timer API varies by version, assuming v2.x here based on your snippet
    timer = timerBegin(0, 80, true); // 1 tick = 1us
    timerAttachInterrupt(timer, &onTimer, true);
    
    txPacket.terminator = 0xAAAA; 
}

void loop() {
    // 1. Check for incoming commands from PC
    handleIncomingSerial();

    // 2. Handle Data Streaming
    if (isStreaming && triggerSample) {
        triggerSample = false;
        
        // Check duration (if not infinite)
        if (streamDuration > 0 && (millis() - streamStartTime >= streamDuration)) {
            stopStreaming(); // This will now send the stop packet
            return;
        }

        // Capture & Send
        txPacket.timestamp = micros();
        for(int i=0; i<8; i++) {
            txPacket.values[i] = analogRead(SENSOR_PINS[i]);
        }
        Serial.write((uint8_t*)&txPacket, sizeof(txPacket));
    }
}

// --- Helper Logic ---

void handleIncomingSerial() {
    // We need at least the size of a command packet to proceed
    if (Serial.available() >= sizeof(CommandPacket)) {
        
        if (Serial.peek() != CMD_HEADER) {
            Serial.read(); // Discard garbage
            return;
        }

        CommandPacket cmd;
        Serial.readBytes((char*)&cmd, sizeof(cmd));

        if (cmd.type == CMD_START) {
            startStreaming(cmd.sampleRate, cmd.durationMs);
        } 
        else if (cmd.type == CMD_STOP) {
            stopStreaming();
        }
    }
}

void startStreaming(uint32_t rate, uint32_t duration) {
    if (rate == 0) rate = 1000; 
    
    uint64_t alarmVal = 1000000 / rate;
    
    timerAlarmDisable(timer);
    timerAlarmWrite(timer, alarmVal, true);
    timerAlarmEnable(timer);

    streamDuration = duration;
    streamStartTime = millis();
    isStreaming = true;
    
    // Optional: Reset buffer? 
    // Serial.flush() only flushes TX, not RX. 
    // To clear RX: while(Serial.available()) Serial.read();
}

// --- MODIFIED FUNCTION ---
void stopStreaming() {
    // Only send the packet if we were previously running
    // This prevents spamming stop packets if the user clicks Stop twice
    if (isStreaming) {
        sendStopPacket();
    }

    isStreaming = false;
    triggerSample = false;
    timerAlarmDisable(timer); 
}

// --- NEW FUNCTION ---
void sendStopPacket() {
    DataPacket stopPkg;
    
    // The "Magic" Timestamp that Python looks for
    stopPkg.timestamp = 0xFFFFFFFF; 
    
    // Fill sensors with 0
    memset(stopPkg.values, 0, sizeof(stopPkg.values));
    
    // Use the same terminator so Python's validation doesn't reject it
    stopPkg.terminator = 0xAAAA; 
    
    Serial.write((uint8_t*)&stopPkg, sizeof(stopPkg));
}