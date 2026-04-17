import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the data
# If you have a file, use: df = pd.read_csv('your_file.csv')
# For this example, we'll assume the data is in a DataFrame called 'df'
df = pd.read_csv('./data/2_legs/leftleg1.csv')

# 2. Create a figure with subplots (4 rows, 2 columns)
fig, axes = plt.subplots(4, 2, figsize=(14, 18), sharex=True)
axes = axes.flatten() # Flatten the 2D array of axes for easy iteration

# 3. Loop through sensors 1 to 8 and plot
for i in range(1, 9):
    ax = axes[i-1]
    raw_col = f'Raw_Sensor_{i}'
    filt_col = f'Filt_Sensor_{i}'
    
    # Plot Raw data
    ax.plot(df['Time'][:4000], df[raw_col][:4000], label='Raw')
    # Plot Filtered data
    ax.plot(df['Time'][:4000], df[filt_col][:4000], label='Filtered')
    
    ax.set_title(f'Sensor {i} Comparison')
    ax.set_ylabel('Sensor Value')
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.7)

# 4. Final formatting
axes[-1].set_xlabel('Time (s)')
axes[-2].set_xlabel('Time (s)')
plt.tight_layout()

# 5. Show or save the plot
plt.savefig('sensor_comparison.png')
plt.show()