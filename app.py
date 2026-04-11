import cv2
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter
import tkinter as tk
from tkinter import filedialog, messagebox

class IRInterpreterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IR Spectrum Analyzer - Calibration Pro")
        
        # Configuration Variables
        self.image_path = None
        self.processed_data = None
        
        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        btn_load = tk.Button(self.root, text="Load IR Spectrum Image", command=self.load_image)
        btn_load.pack(pady=20)

        self.status_label = tk.Label(self.root, text="No image loaded", fg="grey")
        self.status_label.pack()

    def load_image(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.tiff")])
        if self.image_path:
            self.status_label.config(text=f"Loaded: {self.image_path.split('/')[-1]}", fg="green")
            self.process_spectrum()

    def process_spectrum(self):
        # 1. Load and Grayscale
        img = cv2.imread(self.image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Thresholding to isolate the spectral line
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # 3. Extracting coordinates (Assuming spectrum is the darkest line)
        points = np.column_stack(np.where(thresh > 0))
        
        # Sort by X-axis and average Y for each X to handle line thickness
        df = pd.DataFrame(points, columns=['y', 'x'])
        spectrum_line = df.groupby('x')['y'].mean().reset_index()

        # 4. Smoothing (Savitzky-Golay Filter)
        y_smooth = savgol_filter(spectrum_line['y'], window_length=11, polyorder=3)
        
        # 5. Peak Detection (Inverting Y because IR peaks point down)
        peaks, _ = find_peaks(-y_smooth, prominence=10, distance=20)

        self.analyze_peaks(spectrum_line['x'].iloc[peaks].values)

    def analyze_peaks(self, peak_pixels):
        """
        Calibrates pixels to Wavenumbers (cm⁻¹) 
        Note: This uses a standard 4000-400 cm⁻¹ range logic.
        """
        # Placeholder for calibration logic (Width of graph / wavenumber range)
        # You can adjust these constants based on your specific Shimadzu chart dimensions
        results = []
        for p in peak_pixels:
            wavenumber = self.pixel_to_cm1(p)
            functional_group = self.lookup_group(wavenumber)
            results.append((round(wavenumber, 2), functional_group))

        self.display_results(results)

    def pixel_to_cm1(self, pixel_x):
        # Example linear mapping: 4000 cm-1 at x=0, 400 cm-1 at x=max_width
        # Adjust based on your UI's calibration slider
        return 4000 - (pixel_x * 3.6)

    def lookup_group(self, wn):
        if 3200 <= wn <= 3600: return "O-H Stretch (Alcohol/Phenol)"
        if 2850 <= wn <= 3000: return "C-H Stretch (Alkane)"
        if 1670 <= wn <= 1820: return "C=O Stretch (Carbonyl)"
        if 1600 <= wn <= 1680: return "C=C Stretch (Alkene)"
        return "Fingerprint Region / Other"

    def display_results(self, results):
        output = "\n".join([f"{wn} cm⁻¹: {grp}" for wn, grp in results])
        messagebox.showinfo("Interpretation Results", output)

if __name__ == "__main__":
    root = tk.Tk()
    app = IRInterpreterApp(root)
    root.mainloop()
