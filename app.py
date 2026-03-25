import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re
import io

# --- 1. THE COMPLETE IR DATABASE ---
IR_DB = {
    "Alcohol O-H": [3200, 3650],
    "Carboxylic Acid O-H": [2400, 3400],
    "Amine/Amide N-H": [3100, 3500],
    "Alkyne ≡C-H": [3250, 3350],
    "Aromatic/Alkene C-H": [3000, 3100],
    "Alkane C-H": [2850, 2970],
    "Aldehyde C-H (Fermi)": [2720, 2850],
    "Nitrile C≡N": [2240, 2260],
    "Alkyne C≡C": [2100, 2250],
    "Acid Chloride/Anhydride C=O": [1760, 1810],
    "Ester C=O": [1730, 1750],
    "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1680],
    "Alkene C=C": [1600, 1680],
    "Aromatic C=C": [1475, 1600],
    "Nitro (-NO2)": [1350, 1550],
    "C-O Stretch": [1000, 1300],
    "C-Cl (Halide)": [540, 785]
}

# --- 2. STRUCTURE -> REQUIRED GROUPS ---
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

# --- 3. PAGE CONFIG & UI ---
st.set_page_config(page_title="PhD IR Pro Interpreter", layout="wide")
st.title("🔬 Optimized PhD IR Interpretation Engine")
st.markdown("---")

with st.sidebar:
    st.header("📝 Sample Details")
    sample_id = st.text_input("Sample ID / Name:", "Sample_001")
    target_structure = st.selectbox("Select Structure to Verify:", list(STRUCTURE_LOGIC.keys()))
    
    st.divider()
    st.header("📲 Mobile App Instructions")
    st.info("To use this as a FREE app: Open in Chrome/Safari on your phone and select **'Add to Home Screen'**.")
    
    st.divider()
    st.subheader("🔗 Share Research")
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://ir-interpreter-pro.streamlit.app"
    st.image(qr_url, caption="Scan to open on mobile")

# --- 4. PROCESSING LOGIC ---
uploaded_file = st.file_uploader("Upload IR Graph (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Full Analysis"):
        with st.spinner("Validating spectrum and extracting peaks..."):
            reader = easyocr.Reader(['en'])
            # rotation_info handles vertical Shimadzu labels
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            raw_numbers = []
            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                if clean:
                    try: raw_numbers.append(float(clean))
                    except: continue

            # --- SMART VALIDATION ---
            if raw_numbers and max(raw_numbers) < 100:
                st.error("❌ **Wrong Graph Detected!** The values found (< 100) suggest an NMR or UV graph. Please upload an IR spectrum (400-4000 cm⁻¹).")
            else:
                peaks_found = []
                scale_ignore = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 400]
                
                for val in raw_numbers:
                    if int(val) in scale_ignore: continue
                    if 400 <= val <= 4000:
                        for group, r in IR_DB.items():
                            # 15 cm-1 buffer for experimental shift
                            if (r[0]-15) <= val <= (r[1]+15):
                                peaks_found.append({
                                    "Sample ID": sample_id,
                                    "Experimental Peak": val, 
                                    "Functional Group": group,
                                    "Literature Range": f"{r[0]} - {r[1]}"
                                })

                if peaks_found:
                    full_df = pd.DataFrame(peaks_found).drop_duplicates(subset=["Experimental Peak"])
                    req_groups = STRUCTURE_LOGIC[target_structure]
                    
                    if target_structure == "All Peaks (No Filter)":
                        display_df = full_df
                    else:
                        display_df = full_df[full_df["Functional Group"].isin(req_groups)]

                    st.subheader(f"✅ Results for: {target_structure}")
                    
                    if not display_df.empty:
                        final_df = display_df.sort_values("Experimental Peak", ascending=False)
                        st.table(final_df)
                        
                        # --- DOWNLOAD REPORT ---
                        csv = final_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Research CSV",
                            data=csv,
                            file_name=f"{sample_id}_IR_Analysis.csv",
                            mime="text/csv",
                        )
                        
                        # Structural Match Success Logic
                        found_set = set(display_df["Functional Group"].tolist())
                        missing = set(req_groups) - found_set
                        if not missing and target_structure != "All Peaks (No Filter)":
                            st.success(f"🎯 Structural Match! All expected peaks for {target_structure} were confirmed.")
                    else:
                        st.error(f"No peaks matching the {target_structure} pattern were detected.")
                else:
                    st.warning("No peaks detected. Ensure numerical labels are clearly visible on the spectrum.")
