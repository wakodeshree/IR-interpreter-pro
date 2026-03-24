import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE COMPLETE IR DATABASE ---
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
    "C-Cl (Halide)": [540, 785, "Strong"]}

# --- 2. STRUCTURE -> REQUIRED GROUPS MAPPING ---
STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"],
    "Amine/Amide N-H": ["Amine/Amide N-H"],
    "Nitrile (C≡N)": ["Nitrile (C≡N)"],
    "Alkyne (C≡C)": ["Alkyne (C≡C)"]       
}

st.set_page_config(page_title="Structure-Verified IR", layout="wide")
st.title("🔬 Structure-Verified IR Interpreter")

# --- 3. THE SELECTOR ---
target_structure = st.selectbox("Select the expected Structure to verify:", list(STRUCTURE_LOGIC.keys()))

uploaded_file = st.file_uploader("Upload IR Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Verify Structure"):
        reader = easyocr.Reader(['en'])
        results = reader.readtext(np.array(img), rotation_info=[90, 270])
        
        peaks_found = []
        for (bbox, text, prob) in results:
            clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
            try:
                val = float(clean)
                # Ignore Scale (4000, 500 etc)
                if val in [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500]: continue
                
                if 400 <= val <= 4000:
                    for group, r in IR_DB.items():
                        if (r[0]-15) <= val <= (r[1]+15):
                            peaks_found.append({"Wavenumber": val, "Group": group})
            except: continue

        if peaks_found:
            full_df = pd.DataFrame(peaks_found).drop_duplicates(subset=["Wavenumber"])
            
            # --- THE FILTERING LOGIC ---
            required_groups = STRUCTURE_LOGIC[target_structure]
            
            if target_structure == "All Peaks (No Filter)":
                display_df = full_df
            else:
                # Filter to only show groups that belong to the selected structure
                display_df = full_df[full_df["Group"].isin(required_groups)]

            st.subheader(f"✅ Peaks relevant to: {target_structure}")
            if not display_df.empty:
                st.table(display_df.sort_values("Wavenumber", ascending=False))
                
                # Check if all required groups were found
                found_set = set(display_df["Group"].tolist())
                missing = set(required_groups) - found_set
                
                if not missing:
                    st.success(f"🎯 Structural Match! All expected peaks for {target_structure} were detected.")
                else:
                    st.warning(f"⚠️ Missing peaks for: {', '.join(missing)}. Structure might be different.")
            else:
                st.error(f"No peaks matching the {target_structure} pattern were found.")
