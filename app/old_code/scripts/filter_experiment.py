import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, iirnotch, lfilter, square, chirp

# --- 1. Define Helper Function & Your Class ---

def causal_filter(b, a, x, zi):
    """
    Wrapper for lfilter to handle state (zi).
    x: array of data (can be length 1 for real-time)
    zi: current state
    Returns: (y, zf)
    """
    y, zf = lfilter(b, a, x, zi=zi)
    return y, zf

class EMGFilterAndEstimator:
    def __init__(self, fs=500, hum_freq=50):
        # Store parameters
        self.fs = fs
        self.hum_freq = hum_freq

        # Design all filters based on current sampling rate
        self._design_filters()

        # (Kalman vars omitted for brevity as they aren't used in this specific signal test)

    def _design_filters(self):
        nyq = 0.5 * self.fs

        # Notch filters for hum and its harmonics (50, 100, 150, ...)
        self.notches = []
        if self.hum_freq is not None and self.hum_freq > 0:
            max_harm = int(nyq // self.hum_freq)
            for k in range(1, max_harm + 1):
                f_h = self.hum_freq * k
                if f_h >= nyq:
                    break
                # Design a narrow notch at f_h
                b_n, a_n = iirnotch(f_h / nyq, Q=5)
                zi_n = np.zeros(max(len(a_n), len(b_n)) - 1)
                self.notches.append({"b": b_n, "a": a_n, "zi": zi_n, "f": f_h})

        # Bandpass Filter (20-250 Hz for raw EMG - Causal)
        low_cut = 20 / nyq
        high_cut = min(250 / nyq, 0.999)
        self.b_band, self.a_band = butter(6, [low_cut, high_cut], btype='bandpass', output='ba')
        self.zi_band = np.zeros(max(len(self.a_band), len(self.b_band)) - 1)

        # Band-stop Filter (1.5-3.5 Hz)
        stop_low = 1.5 / nyq
        stop_high = 3.5 / nyq
        self.b_stop, self.a_stop = butter(1, [stop_low, stop_high], btype='bandstop', output='ba')
        self.zi_stop = np.zeros(max(len(self.a_stop), len(self.b_stop)) - 1)

        # Lowpass Filter for Envelope (4th order, 5 Hz cutoff - Causal)
        env_cut = min(5 / nyq, 0.499)
        self.b_env, self.a_env = butter(4, env_cut, btype='low', output='ba')
        self.zi_env = np.zeros(max(len(self.a_env), len(self.b_env)) - 1)

    def process_sample(self, raw_sample):
        # 1. Bandpass Filtering (20-250Hz) - DO THIS FIRST
        # Why? It removes DC offset and high-freq noise, giving the Notch a cleaner signal.
        band_out, self.zi_band = causal_filter(self.b_band, self.a_band, np.array([raw_sample]), self.zi_band)

        # 2. Hum Removal (Notch Filters)
        # Now the notch filters run on the bandpassed signal
        notch_signal = band_out # Pass the result from step 1 into here
        for notch in self.notches:
            notch_signal, zi_new = causal_filter(notch["b"], notch["a"], notch_signal, notch["zi"])
            notch["zi"] = zi_new
        
        # 3. Band-stop Filtering (Motion Artifacts)
        # (This remains after bandpass/notch, or could be merged with step 1 logic)
        stop_out, self.zi_stop = causal_filter(self.b_stop, self.a_stop, notch_signal, self.zi_stop)

        # 4. Rectification
        rectified = np.abs(stop_out)

        # 5. Lowpass Filtering for Envelope
        env_out, self.zi_env = causal_filter(self.b_env, self.a_env, rectified, self.zi_env)
        measurement = env_out[0]

        return stop_out[0], measurement

# --- 2. Simulation Setup ---

fs = 500
duration = 10.0 # seconds
t = np.linspace(0, duration, int(fs*duration), endpoint=False)

# Generate 50Hz Square Wave
raw_signal = square(2 * np.pi * 50.15 * t)*200 + 200 + chirp((2 * np.pi * 7 * t), 11, 1, 17)*0

# Initialize your class
processor = EMGFilterAndEstimator(fs=fs, hum_freq=50)

# Lists to store results
filtered_output = []
envelope_output = []

# --- 3. Run Loop (Sample by Sample) ---
print(f"Processing {len(raw_signal)} samples...")

for sample in raw_signal:
    filt_val, env_val = processor.process_sample(sample)
    filtered_output.append(filt_val)
    envelope_output.append(env_val)

# --- 4. Plotting ---

plt.figure(figsize=(15, 10))

# Subplot 1: Raw vs Filtered
plt.subplot(2, 1, 1)
plt.title("Effect of Comb Notch Filter on 50Hz Square Wave")
plt.plot(t[:5000], raw_signal[:5000], 'k', alpha=0.3, label="Raw 50Hz Square", linewidth=2)
plt.plot(t[:5000], filtered_output[:5000], 'r', label="Filtered Output")
plt.ylabel("Amplitude")
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 2: The Envelope
# plt.subplot(3, 1, 2)
# plt.title("Resulting EMG Envelope")
# plt.plot(t, envelope_output, 'g', linewidth=2)
# plt.ylabel("Envelope Amplitude")
# plt.grid(True, alpha=0.3)
# plt.text(0.02, max(envelope_output)*0.8, "Note: Envelope is near zero because signal is destroyed", bbox=dict(facecolor='white', alpha=0.8))

# Subplot 3: Frequency Spectrum Verification
plt.subplot(2, 1, 2)
plt.title("Frequency Spectrum (FFT)")
def get_fft(data, fs):
    mags = np.abs(np.fft.rfft(data))
    freqs = np.fft.rfftfreq(len(data), 1/fs)
    return freqs, mags

f_raw, m_raw = get_fft(raw_signal, fs)
f_filt, m_filt = get_fft(filtered_output, fs)

plt.plot(f_raw, m_raw, 'k', alpha=0.3, label="Raw Spectrum")
plt.plot(f_filt, m_filt, 'r', label="Filtered Spectrum")
plt.xlim(0, 250)
plt.xlabel("Frequency (Hz)")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()