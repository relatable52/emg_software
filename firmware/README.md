# EMG Firmware

Arduino-based firmware for EMG signal acquisition using an ATmega328P microcontroller.

## Hardware Requirements

- Arduino Nano or compatible board (ATmega328P)
- EMG sensor module
- Power supply
- USB cable for programming

## Development Setup

### Prerequisites

- PlatformIO IDE or VS Code with PlatformIO extension
- Arduino USB drivers

### Building and Uploading

1. Open this directory in PlatformIO
2. Connect your Arduino Nano board
3. Build the project:
   ```
   pio run
   ```
4. Upload to your board:
   ```
   pio run --target upload
   ```

## Configuration

The firmware is configured using `platformio.ini`:
- Platform: ATmega AVR
- Board: Arduino Nano (ATmega328P)
- Framework: Arduino

## Features

- Real-time EMG signal acquisition
- Serial communication protocol for data transmission
- Configurable sampling rate
- LED status indicators

## Pin Configuration

[Add your pin configuration details here]

## Serial Protocol

[Add your serial communication protocol details here]
