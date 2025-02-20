import tkinter as tk
import time
import math
from tkinter import messagebox
from datetime import datetime

class MouseTracker:
    def __init__(self, root):
        self.root = root
        self.last_x = None
        self.last_y = None
        self.last_time = None
        self.data = []  # Each entry: (instantaneous speed, distance, dt)
        
        self.root.bind("<Motion>", self.on_motion)
        
        self.info_label = tk.Label(root, text="Move your mouse over this window to collect data.")
        self.info_label.pack(pady=10)
        
        self.results_button = tk.Button(root, text="Show Acceleration Profile", command=self.show_results)
        self.results_button.pack(pady=5)
        
        self.reset_button = tk.Button(root, text="Reset Data", command=self.reset_data)
        self.reset_button.pack(pady=5)
        
        # Set logging interval (in milliseconds). Default is 300000 ms = 5 minutes.
        self.log_interval = 300000  
        # Start periodic logging.
        self.log_profile()
        
    def on_motion(self, event):
        current_time = time.time()
        x, y = event.x, event.y
        
        if self.last_x is not None and self.last_time is not None:
            dx = x - self.last_x
            dy = y - self.last_y
            dt = current_time - self.last_time
            if dt > 0:
                distance = math.hypot(dx, dy)
                # Compute speed in pixels per second
                speed = distance / dt
                self.data.append((speed, distance, dt))
                
        self.last_x, self.last_y, self.last_time = x, y, current_time
        
    def reset_data(self):
        self.data = []
        messagebox.showinfo("Reset", "Data has been reset.")
        
    def compute_profile(self):
        if not self.data:
            return "No data collected yet."
        
        # Bin the speeds into 9 groups
        speeds = [entry[0] for entry in self.data]
        min_speed, max_speed = min(speeds), max(speeds)
        num_bins = 9
        bin_size = (max_speed - min_speed) / num_bins if max_speed != min_speed else 1
        bins = [[] for _ in range(num_bins)]
        for s, _, _ in self.data:
            bin_index = int((s - min_speed) / bin_size)
            if bin_index >= num_bins:
                bin_index = num_bins - 1
            bins[bin_index].append(s)
        
        mapping_points = []
        for i, bin_data in enumerate(bins):
            if bin_data:
                avg_speed = sum(bin_data) / len(bin_data)
                # Use the bin center as the representative input speed
                bin_center = min_speed + (i + 0.5) * bin_size
                mapping_points.append((bin_center, avg_speed))
                
        result_text = "Libinput Custom Acceleration Profile Points:\n"
        result_text += "(Input Speed (pixels/sec), Average Pointer Speed (pixels/sec))\n\n"
        for point in mapping_points:
            result_text += f"({point[0]:.2f}, {point[1]:.2f})\n"
            
        # Convert speeds from pixels/sec to device units/ms (divide by 1000)
        converted_points = [(inp/1000, out/1000) for inp, out in mapping_points]
        result_text += "\nConverted to device units per ms:\n"
        result_text += "(Input Speed (units/ms), Average Pointer Speed (units/ms))\n\n"
        for point in converted_points:
            result_text += f"({point[0]:.5f}, {point[1]:.5f})\n"
            
        # Calculate step size as the average difference between consecutive converted input speeds
        if len(converted_points) > 1:
            diffs = [converted_points[i+1][0] - converted_points[i][0] for i in range(len(converted_points)-1)]
            step_size = sum(diffs) / len(diffs)
        else:
            step_size = 1.0
        result_text += f"\nCalculated step size: {step_size:.5f} (device units/ms)\n"
        
        # Prepare suggested xinput commands (replace "Device Name" with your actual device)
        y_values = " ".join(f"{point[1]:.5f}" for point in converted_points)
        xinput_commands = "\n# Suggested xinput commands:\n"
        xinput_commands += f'xinput set-prop "Device Name" "libinput Accel Custom Motion Points" {y_values}\n'
        xinput_commands += f'xinput set-prop "Device Name" "libinput Accel Custom Motion Step" {step_size:.5f}\n'
        xinput_commands += 'xinput set-prop "Device Name" "libinput Accel Profile Enabled" 0 0 1\n'
        
        result_text += "\n" + xinput_commands
        
        return result_text
        
    def show_results(self):
        result_text = self.compute_profile()
        result_window = tk.Toplevel(self.root)
        result_window.title("Acceleration Profile Results")
        text_widget = tk.Text(result_window, wrap="word", width=80, height=30)
        text_widget.insert("1.0", result_text)
        text_widget.pack(padx=10, pady=10)
        text_widget.config(state="disabled")
        
    def log_profile(self):
        # Compute current profile and add a timestamp
        result_text = self.compute_profile()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"Timestamp: {timestamp}\n{result_text}\n{'-'*80}\n"
        with open("acceleration_profile_log.txt", "a") as logfile:
            logfile.write(log_entry)
        # Schedule next log entry after the specified interval
        self.root.after(self.log_interval, self.log_profile)

def main():
    root = tk.Tk()
    root.title("Mouse Tracker for Libinput Custom Acceleration Profile")
    app = MouseTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
