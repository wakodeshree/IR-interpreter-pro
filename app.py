import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- 1. SETTINGS & DATABASE ---
st.set_page_config(page_title="PhD Multi-Spec Dashboard", layout="wide")
st.title("🔬 Integrated IR & H-NMR Interpreter")

OFFICIAL_IR_DATABASE = {
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

# --- 2. CREATE THE TABS ---
tab1, tab2 = st.tabs(["📡 Infrared (IR)", "🧬 H-NMR Analysis"])

# --- TAB 1: IR ANALYSIS ---
with tab1:
    st.header("IR Spectrum Analysis")
    uploaded_file = st.file_uploader("Upload IR Graph", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("🚀 Analyze IR"):
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            interpretations = []
            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I", "1").replace("l", "1")))
                try:
                    val = float(clean)
                    if 400 <= val <= 4000:
                        for group, info in OFFICIAL_IR_DATABASE.items():
                            if (info[0]-12) <= val <= (info[1]+12):
                                interpretations.append({"Peak": val, "Group": group, "Shape": info[2]})
                except: continue

            if interpretations:
                df = pd.DataFrame(interpretations).drop_duplicates(subset=["Peak"])
                st.subheader("✅ IR Results")
                st.table(df)
            else:
                st.error("No IR peaks detected.")

# --- TAB 2: NMR ANALYSIS ---
with tab2:
    st.header("Proton NMR Interpretation")
    st.write("Enter the chemical shifts (δ) from your NMR spectrum.")
    
    # Text input for the numbers
    nmr_input = st.text_input("Enter shifts separated by commas (e.g. 9.8, 7.2, 1.2)", "")
    
    if nmr_input:
        try:
            # Convert text to list of numbers
            shifts = [float(x.strip()) for x in nmr_input.split(",") if x.strip()]
            
            nmr_data = []
            for s in shifts:
                label = "Aliphatic/Alkyl"
                if 9.0 <= s <= 10.2: label = "Aldehyde (CHO)"
                elif 10.5 <= s <= 13.0: label = "Carboxylic Acid (OH)"
                elif 6.5 <= s <= 8.5: label = "Aromatic Protons"
                elif 3.3 <= s <= 4.5: label = "Protons near O/N/Halogen"
                
                nmr_data.append({"Shift (δ)": s, "Proton Type": label})
            
            st.subheader("✅ NMR Results")
            st.table(pd.DataFrame(nmr_data))
            
            # --- COMBINED LOGIC ---
            st.divider()
            if any(9.0 <= s <= 10.2 for s in shifts):
                st.success("🎯 **Conclusion**: NMR confirms an **Aldehyde** group.")
            if any(6.5 <= s <= 8.5 for s in shifts):
                st.info("🎯 **Conclusion**: NMR confirms an **Aromatic Ring**.")
        
        except ValueError:
            st.error("Please enter only numbers and commas.")
