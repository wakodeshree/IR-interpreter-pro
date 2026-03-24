import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE COMPLETE IR DATABASE (Table 2.3) ---
IR_DB = {
    "Alcohol O-H (Broad)": [3200, 3650],
    "Carboxylic Acid O-H (Very Broad)": [2400, 3400],
    "Amine/Amide N-H": [3100, 3500],
    "Alkyne ≡C-H": [3250, 3350],
    "Aromatic C-H": [3000, 3100],
    "Alkene =C-H": [3010, 3100],
    "Alkane C-H": [2850, 2970],
    "Aldehyde C-H (Fermi Doublet)": [2720, 2850],
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
    "C-O Stretch (Ether/Ester/Alcohol)": [1000, 1300],
    "C-Cl (Halide)": [540, 785]
}

# --- 2. THE CLEANING ENGINE ---
def is_scale(val):
    """Ignores standard IR axis numbers"""
    scale_markers = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 500, 400]
    return int(val) in scale_markers if val % 1 == 0 else False

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Professional IR Interpreter", layout="wide")
st.title("🔬 Professional IR Interpretation Engine")
st.write("Upload your IR graph to detect peaks and match them against the official database.")

uploaded_file = st.file_uploader("Upload IR Image (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Spectrum", use_container_width=True)
    
    if st.button("🚀 Analyze Spectrum"):
        with st.spinner("Scanning for peaks and matching data..."):
            # Initialize OCR for vertical labels
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            peaks_found = []
            for (bbox, text, prob) in results:
                # Clean text: keep only numbers and decimals
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                
                try:
                    val = float(clean)
                    # Filter: Range check and Scale check
                    if 400 <= val <= 4000 and not is_scale(val):
                        for group, r in IR_DB.items():
                            # 10 cm-1 buffer for experimental shift
                            if (r[0]-10) <= val <= (r[1]+10):
                                peaks_found.append({
                                    "Wavenumber (cm⁻¹)": val,
                                    "Functional Group": group,
                                    "Literature Range": f"{r[0]} - {r[1]}"
                                })
                except:
                    continue

            if peaks_found:
                df = pd.DataFrame(peaks_found).drop_duplicates(subset=["Wavenumber (cm⁻¹)"])
                df = df.sort_values("Wavenumber (cm⁻¹)", ascending=False)
                
                st.subheader("✅ Detected Functional Groups")
                st.table(df)
                
                # Structural Logic
                groups = df["Functional Group"].tolist()
                st.subheader("🎯 Structural Summary")
                if "Aldehyde C=O" in groups and "Aldehyde C-H (Fermi Doublet)" in groups:
                    st.success("The compound is likely an **Aldehyde**.")
                elif "Carboxylic Acid C=O" in groups and "Carboxylic Acid O-H (Very Broad)" in groups:
                    st.success("The compound is likely a **Carboxylic Acid**.")
                elif "Ester C=O" in groups and "C-O Stretch (Ether/Ester/Alcohol)" in groups:
                    st.success("The compound is likely an **Ester**.")
                else:
                    st.info("Multiple functional groups detected. Compare with NMR for full structure.")
            else:
                st.warning("No peaks detected. Ensure numerical labels are clearly visible on the graph.")
