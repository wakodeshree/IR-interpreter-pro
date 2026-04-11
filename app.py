import streamlit as st
import numpy as np
import cv2
from scipy.signal import find_peaks
import pandas as pd

# --- FUNCTIONAL GROUP DATABASE ---
IR_DATABASE = {
    "O-H (alcohol)": (3200, 3600, "Strong, Broad"),
    "O-H (carboxylic acid)": (2500, 3300, "Very Broad"),
    "N-H (amine)": (3300, 3500, "Medium"),
    "C-H (alkane)": (2850, 2970, "Medium to Strong"),
    "C-H (alkene)": (3010, 3095, "Medium"),
    "C-H (alkyne)": (3300, 3300, "Strong, Sharp"),
    "C=O (ester)": (1735, 1750, "Strong"),
    "C=O (ketone)": (1705, 1725, "Strong"),
    "C=O (aldehyde)": (1720, 1740, "Strong"),
    "C=C (alkene)": (1640, 1680, "Medium"),
    "C≡N (nitrile)": (2210, 2260, "Medium"),
    "C-O (ether)": (1050, 1150, "Strong")
}

def process_ir_image(uploaded_file, sensitivity):
    # --- FIXED LINE BELOW (Added np. prefix) ---
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert and threshold to find the line
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Extract peak coordinates
    height, width = thresh.shape
    y_coords = []
    for x in range(width):
        column = thresh[:, x]
        peaks_in_col = np.where(column > 0)[0]
        if len(peaks_in_col) > 0:
            y_coords.append(np.mean(peaks_in_col))
        else:
            y_coords.append(np.nan)
            
    # Interpolate missing values for a smooth curve
    y_series = pd.Series(y_coords).interpolate().values
    
    # Peak finding
    peaks, _ = find_peaks(y_series, distance=20, prominence=sensitivity)
    return y_series, peaks, width

# --- UI LAYOUT ---
st.set_page_config(page_title="IR Interpreter Pro", layout="wide")
st.title("🔬 Professional IR Spectrum Interpreter")

st.sidebar.header("Control Panel")
uploaded_file = st.sidebar.file_uploader("Upload IR Graph (JPEG/PNG)", type=['png', 'jpg', 'jpeg'])
sensitivity = st.sidebar.slider("Peak Detection Sensitivity", 5, 100, 30)

if uploaded_file:
    # Process the image
    y_data, peaks, img_width = process_ir_image(uploaded_file, sensitivity)
    
    # Display the spectrum image
    st.image(uploaded_file, caption="Uploaded Spectrum", use_container_width=True)
    
    # Analysis Logic
    results = []
    for p in peaks:
        # Scale: 4000 cm-1 to 400 cm-1 mapping
        wavenumber = 4000 - (p * (3600 / img_width))
        
        match = "Fingerprint Region / Unidentified"
        for group, (low, high, desc) in IR_DATABASE.items():
            if low <= wavenumber <= high:
                match = f"{group} [{desc}]"
                break
        
        results.append({"Wavenumber (cm⁻¹)": round(wavenumber, 1), "Possible Assignment": match})

    # Results Table
    st.subheader("Analysis Results")
    if results:
        df_results = pd.DataFrame(results)
        st.table(df_results)
        
        # Export Data
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis as CSV", csv, "ir_report.csv", "text/csv")
    else:
        st.warning("No significant peaks detected. Try lowering the sensitivity slider.")
else:
    st.info("Upload an IR spectrum image in the sidebar to start the interpretation.")
