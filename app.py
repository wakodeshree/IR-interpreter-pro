import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE COMPLETE IR DATABASE ---
IR_DB = {
    "Alcohol O-H": [3200, 3650],
    "Carboxylic Acid O-H": [2400, 3400],
    "Aldehyde C-H (Fermi)": [2720, 2850],
    "Ester C=O": [1730, 1750],
    "Aldehyde C=O": [1720, 1740],
    "Ketone C=O": [1705, 1725],
    "Carboxylic Acid C=O": [1700, 1725],
    "Amide C=O": [1630, 1680],
    "Nitro (-NO2)": [1350, 1550],
    "C-O Stretch": [1000, 1300]
}

# --- 2. STRUCTURE -> REQUIRED GROUPS MAPPING ---
STRUCTURE_LOGIC = {
    "All Peaks (No Filter)": [],
    "Aldehyde": ["Aldehyde C=O", "Aldehyde C-H (Fermi)"],
    "Carboxylic Acid": ["Carboxylic Acid C=O", "Carboxylic Acid O-H"],
    "Ester": ["Ester C=O", "C-O Stretch"],
    "Alcohol/Phenol": ["Alcohol O-H", "C-O Stretch"],
    "Ketone": ["Ketone C=O"]
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
