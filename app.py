import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io, re

# --- CONFIG ---
st.set_page_config(page_title="IR Structure Predictor Pro", layout="wide")
st.title("🔬 IR Structure Predictor Pro")
st.markdown("Automated Peak Detection & Advanced Substitution Analysis")

# --- DATABASE ---
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

uploaded_file = st.file_uploader("Upload Shimadzu Graph", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    st.image(raw_img, use_container_width=True)
    
    # Pre-processing
    proc_img = ImageOps.autocontrast(raw_img.convert('L'))
    enhancer = ImageEnhance.Sharpness(proc_img)
    proc_img = enhancer.enhance(2.0)

    if st.button("🚀 Run Analysis"):
        with st.spinner("Extracting Precise Data..."):
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(proc_img), rotation_info=[90, 270])
            
            table_data = []
            for (bbox, text, prob) in results:
                clean_text = text.replace("I", "1").replace("l", "1").replace(" ", "")
                clean_text = "".join(re.findall(r'[0-9.]+', clean_text))
                try:
                    if len(clean_text) < 3: continue
                    val = float(clean_text)
                    if 400 <= val <= 4000:
                        for group, info in ir_db.items():
                            if (info[0]-15) <= val <= (info[1]+15):
                                table_data.append({"Peak": val, "Interpretation": group, "Intensity": info[2]})
                except: continue

            if table_data:
                df = pd.DataFrame(table_data).drop_duplicates(subset=["Peak"]).sort_values("Peak", ascending=False)
                st.subheader("1. Detected Peaks")
                st.dataframe(df, use_container_width=True)

                # --- ADVANCED ANALYSIS ---
                st.subheader("🧪 Advanced Structural Analysis")
                peaks = df["Peak"].values
                
                # Substitution Logic
                sub_msg = "⚠️ No aromatic substitution pattern found in 675-900 cm⁻¹ region."
                if any(730 <= p <= 770 for p in peaks) and any(680 <= p <= 710 for p in peaks):
                    sub_msg = "✅ **Monosubstituted Benzene Ring** (~750 and ~700 cm⁻¹)"
                elif any(735 <= p <= 775 for p in peaks):
                    sub_msg = "✅ **Ortho-disubstituted (1,2-di)** (~750 cm⁻¹)"
                elif any(800 <= p <= 855 for p in peaks):
                    sub_msg = "✅ **Para-disubstituted (1,4-di)** (~825 cm⁻¹)"
                
                st.info(sub_msg)

                # Shape Logic
                if any(3200 <= p <= 3650 for p in peaks):
                    st.warning("📢 **Shape Analysis**: Broad peak found >3200 cm⁻¹ (H-Bonding/Alcohol).")

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", data=csv, file_name="IR_Report.csv")
            else:
                st.error("No peaks detected. Ensure the graph labels are clear.")
