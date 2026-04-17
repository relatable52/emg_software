from matplotlib import pyplot as plt
import pandas as pd

def plot_emg_data(time, emg_signals, labels, ax, title=""):
    """
    Plots multiple EMG signals over time.

    Parameters:
    - time: array-like, time stamps for the EMG data
    - emg_signals: list of array-like, each containing EMG signal data
    - labels: list of strings, labels for each EMG signal
    - title: string, title of the plot
    """
    for signal, label in zip(emg_signals, labels):
        ax.plot(time, signal, label=label)
    
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

data_path = "emg_data.csv"
df = pd.read_csv(data_path)
time = df["time_stamp"] - df["time_stamp"].iloc[0]
emg_data = [df[f"sensor_{i}"].values for i in range(1, 9)]
fig, axs = plt.subplots(figsize=(12, 8), nrows=8, ncols=1)
fig.align_xlabels(axs)
for i in range(4):
    plot_emg_data(time, [emg_data[i]], [f"Sensor {i+1}"], axs[i], title=f"EMG Sensor {i+1}")

plt.tight_layout()
plt.show()