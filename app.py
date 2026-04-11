import streamlit as st
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from scipy.signal import find_peaks, savgol_filter

# --- IR DATABASE ---
IR_DB = {
    "Alcohol O-H (free)": [3600, 3650],
    "Alcohol O-H (H-bonded)": [3200, 3550],
    "Carboxylic Acid O-H": [2500, 3300],
    "Primary Amine N-H": [3300, 3500],
    "Secondary Amine N-H": [3310, 3350],
    "Amide N-H": [3100, 3500],
    "Alkane C-H": [2850, 2960],
    "Aldehyde C-H": [2720, 2820],
    "Aromatic C-H": [3000, 3100],
    "Alkyne ≡C-H": [3250, 3350],
    "Nitrile C≡N": [2210, 2260],
    "Alkyne C≡C": [2100, 2260],
    "Acid Chloride C=O": [1780, 1815],
    "Anhydride C=O": [1740, 1800],
    "Ester C=O": [1735, 1750],
    "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1690],
    "Alkene C=C": [1620, 1680],
    "Aromatic C=C": [1450, 1600],
    "NO2 asymmetric": [1520, 1550],
    "NO2 symmetric": [1340, 1380],
    "Alcohol C-O": [1000, 1260],
    "Ester C-O": [1050, 1300],
    "Ether C-O": [1050, 1150],
    "C-Cl": [600, 800],
}

# --- IMAGE PROCESSING ---
def get_spectrum_line(img):
    img_np = np.array(img.convert('L'))
    # Threshold to find the black line
    _, thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY_INV)
    
    h, w = thresh.shape
    profile = []
    for x in range(w):
        col = thresh[:, x]
        y_indices = np.where(col > 0)[0]
        if len(y_indices) > 0:
            profile.append(np.max(y_indices)) # Bottom-most pixel (the peak dip)
        else:
            profile.append(np.nan)
    
    # Clean up signal
    s = pd.Series(profile).interpolate(limit_direction='both').values
    # Smooth with Savgol filter to maintain peak integrity
    smooth = savgol_filter(s, window_length=11, polyorder=3)
    return smooth

def match_functional_groups(wavenumber):
    matches = []
    for group, rng in IR_DB.items():
        if rng[0] <= wavenumber <= rng[1]:
            matches.append(group)
    return " / ".join(matches) if matches else "Fingerprint/Unknown"

# --- UI SETUP ---
st.set_page_config(page_title="IR Interpret Pro", layout="wide")
st.title("🔬 Advanced IR Spectrum Peak Interpreter")

with st.sidebar:
    st.header("Calibration")
    start_wn = st.number_input("Left Axis (cm⁻¹)", value=4000)
    end_wn = st.number_input("Right Axis (cm⁻¹)", value=400)
    st.divider()
    sensitivity = st.slider("Peak Sensitivity (Prominence)", 1, 100, 20)

uploaded_file = st.file_uploader("Upload an IR Spectrum Image (Crop to the chart area for best results)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Spectrum", use_container_width=True)
    
    if st.button("Analyze Spectrum"):
        with st.spinner("Analyzing peaks..."):
            try:
                line = get_spectrum_line(img)
                width = len(line)
                
                # Peaks in IR are "dips" - in image coordinates, dips have higher Y values
                peaks, props = find_peaks(line, prominence=sensitivity, distance=20)
                
                if len(peaks) > 0:
                    # Map pixels to wavenumbers
                    # Formula: Start - (percentage across image * range)
                    wn_values = start_wn - (peaks / width) * (start_wn - end_wn)
                    
                    results = []
                    for val in wn_values:
                        results.append({
                            "Wavenumber (cm⁻¹)": round(val, 1),
                            "Possible Interpretation": match_functional_groups(val)
                        })
                    
                    df = pd.DataFrame(results).sort_values("Wavenumber (cm⁻¹)", ascending=False)
                    
                    st.success(f"Detected {len(peaks)} significant peaks.")
                    st.table(df)
                    
                    # Download section
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Analysis (CSV)", csv, "ir_analysis.csv", "text/csv")
                else:
                    st.warning("No peaks detected. Try adjusting the sensitivity slider in the sidebar.")
            
            except Exception as e:
                st.error(f"Error processing image: {e}")
