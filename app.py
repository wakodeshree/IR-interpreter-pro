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
    # Convert uploaded file to OpenCV image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert and threshold to find the line
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Extract peak coordinates
    # We look for the lowest Y value (strongest absorption) for every X
    height, width = thresh.shape
    y_coords = []
    for x in range(width):
        column = thresh[:, x]
        peaks_in_col = np.where(column > 0)[0]
        if len(peaks_in_col) > 0:
            y_coords.append(np.mean(peaks_in_col))
        else:
            y_coords.append(np.nan)
            
    # Interpolate missing values
    y_series = pd.Series(y_coords).interpolate().values
    
    # Peak finding
    # distance and prominence controlled by 'sensitivity'
    peaks, _ = find_peaks(y_series, distance=20, prominence=sensitivity)
    return y_series, peaks, width

# --- UI LAYOUT ---
st.title("🔬 Professional IR Spectrum Interpreter")
st.sidebar.header("Settings")

uploaded_file = st.sidebar.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'])
sensitivity = st.sidebar.slider("Peak Sensitivity", 5, 100, 30)

if uploaded_file:
    y_data, peaks, img_width = process_ir_image(uploaded_file, sensitivity)
    
    st.image(uploaded_file, caption="Original Spectrum", use_column_width=True)
    
    # Conversion Logic: 4000 to 400 cm-1
    results = []
    for p in peaks:
        # Linear map: x=0 -> 4000, x=width -> 400
        wavenumber = 4000 - (p * (3600 / img_width))
        
        # Identification Logic
        match = "Unknown / Fingerprint"
        for group, (low, high, desc) in IR_DATABASE.items():
            if low <= wavenumber <= high:
                match = f"{group} ({desc})"
                break
        
        results.append({"Wavenumber": round(wavenumber, 1), "Assignment": match})

    # Display Results
    st.subheader("Detected Functional Groups")
    df_results = pd.DataFrame(results)
    st.table(df_results)
    
    # Export CSV
    csv = df_results.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data as CSV", csv, "ir_analysis.csv", "text/csv")
else:
    st.info("Please upload an IR spectrum image to begin analysis.")
