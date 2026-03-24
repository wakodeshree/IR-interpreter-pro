import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE COMPLETE IR DATABASE (WITH RANGES) ---
IR_DB = {
    # C-H Region
    "Alkane C-H (stretch)": [2850, 3000, "Strong"],
    "Alkene =C-H (stretch)": [3000, 3100, "Medium"],
    "Aromatic C-H (stretch)": [3010, 3050, "Medium"],
    "Alkyne ≡C-H (stretch)": [3250, 3350, "Strong/Sharp"],
    "Aldehyde (C-H stretch)": [2800, 2900, "Weak/2 peaks"],
    
    # Multiple Bonds
    "Alkene (C=C)": [1600, 1680, "Medium"],
    "Aromatic (C=C)": [1475, 1600, "Medium/Weak"],
    "Alkyne (C≡C)": [2100, 2250, "Medium/Weak"],
    "Nitrile (C≡N)": [2240, 2260, "Medium/Sharp"],

    # Carbonyls (The 1700 Region)
    "Aldehyde C=O": [1720, 1740, "Strong"],
    "Ketone C=O": [1705, 1725, "Strong"],
    "Carboxylic acid C=O": [1700, 1725, "Strong"],
    "Ester C=O": [1730, 1750, "Strong"],
    "Amide C=O": [1630, 1680, "Strong"],
    "Anhydride/Acid Chloride": [1760, 1810, "Strong"],

    # O-H / N-H Region
    "Alcohol O-H (free)": [3600, 3650, "Sharp"],
    "Alcohol O-H (H-bonded)": [3200, 3400, "Strong/Broad"],
    "Carboxylic acid O-H": [2400, 3400, "Very Broad"],
    "Amine/Amide N-H": [3100, 3500, "Medium"],
    
    # Fingerprint/Single Bonds
    "Nitro (-NO2)": [1350, 1550, "Strong"],
    "C-O (Alcohol/Ether/Ester)": [1000, 1300, "Strong"],
    "C-F (Halide)": [1000, 1400, "Strong"],
    "C-Cl (Halide)": [540, 785, "Strong"]
}

# --- 2. STRUCTURE -> REQUIRED GROUPS ---
STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"]
}

st.set_page_config(page_title="IR Interpreter", layout="wide")
st.title("🔬IR Interpreter Engine")

target_structure = st.selectbox("Select Structure to Verify:", list(STRUCTURE_LOGIC.keys()))
uploaded_file = st.file_uploader("Upload IR Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Analysis"):
        with st.spinner("Extracting peaks..."):
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            peaks_found = []
            scale_ignore = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500]
            
            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                try:
                    val = float(clean)
                    if int(val) in scale_ignore: continue
                    
                    if 400 <= val <= 4000:
                        for group, r in IR_DB.items():
                            # 15 cm-1 buffer for experimental shift
                            if (r[0]-15) <= val <= (r[1]+15):
                                peaks_found.append({
                                    "Experimental Peak": val, 
                                    "Functional Group": group,
                                    "Literature Range": f"{r[0]} - {r[1]}"  # Added Range back
                                })
                except: continue

            if peaks_found:
                full_df = pd.DataFrame(peaks_found).drop_duplicates(subset=["Experimental Peak"])
                req_groups = STRUCTURE_LOGIC[target_structure]
                
                if target_structure == "All Peaks (No Filter)":
                    display_df = full_df
                else:
                    display_df = full_df[full_df["Functional Group"].isin(req_groups)]

                st.subheader(f"📊 Results for: {target_structure}")
                if not display_df.empty:
                    # Display table with the Range column
                    st.table(display_df.sort_values("Experimental Peak", ascending=False))
                    
                    # Logic Check
                    found_set = set(display_df["Functional Group"].tolist())
                    missing = set(req_groups) - found_set
                    if not missing and target_structure != "All Peaks (No Filter)":
                        st.success(f"🎯 Structural Match! All expected peaks for {target_structure} were detected.")
                else:
                    st.error(f"No peaks matching the {target_structure} pattern were found.")
            else:
                st.warning("No peaks detected. Ensure the numerical labels are clear.")
                # --- DOWNLOAD SECTION ---
                st.divider()
                st.subheader("📥 Export Analysis")
                
                # Convert the displayed results to CSV
                csv = display_df.to_csv(index=False).encode('utf-8')
                
                # Create the Download Button
                st.download_button(
                    label="Download Report as CSV",
                    data=csv,
                    file_name=f"IR_Analysis_{target_structure.replace(' ', '_')}.csv",
                    mime="text/csv",
                )
