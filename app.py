import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re
import cv2

# --- IR DATABASE ---
IR_DB = {
    "Alcohol O-H": [3200, 3650], "Carboxylic Acid O-H": [2400, 3400],
    "Amine/Amide N-H": [3100, 3500], "Alkyne ≡C-H": [3250, 3350],
    "Aromatic/Alkene C-H": [3000, 3100], "Alkane C-H": [2850, 2970],
    "Aldehyde C-H (Fermi)": [2720, 2850], "Nitrile C≡N": [2240, 2260],
    "Alkyne C≡C": [2100, 2250], "Acid Chloride/Anhydride C=O": [1760, 1810],
    "Ester C=O": [1730, 1750], "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725], "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1680], "Alkene C=C": [1600, 1680],
    "Aromatic C=C": [1475, 1600], "Nitro (-NO2)": [1350, 1550],
    "C-O Stretch": [1000, 1300], "C-Cl (Halide)": [540, 785]
}

# --- IMAGE PREPROCESSING ---
def preprocess(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.equalizeHist(gray)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    return gray

# --- ROTATION HANDLING ---
def get_rotations(img):
    return [
        img,
        cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]

# --- OCR EXTRACTION ---
def extract_numbers(reader, images):
    nums = []
    
    for im in images:
        result = reader.readtext(im, detail=1, paragraph=False)
        
        for (_, text, prob) in result:
            text = text.replace("O","0").replace("I","1").replace("l","1")
            matches = re.findall(r'\d{3,4}', text)
            
            for m in matches:
                try:
                    val = float(m)
                    if 400 <= val <= 4000:
                        nums.append((val, prob))
                except:
                    pass
    
    return nums

# --- PEAK MATCHING ---
def match_peaks(nums):
    peaks = []
    
    for val, prob in nums:
        for grp, r in IR_DB.items():
            tol = 20 if val > 2000 else 15
            
            if r[0]-tol <= val <= r[1]+tol:
                peaks.append({
                    "Peak (cm⁻¹)": val,
                    "Group": grp,
                    "Range": f"{r[0]}-{r[1]}",
                    "Confidence": round(prob,2)
                })
    
    return peaks

# --- STREAMLIT ---
st.set_page_config(layout="wide")
st.title("🔬 IR Analyzer (Advanced OCR Engine)")

uploaded = st.file_uploader("Upload IR Spectrum", type=["png","jpg","jpeg"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, use_container_width=True)

    if st.button("Analyze Spectrum"):
        with st.spinner("Analyzing..."):

            processed = preprocess(img)
            rotations = get_rotations(processed)

            reader = easyocr.Reader(['en'], gpu=False)

            numbers = extract_numbers(reader, rotations)

            if len(numbers) == 0:
                st.error("❌ OCR failed. Try higher resolution image.")
            else:
                peaks = match_peaks(numbers)

                if len(peaks) == 0:
                    st.warning("⚠️ Numbers found but no IR match.")
                else:
                    df = pd.DataFrame(peaks).drop_duplicates()

                    st.success("✅ Peaks detected")
                    st.dataframe(df.sort_values("Peak (cm⁻¹)", ascending=False))

                    csv = df.to_csv(index=False).encode()
                    st.download_button("Download CSV", csv, "IR_results.csv")
