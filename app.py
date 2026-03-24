import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import io, re

# --- WEBSITE CONFIG ---
st.set_page_config(page_title="IR Interpreter Pro", layout="centered")

st.title("🔬 PhD IR Interpreter Pro")
st.markdown("Automated functional group analysis for Shimadzu IR spectra.")

# Your Research Database
ir_db = {
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

uploaded_file = st.file_uploader("Upload Graph Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Analysis"):
        with st.spinner("Analyzing vertical peaks..."):
            # Initialize the reader
            reader = easyocr.Reader(['en'])
            # We use 90 and 270 degrees to catch vertical Shimadzu text
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            table_data = []
            for (bbox, text, prob) in results:
                # Clean text to keep only digits
                clean_text = "".join(re.findall(r'[0-9.]+', text.replace("I", "1")))
                try:
                    val = float(clean_text)
                    if 400 <= val <= 4000:
                        for group, info in ir_db.items():
                            if (info[0]-15) <= val <= (info[1]+15):
                                table_data.append({
                                    "Peak (cm⁻¹)": val, 
                                    "Interpretation": group, 
                                    "Intensity": info[2]
                                })
                except: continue

            if table_data:
                df = pd.DataFrame(table_data).drop_duplicates(subset=["Peak (cm⁻¹)"])
                df = df.sort_values("Peak (cm⁻¹)", ascending=False)
                st.success("Analysis Complete!")
                st.table(df)
                
                # Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results", data=csv, file_name="IR_Report.csv")
            else:
                st.warning("No peaks detected. Ensure numbers are printed clearly on the graph.")
