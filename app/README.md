# EMG Analysis Application

Python application for processing and visualizing EMG signals acquired from the hardware component.

## Features

- Real-time EMG signal visualization
- Signal processing and analysis
- Data logging and export capabilities
- Wavelet analysis for signal decomposition

## Requirements

- Python 3.12 or higher
- uv

## Installation

### Setting up a Virtual Environment

1. Make sure you have Python 3.12 or higher installed

2. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   
1. Create a new virtual environment:
   ```bash
   uv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On Unix or MacOS:
     ```bash
     source .venv/bin/activate
     ```

3. Install the required packages:
   ```bash
   uv pip install .
   ```

## Usage

1. Connect the EMG hardware
2. Run the main application:
   ```bash
   python main.py
   ```

## Configuration

[Add configuration details here]

## Data Format

[Add information about data format and storage]

## Analysis Features

- Real-time signal visualization
- Signal filtering and processing
- Feature extraction
- Data export capabilities

## Troubleshooting

[Add common issues and solutions here]
