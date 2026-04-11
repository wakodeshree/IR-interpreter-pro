import streamlit as st
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from scipy.signal import find_peaks

# --- IR DATABASE ---
IR_DB = {
    # --- O-H ---
    "Alcohol O-H (free)": [3600, 3650],
    "Alcohol O-H (H-bonded)": [3200, 3550],
    "Carboxylic Acid O-H": [2500, 3300],

    # --- N-H ---
    "Primary Amine N-H": [3300, 3500],
    "Secondary Amine N-H": [3310, 3350],
    "Amide N-H": [3100, 3500],

    # --- C-H ---
    "Alkane C-H": [2850, 2960],
    "Aldehyde C-H": [2720, 2820],
    "Aromatic C-H": [3000, 3100],
    "Alkyne ≡C-H": [3250, 3350],

    # --- TRIPLE BOND ---
    "Nitrile C≡N": [2210, 2260],
    "Alkyne C≡C": [2100, 2260],

    # --- CARBONYL (VERY IMPORTANT REGION) ---
    "Acid Chloride C=O": [1780, 1815],
    "Anhydride C=O": [1740, 1800],
    "Ester C=O": [1735, 1750],
    "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1690],

    # --- DOUBLE BOND ---
    "Alkene C=C": [1620, 1680],
    "Aromatic C=C": [1450, 1600],

    # --- NITRO ---
    "NO2 asymmetric": [1520, 1550],
    "NO2 symmetric": [1340, 1380],

    # --- C-O ---
    "Alcohol C-O": [1000, 1260],
    "Ester C-O": [1050, 1300],
    "Ether C-O": [1050, 1150],

    # --- HALIDES ---
    "C-Cl": [600, 800],
    "C-Br": [500, 600],
    "C-I": [400, 500],

    # --- FINGERPRINT REGION ---
    "Aromatic substitution": [690, 900],
    "Out of plane bending": [650, 1000]
}

# --- PREPROCESS ---
def preprocess(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Edge detection (better than threshold)
    edges = cv2.Canny(gray, 50, 150)

    return edges

# --- EXTRACT CURVE PROFILE ---
def extract_profile(edges):
    h, w = edges.shape
    profile = []

    for x in range(w):
        col = edges[:, x]
        y = np.where(col > 0)[0]

        if len(y) > 0:
            profile.append(np.max(y))  # take bottom-most edge (IR dip)
        else:
            profile.append(np.nan)

    return np.array(profile)

# --- SMOOTH SIGNAL ---
def smooth_signal(signal):
    return pd.Series(signal).interpolate().rolling(15, min_periods=1).mean().values

# --- DETECT PEAKS ---
def detect_peaks(signal):
    inverted = np.max(signal) - signal
    peaks, _ = find_peaks(inverted, distance=30, prominence=5)
    return peaks

# --- MAP PIXELS TO CM⁻¹ ---
def map_to_wavenumber(peaks, width):
    return 4000 - (peaks / width) * (4000 - 500)

# --- MATCH GROUPS ---
def match_groups(values):
    results = []
    for v in values:
        for grp, r in IR_DB.items():
            if r[0] <= v <= r[1]:
                results.append((round(v,1), grp))
    return results

# --- STREAMLIT ---
st.set_page_config(layout="wide")
st.title("🔬 IR Peak Detector (Advanced Version)")

file = st.file_uploader("Upload IR Spectrum", type=["png","jpg","jpeg"])

if file:
    img = Image.open(file)
    st.image(img, use_container_width=True)

    if st.button("Analyze"):

        edges = preprocess(img)
        profile = extract_profile(edges)
        smooth = smooth_signal(profile)

        peaks = detect_peaks(smooth)
        wn = map_to_wavenumber(peaks, len(smooth))

        matches = match_groups(wn)

        if len(peaks) == 0:
            st.error("❌ No peaks detected. Try clearer crop.")
        else:
            st.success(f"✅ {len(peaks)} Peaks Detected")

            df = pd.DataFrame({
                "Wavenumber (cm⁻¹)": np.round(wn,1)
            })

            st.dataframe(df)

            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "peaks.csv")
