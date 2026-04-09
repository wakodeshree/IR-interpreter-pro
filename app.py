import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re
import cv2

# --- 1. FULL CHEMICAL DATABASE ---
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

STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"],
    "Nitro Compound": ["Nitro (-NO2)"],
    "Amide": ["Amide C=O", "Amine/Amide N-H"]
}

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="PhD IR Smart-Guardian", layout="wide")
st.title("🔬 Official IR Interpretation Engine ")
st.markdown("---")
# --- IMAGE PREPROCESSING ---
def preprocess_image(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    return gray


# --- IMPROVED OCR EXTRACTION ---
def extract_numbers(ocr_res):
    numbers = []
    for (_, text, prob) in ocr_res:
        text = text.replace("I","1").replace("l","1").replace("O","0")
        matches = re.findall(r'\d{3,4}', text)
        for m in matches:
            try:
                val = float(m)
                if 400 <= val <= 4000:
                    numbers.append((val, prob))
            except:
                continue
    return numbers


# --- SMART PEAK MATCHING ---
def match_ir_peaks(numbers):
    peaks = []
    scale_markers = {4000,3500,3000,2500,2000,1500,1000,500,400}
    
    for val, prob in numbers:
        if int(val) in scale_markers:
            continue
        
        for grp, r in IR_DB.items():
            tolerance = 20 if val > 2000 else 15
            
            if (r[0]-tolerance) <= val <= (r[1]+tolerance):
                peaks.append({
                    "Sample ID": sample_id,
                    "Experimental Peak": val,
                    "Functional Group": grp,
                    "Literature Range": f"{r[0]}-{r[1]}",
                    "Confidence": round(prob,2)
                })
    return peaks

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("📝 Experiment")
    sample_id = st.text_input("Sample ID", "001")
    target_structure = st.selectbox("Structure Verification:", list(STRUCTURE_LOGIC.keys()))
    st.divider()
    st.info("Please Verify Manually too.")

# --- 4. IMAGE HANDLING ---
uploaded_file = st.file_uploader("Upload IR Spectrum (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption=f"Processing: {uploaded_file.name}", use_container_width=True)
    
    if st.button("🚀 Analyze Spectrum"):
    with st.spinner("Processing..."):

        processed_img = preprocess_image(img)

        reader = easyocr.Reader(['en'], gpu=False)  
        ocr_res = reader.readtext(processed_img, detail=1)
            
            # --- SMART GUARDIAN LOGIC ---
           numbers = extract_numbers(ocr_res)
            all_vals = [int(n[0]) for n in numbers]
            
            has_ir_axis = any(x in all_vals for x in [4000,3000,2000,1000])
            has_nmr_labels = any(word in all_text for word in ["ppm", "nmr", "shift"])
            
            if has_nmr_labels or (not has_ir_axis and max(all_nums, default=0) < 450):
                st.error("❌ **NON-IR GRAPH BLOCKED**")
                st.warning("The Guardian detected an NMR/Carbon scale. Please upload a valid IR spectrum.")
            else:
                # --- PEAK EXTRACTION ---
                peaks = match_ir_peaks(numbers)
                
                for (bbox, text, prob) in ocr_res:
                    clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                    try:
                        v = float(clean)
                        if int(v) in scale_markers: continue
                        
                        if 400 <= v <= 4000:
                            for grp, r in IR_DB.items():
                                if r[0]-15 <= v <= r[1]+15:
                                    peaks.append({
                                        "Sample ID": sample_id,
                                        "Experimental Peak": v, 
                                        "Functional Group": grp, 
                                        "Literature Range": f"{r[0]}-{r[1]}"
                                    })
                    except: continue

                if peaks:
                    full_df = pd.DataFrame(peaks).drop_duplicates(subset=["Experimental Peak"])
                    
                    req = STRUCTURE_LOGIC[target_structure]
                    if target_structure != "All Peaks (No Filter)":
                        display_df = full_df[full_df["Functional Group"].isin(req)]
                    else:
                        display_df = full_df

                    if not display_df.empty:
                        st.subheader(f"✅ IR Results: {sample_id}")
                        # STABLE TABLE (No background styling)
                        st.table(display_df.sort_values("Experimental Peak", ascending=False))
                        
                        csv = display_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download CSV", csv, f"{sample_id}.csv", "text/csv")
                    else:
                        st.error(f"Structure verification failed for {target_structure}.")
                else:
                    st.warning("No identifiable IR peaks detected.")
