import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

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
st.set_page_config(page_title="PhD IR Smart-Guardian", layout="wide", page_icon="🔬")
st.title("🔬 PhD IR Interpretation Engine (Stable v5.1)")
st.markdown("---")

# --- 3. SIDEBAR UTILITIES ---
with st.sidebar:
    st.header("📝 Lab Notebook")
    sample_id = st.text_input("Sample ID", "Ref_Compound_001")
    target_structure = st.selectbox("Structure Verification:", list(STRUCTURE_LOGIC.keys()))
    
    st.divider()
    st.subheader("📲 Sharing & Mobile")
    st.info("To use as a FREE App: Open in phone browser and select 'Add to Home Screen'.")
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://ir-interpreter-pro.streamlit.app"
    st.image(qr_url)

# --- 4. IMAGE FILE HANDLING ---
uploaded_file = st.file_uploader("Upload IR Spectrum (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption=f"Processing: {uploaded_file.name}", use_container_width=True)
    
    if st.button("🚀 Analyze Spectrum"):
        with st.spinner("Machine Scanning & Validating..."):
            reader = easyocr.Reader(['en'])
            # OCR with rotation for vertical axis labels
            ocr_res = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            # --- SMART GUARDIAN LOGIC ---
            all_text = " ".join([x[1].lower() for x in ocr_res])
            all_nums = []
            for x in ocr_res:
                clean = "".join(re.findall(r'[0-9.]+', x[1]))
                try: all_nums.append(float(clean))
                except: continue
            
            # Validation Flags
            has_ir_axis = any(m in [int(n) for n in all_nums] for m in [4000, 3000, 2000, 1000])
            has_nmr_labels = any(word in all_text for word in ["ppm", "nmr", "shift", "h-nmr"])
            
            # Block if it's NMR or the scale is wrong
            if has_nmr_labels or (not has_ir_axis and max(all_nums, default=0) < 450):
                st.error("❌ **NON-IR GRAPH BLOCKED**")
                st.warning("The Guardian detected an NMR/Carbon scale (ppm). Please upload a valid IR spectrum (cm⁻¹).")
            else:
                # --- PEAK EXTRACTION ---
                peaks = []
                scale_markers = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 400]
                
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
                    
                    # Apply Structural Logic Filter
                    req = STRUCTURE_LOGIC[target_structure]
                    if target_structure != "All Peaks (No Filter)":
                        display_df = full_df[full_df["Functional Group"].isin(req)]
                    else:
                        display_df = full_df

                    if not display_df.empty:
                        st.subheader(f"✅ IR Results: {sample_id}")
                        st.dataframe(
                            display_df.style.background_gradient(cmap='Blues', subset=['Experimental Peak']),
                            use_container_width=True
                        )
                        
                        # Export
                        csv = display_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Research CSV", csv, f"{sample_id}_analysis.csv", "text/csv")
                        
                        # Pattern Match Success
                        found_set = set(display_df["Functional Group"].tolist())
                        missing = set(req) - found_set
                        if not missing and target_structure != "All Peaks (No Filter)":
                            st.success(f"🎯 Pattern Match! All expected peaks for {target_structure} were confirmed.")
                    else:
                        st.error(f"Structure verification failed: Expected {target_structure} peaks were not found.")
                else:
                    st.warning("Valid IR graph found, but no identifiable peaks match the chemical database.")
