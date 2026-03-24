import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- 1. OFFICIAL DATABASE (Table 2.3) ---
# Format: "Group Name": [Min_Range, Max_Range, "Description/Shape"]
OFFICIAL_IR_DATABASE = {
    "Alcohol (O-H)": [3200, 3650, "Strong, Broad"],
    "Carboxylic Acid (O-H)": [2500, 3300, "Very Broad"],
    "Amine (N-H)": [3300, 3500, "Medium, Sharp"],
    "Alkyne (C-H)": [3260, 3330, "Strong, Sharp"],
    "Alkene (=C-H)": [3010, 3100, "Medium"],
    "Aromatic (C-H)": [3000, 3100, "Medium"],
    "Alkane (C-H)": [2850, 2960, "Strong"],
    "Aldehyde (C-H)": [2720, 2820, "Weak, Fermi Doublet"],
    "Nitrile (C≡N)": [2210, 2260, "Medium, Sharp"],
    "Alkyne (C≡C)": [2100, 2260, "Weak/Medium"],
    "Ester (C=O)": [1735, 1750, "Strong"],
    "Aldehyde (C=O)": [1720, 1740, "Strong"],
    "Ketone (C=O)": [1705, 1725, "Strong"],
    "Carboxylic Acid (C=O)": [1700, 1725, "Strong"],
    "Amide (C=O)": [1630, 1690, "Strong"],
    "Alkene (C=C)": [1600, 1680, "Medium"],
    "Aromatic (C=C)": [1450, 1600, "Medium/Weak"],
    "Nitro (-NO2)": [1300, 1550, "Strong, Doublet"],
    "C-O Stretch": [1000, 1300, "Strong"],
    "Arom (Mono)": [690, 710, "Strong"],
    "Arom (Mono/Ortho)": [730, 770, "Strong"]
}

# --- 2. THE APP INTERFACE ---
st.set_page_config(page_title="PhD IR Interpreter", layout="wide")
st.title("🔬 Official IR Interpretation Engine")
st.write("Upload a Shimadzu IR Graph for automated interpretation based on Table 2.3")

uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    # Pre-processing for precision
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Interpret Spectrum"):
        with st.spinner("Step 1: Detecting Peaks..."):
            reader = easyocr.Reader(['en'])
            # rotation_info ensures we catch the vertical numbers on the graph
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            interpretations = []
            for (bbox, text, prob) in results:
                # Clean text: remove noise, keep decimals
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I", "1").replace("l", "1")))
                
                try:
                    val = float(clean)
                    if 400 <= val <= 4000:
                        # Step 2: Match against Official Database
                        matched = False
                        for group, range_info in OFFICIAL_IR_DATABASE.items():
                            if (range_info[0]-10) <= val <= (range_info[1]+10):
                                interpretations.append({
                                    "Peak Found": val,
                                    "Official Interpretation": group,
                                    "Expected Range": f"{range_info[0]}-{range_info[1]}",
                                    "Intensity/Shape": range_info[2]
                                })
                                matched = True
                except: continue

            if interpretations:
                df = pd.DataFrame(interpretations).drop_duplicates(subset=["Peak Found"]).sort_values("Peak Found", ascending=False)
                
                st.subheader("✅ Analysis Results")
                st.dataframe(df, use_container_width=True)
                
                # --- Step 3: Advanced Structure Logic ---
                st.subheader("🧪 Structural Predictions")
                found_groups = df["Official Interpretation"].tolist()
                
                if "Carboxylic Acid (C=O)" in found_groups and "Carboxylic Acid (O-H)" in found_groups:
                    st.info("🎯 **Prediction**: This molecule is likely a **Carboxylic Acid**.")
                elif "Aldehyde (C=O)" in found_groups and "Aldehyde (C-H)" in found_groups:
                    st.info("🎯 **Prediction**: This molecule is likely an **Aldehyde**.")
                
            else:
                st.error("No peaks detected. Ensure numerical labels are clear on the graph.")
