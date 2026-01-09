import numpy as np
from scipy.signal import butter, iirnotch, lfilter

class EMGFilterAndEstimator:
    """
    Stateful Digital Signal Processing service for EMG signals.
    Handles real-time filtering (Bandpass + Notch) sample-by-sample.
    """
    def __init__(self, fs=500, hum_freq=50):
        self.fs = fs
        self.hum_freq = hum_freq
        
        # Initialize filter states
        self.notches = []
        self.b_band = None
        self.a_band = None
        self.zi_band = None
        
        # Design the filters immediately
        self._design_filters()

    def _design_filters(self):
        """
        Calculates filter coefficients (b, a) and initial states (zi)
        based on the current sampling rate.
        """
        if self.fs <= 0:
            return

        nyq = 0.5 * self.fs
        
        # 1. Notch Filters (Remove 50Hz/60Hz and harmonics)
        # We design a notch for every harmonic up to the Nyquist limit.
        self.notches = []
        if self.hum_freq and self.hum_freq > 0:
            # E.g., if fs=500, Nyq=250. Harmonics: 50, 100, 150, 200.
            max_harm = int(nyq // self.hum_freq)
            
            for k in range(1, max_harm + 1):
                f_h = self.hum_freq * k
                
                # Safety: Ensure we don't design a filter exactly AT or ABOVE Nyquist
                if f_h >= nyq - 1: 
                    break
                
                # Quality factor Q=30 is standard for power line removal
                b, a = iirnotch(f_h / nyq, Q=30)
                
                # 'zi' is the internal memory of the filter (Delay line)
                zi = np.zeros(max(len(a), len(b)) - 1)
                
                self.notches.append({
                    "b": b, 
                    "a": a, 
                    "zi": zi
                })

        # 2. Bandpass Filter (20Hz - 500Hz)
        # Standard EMG range to remove motion artifacts (<20Hz) and high freq noise (>500Hz)
        low_cut = 20.0
        high_cut = 500.0
        
        # Adjust high cut if fs is too low
        if high_cut >= nyq:
            high_cut = nyq - 1.0  # Cap just below Nyquist

        # Normalize frequencies
        low = low_cut / nyq
        high = high_cut / nyq
        
        # Safety check for valid butterworth design
        if low <= 0 or high <= 0 or low >= high:
            # Fallback for very low fs (shouldn't happen in production)
            self.b_band, self.a_band = [1.0], [1.0]
        else:
            self.b_band, self.a_band = butter(2, [low, high], btype='bandpass')

        # Initialize bandpass state
        self.zi_band = np.zeros(max(len(self.a_band), len(self.b_band)) - 1)

    def process_sample(self, raw_val: float) -> float:
        """
        Takes a single raw integer/float, applies filters, and returns a single float.
        Updates internal state automatically.
        """
        # Convert to numpy array for scipy input
        # Note: We process 1 sample, so input array shape is (1,)
        signal = np.array([raw_val])

        # 1. Apply Notch Filters (Cascade)
        for notch in self.notches:
            # lfilter returns (filtered_signal, new_state)
            signal, notch["zi"] = lfilter(notch["b"], notch["a"], signal, zi=notch["zi"])

        # 2. Apply Bandpass Filter
        signal, self.zi_band = lfilter(self.b_band, self.a_band, signal, zi=self.zi_band)

        # Return the scalar value
        return float(signal[0])

    def update_fs(self, new_fs: int):
        """
        Re-designs filters when the sampling rate changes.
        Resets the filter states (clears history).
        """
        if new_fs != self.fs:
            self.fs = new_fs
            self._design_filters()