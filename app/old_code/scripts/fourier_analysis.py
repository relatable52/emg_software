"""Fourier / PSD analysis utility

Usage examples:
  python fourier_analysis.py --file data.csv --column sensor_1 --fs 1000 --method welch
  python fourier_analysis.py --file data.csv --column sensor_1 --fs 1000 --method fft --save psd.png

This script supports computing the power spectral density (PSD) using Welch's method
or a straight FFT, and plots the frequency distribution.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch, windows, detrend


def load_signal(csv_path: str, column: str | None = None, time_col: str | None = None):
    df = pd.read_csv(csv_path)

    # If a time column is provided, attempt to compute sampling frequency from it
    fs = None
    if time_col and time_col in df.columns:
        # compute median diff to be robust against jitter
        t = df[time_col].values
        dt = np.median(np.diff(t))
        if dt <= 0:
            raise ValueError("Non-increasing time column, can't infer sampling rate")
        fs = 1.0 / dt

    # Choose column: explicit column or the first numeric column (excluding time_col)
    if column is None:
        # pick first numeric column that's not the time column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if time_col in numeric_cols:
            numeric_cols.remove(time_col)
        if not numeric_cols:
            raise ValueError("No numeric data columns found in CSV")
        column = numeric_cols[0]

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in CSV")

    sig = df[column].astype(float).values
    return sig, fs


def compute_fft(signal: np.ndarray, fs: float, nfft: int | None = None, window: str = 'hann'):
    # Optionally apply a window
    if nfft is None:
        nfft = max(1, int(2 ** np.ceil(np.log2(len(signal)))))

    if window:
        win = windows.get_window(window, len(signal))
    else:
        win = np.ones(len(signal))

    sigw = (signal - np.mean(signal)) * win
    # rfft for real signals
    spec = np.fft.rfft(sigw, n=nfft)
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)
    psd = (np.abs(spec) ** 2) / (fs * np.sum(win ** 2))
    return freqs, psd


def compute_welch(signal: np.ndarray, fs: float, nperseg: int | None = None, window: str = 'hann'):
    if nperseg is None:
        # default to 1/8 of signal length but at least 256
        nperseg = max(256, len(signal) // 8)
    f, p = welch(signal - np.mean(signal), fs=fs, window=window, nperseg=nperseg)
    return f, p


def plot_spectrum(freqs: np.ndarray, psd: np.ndarray, title: str = 'Power Spectral Density', save: str | None = None, log: bool = True):
    plt.figure(figsize=(8, 4))
    if log:
        plt.semilogy(freqs, psd, lw=1)
    else:
        plt.plot(freqs, psd, lw=1)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('PSD')
    plt.title(title)
    plt.grid(True, which='both', ls='--', lw=0.5)
    plt.tight_layout()
    if save:
        plt.savefig(save)
        print(f"Saved plot to {save}")
    else:
        plt.show()


def main(argv=None):
    p = argparse.ArgumentParser(description='Compute Fourier / PSD from CSV data')
    p.add_argument('--file', '-f', required=True, help='Path to CSV file')
    p.add_argument('--column', '-c', help='Column name containing the signal (default: first numeric)')
    p.add_argument('--time-col', help='Optional time column (seconds) to infer sampling rate')
    p.add_argument('--fs', type=float, help='Sampling frequency in Hz (if not provided, inferred from time column)')
    p.add_argument('--method', choices=['welch', 'fft'], default='welch', help='PSD estimation method')
    p.add_argument('--nperseg', type=int, help='nperseg for Welch method')
    p.add_argument('--nfft', type=int, help='nfft for FFT method')
    p.add_argument('--window', default='hann', help='Window name to use (default: hann)')
    p.add_argument('--save', help='Save plot to file instead of showing')
    p.add_argument('--no-log', dest='log', action='store_false', help='Do not use log scale for PSD')

    args = p.parse_args(argv)
    csv = args.file

    sig, inferred_fs = load_signal(csv, column=args.column, time_col=args.time_col)

    fs = args.fs if args.fs else inferred_fs
    if fs is None:
        p.error('Sampling frequency not provided and could not be inferred from time column')

    if args.method == 'welch':
        f, pxx = compute_welch(sig, fs=fs, nperseg=args.nperseg, window=args.window)
        title = f'Welch PSD ({Path(csv).name} - {args.column or "<auto>"})'
        plot_spectrum(f, pxx, title=title, save=args.save, log=args.log)
    else:
        f, pxx = compute_fft(sig, fs=fs, nfft=args.nfft, window=args.window)
        title = f'FFT Power ({Path(csv).name} - {args.column or "<auto>"})'
        plot_spectrum(f, pxx, title=title, save=args.save, log=args.log)


if __name__ == '__main__':
    main()
