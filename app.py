import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- 1. OFFICIAL DATABASE (Table 2.3) ---
OFFICIAL_IR_DATABASE = {
    "Alkane C-H": [2850, 3000, "Strong"],
    "Alkene =C-H": [3000, 3100, "Medium"],
    "Aromatic C-H": [3010, 3050, "Medium"],
    "Alkyne C-H": [3250, 3350, "Strong/Sharp"],
    "Aldehyde C-H": [2720, 2850, "Weak/2 peaks (Fermi)"],
    "Alkene C=C": [1600, 1680, "Medium"],
    "Aromatic C=C": [1475, 1600, "Medium/Weak"],
    "Nitrile C≡N": [2240, 2260, "Medium/Sharp"],
    "Aldehyde C=O": [1720, 1740, "Strong"],
    "Ketone C=O": [1705, 1725, "Strong"],
    "Carboxylic Acid C=O": [1700, 1725, "Strong"],
    "Ester C=O": [1730, 1750, "Strong"],
    "Amide C=O": [1630, 1680, "Strong"],
    "Alcohol O-H": [3200, 3650, "Strong/Broad"],
    "Carboxylic Acid O-H": [2400, 3400, "Very Broad"],
    "Nitro (-NO2)": [1350, 1550, "Strong (Doublet)"],
    "C-O Stretch": [1000, 1300, "Strong"],
    "Arom-Mono": [680, 770, "Strong (2 peaks near 700/750)"],
    "Arom-Para": [800, 860, "Strong (1 peak near 825)"]
}

st.set_page_config(page_title="IR Interpreter Pro", layout="wide")
st.title("🔬 Advanced IR Interpretation Engine")

uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Full Analysis"):
        with st.spinner("Processing Spectrum..."):
            reader = easyocr.Reader(['en'])
            # rotation_info is key for vertical labels
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            interpretations = []
            found_peaks_list = []

            for (bbox, text, prob) in results:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I", "1").replace("l", "1")))
                try:
                    val = float(clean)
                    if 400 <= val <= 4000:
                        for group, range_info in OFFICIAL_IR_DATABASE.items():
                            # Using a 15 cm-1 tolerance for better matching
                            if (range_info[0]-15) <= val <= (range_info[1]+15):
                                interpretations.append({
                                    "Peak Found": val,
                                    "Interpretation": group,
                                    "Standard Range": f"{range_info[0]}-{range_info[1]}",
                                    "Shape": range_info[2]
                                })
                                found_peaks_list.append(val)
                except: continue

            if interpretations:
                df = pd.DataFrame(interpretations).drop_duplicates(subset=["Peak Found"]).sort_values("Peak Found", ascending=False)
                st.subheader("✅ Analysis Results")
                st.dataframe(df, use_container_width=True)
                
                # --- STRUCTURAL LOGIC SECTION ---
                st.subheader("🧪 Molecular Structure Prediction")
                groups = df["Interpretation"].tolist()
                peaks = df["Peak Found"].tolist()
                
                # Logic 1: Aldehyde
                if "Aldehyde C=O" in groups and "Aldehyde C-H" in groups:
                    st.success("🎯 **Predicted Structure: Aldehyde**")
                    st.write("Reason: Found Carbonyl (1720+) and Fermi Doublet (2720/2820).")

                # Logic 2: Carboxylic Acid
                elif "Carboxylic Acid C=O" in groups and "Carboxylic Acid O-H" in groups:
                    st.success("🎯 **Predicted Structure: Carboxylic Acid**")
                    st.write("Reason: Found Carbonyl (~1710) and Very Broad O-H (2400-3400).")

                # Logic 3: Ester
                elif "Ester C=O" in groups and "C-O Stretch" in groups:
                    st.success("🎯 **Predicted Structure: Ester**")
                    st.write("Reason: Found C=O (~1740) and strong C-O (~1200).")

                # Logic 4: Aromatic Substitution Pattern
                st.markdown("---")
                st.write("**Aromatic Substitution (Fingerprint Region):**")
                if any(680 <= p <= 710 for p in peaks) and any(730 <= p <= 770 for p in peaks):
                    st.info("✅ **Pattern: Monosubstituted Benzene Ring**")
                elif any(800 <= p <= 850 for p in peaks):
                    st.info("✅ **Pattern: Para-disubstituted Benzene**")
                else:
                    st.write("No clear substitution pattern detected in 600-900 cm⁻¹.")
                
                # Download results
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", data=csv, file_name="IR_Report.csv")
            else:
                st.error("No peaks detected. Ensure numbers are printed clearly.")
