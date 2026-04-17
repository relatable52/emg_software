import cv2
import pandas as pd
import numpy as np

def create_multichannel_video(csv_path, video_path, output_path, window_seconds=5.0):
    # --- 1. Load Data ---
    print("Loading data...")
    df = pd.read_csv(csv_path)
    df['time_stamp'] = df['time_stamp'] - df['time_stamp'].iloc[0]
    
    # Columns to plot
    signal_cols = ['filtered_1', 'filtered_2', 'filtered_3', 'filtered_4']
    
    # Define a distinct color for each plot (BGR format)
    # Dark Blue, Dark Green, Dark Red, Dark Orange (for visibility on white)
    colors = [(139, 0, 0), (0, 100, 0), (0, 0, 139), (0, 140, 255)] 
    
    # Calculate global limits to keep scaling consistent
    # We assume EMG centers roughly around 0. Let's find the max absolute amplitude
    max_amp = df[signal_cols].abs().max().max()
    # Add 10% padding
    y_limit = max_amp * 1.1 
    y_min, y_max = -y_limit, y_limit

    # --- 2. Setup Video Input ---
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # --- 3. Setup Layout ---
    # Plot area width = same as video width
    plot_w = vid_w
    combined_w = vid_w + plot_w
    combined_h = vid_h
    
    # Height of one individual subplot
    subplot_h = int(vid_h / 4) 

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (combined_w, combined_h))
    
    print(f"Output Resolution: {combined_w}x{combined_h}")
    print(f"Subplot Height: {subplot_h}px")

    # --- 4. Processing Loop ---
    frame_idx = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = frame_idx / fps
        
        # --- Create the Plot Canvas (White Background) ---
        # Initialize with 255 (White)
        plot_img = np.full((combined_h, plot_w, 3), 255, dtype=np.uint8)
        
        # Data Window Logic
        start_time = current_time - window_seconds
        end_time = current_time
        
        # Fast boolean masking
        mask = (df['time_stamp'] >= start_time) & (df['time_stamp'] <= end_time)
        window_data = df.loc[mask]
        
        if not window_data.empty:
            # X-Coordinates are shared across all 4 plots
            # Normalize time to [0, plot_w]
            t_rel = window_data['time_stamp'].values - start_time
            x_coords = (t_rel / window_seconds * plot_w).astype(int)
            
            # --- Iterate over the 4 Sensors ---
            for i, col in enumerate(signal_cols):
                # Calculate the vertical space for this specific subplot
                # Top pixel of this subplot
                plot_top = i * subplot_h 
                # Bottom pixel of this subplot
                plot_bottom = (i + 1) * subplot_h 
                
                # Draw Background Elements for this subplot
                # 1. Gray Zero-Line (Baseline)
                mid_y = plot_top + (subplot_h // 2)
                cv2.line(plot_img, (0, mid_y), (plot_w, mid_y), (220, 220, 220), 1)
                # 2. Black bottom border
                cv2.line(plot_img, (0, plot_bottom-1), (plot_w, plot_bottom-1), (0, 0, 0), 2)
                # 3. Label
                cv2.putText(plot_img, f"Sensor {i+1}", (10, plot_top + 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)

                # Process Signal Data
                vals = window_data[col].values
                
                # Normalize Y: Map [-limit, +limit] to [plot_bottom, plot_top]
                # Formula: (val - min) / (max - min)
                norm_vals = (vals - y_min) / (y_max - y_min)
                
                # Invert because Image Y increases downwards
                # We map 0.0 to plot_bottom and 1.0 to plot_top
                y_rel = (1 - norm_vals) * subplot_h
                
                # Add the offset of the current subplot
                y_coords = (y_rel + plot_top).astype(int)
                
                # Draw Signal
                points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
                cv2.polylines(plot_img, [points], isClosed=False, color=colors[i], thickness=2)

        # Draw a vertical red "Time Cursor" at the right edge
        cv2.line(plot_img, (plot_w-1, 0), (plot_w-1, combined_h), (0, 0, 255), 2)
        
        # --- Combine Side-by-Side ---
        combined_frame = np.hstack((frame, plot_img))
        out.write(combined_frame)
        
        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx}/{total_frames} frames...")

    cap.release()
    out.release()
    print("Done.")

# --- Usage ---

for i in range(1, 11):
    print(f'leg_data_{i}.csv', 'leg_{i}.mp4', 'output_stacked_{i}.mp4')
    create_multichannel_video(f'leg_data_{i}.csv', f'leg_{i}.mp4', f'output_stacked_{i}.mp4')