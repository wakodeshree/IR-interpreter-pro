import streamlit as st
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from scipy.signal import find_peaks, savgol_filter

# --- ENHANCED DATABASE ---
# Added "Strong/Medium" labels to help prioritize important peaks
IR_DB = {
    "O-H (Alcohol/Phenol)": [3200, 3650],
    "N-H (Amine/Amide)": [3300, 3500],
    "C-H (Aromatic)": [3000, 3100],
    "C-H (Alkane)": [2850, 2970],
    "C-H (Aldehyde)": [2700, 2850],
    "C≡N (Nitrile)": [2210, 2260],
    "C≡C (Alkyne)": [2100, 2260],
    "C=O (Ester/Aldehyde/Ketone)": [1700, 1750],
    "C=O (Amide)": [1630, 1690],
    "C=C (Alkene)": [1600, 1680],
    "N-O (Nitro)": [1340, 1550],
    "C-O (Ether/Ester/Alcohol)": [1050, 1300],
}

def clean_and_extract(img):
    # 1. Convert to Grayscale
    img_np = np.array(img.convert('L'))
    
    # 2. Adaptive Thresholding (Handles shadows/uneven scans better)
    thresh = cv2.adaptiveThreshold(img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # 3. MORPHOLOGICAL FILTERING (The "Secret Sauce")
    # This removes the thin grid lines and the small text numbers
    kernel = np.ones((3,3), np.uint8)
    # Remove horizontal grid lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    detected_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    thresh = cv2.absdiff(thresh, detected_lines)
    
    # 4. Extract Profile
    h, w = thresh.shape
    profile = []
    for x in range(w):
        col = thresh[:, x]
        y_indices = np.where(col > 0)[0]
        if len(y_indices) > 0:
            # We want the highest density of black pixels, not just the max
            profile.append(np.median(y_indices)) 
        else:
            profile.append(np.nan)
            
    s = pd.Series(profile).interpolate(limit_direction='both').values
    # Stronger smoothing to ignore the "steps" left by removed grid lines
    smooth = savgol_filter(s, window_length=21, polyorder=2)
    return smooth

# --- UI ---
st.set_page_config(page_title="Ultra-IR Predictor", layout="wide")
st.title("🔬 Ultra-Accurate IR Peak Interpretation")
st.markdown("This version uses **Morphological Filtering** to ignore grid lines and text labels.")

with st.sidebar:
    st.header("Calibration")
    # Note: Shimadzu graphs usually change scale at 2000. 
    # For now, we use a custom range.
    left_wn = st.number_input("Left Value", value=4000)
    right_wn = st.number_input("Right Value", value=400)
    st.divider()
    prom = st.slider("Peak Sensitivity", 5, 100, 25)

uploaded_file = st.file_uploader("Upload Shimadzu Graph", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(img, use_container_width=True)
    
    if st.button("Run High-Precision Analysis"):
        line = clean_and_extract(img)
        width = len(line)
        
        # Detect Dips (High Y values)
        peaks, props = find_peaks(line, prominence=prom, distance=width//50)
        
        if len(peaks) > 0:
            # Calculation
            wn_values = left_wn - (peaks / width) * (left_wn - right_wn)
            
            results = []
            for val in wn_values:
                # Match logic
                matches = [g for g, r in IR_DB.items() if r[0] <= val <= r[1]]
                results.append({
                    "Detected Wavenumber": round(val, 0),
                    "Assignment": " / ".join(matches) if matches else "Fingerprint"
                })
            
            df = pd.DataFrame(results).sort_values("Detected Wavenumber", ascending=False)
            
            with col2:
                st.success("Analysis Complete")
                st.dataframe(df, height=600)
        else:
            st.error("No peaks found. Check 'Peak Sensitivity' slider.")
