import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import io, re

st.set_page_config(page_title="IR Interpreter Pro", layout="wide")
st.title("🔬 PhD IR Interpreter Pro (Exact Match)")
st.markdown("Automated analysis optimized for Shimadzu high-precision decimal peaks.")

# Database
ir_db = {
    "O-H (Alcohol/Phenol)": [3200, 3650, "Strong/Broad"],
    "N-H (Amine/Amide)": [3100, 3500, "Medium/Sharp"],
    "C-H (Alkane)": [2850, 3000, "Strong"],
    "C=O (Ketone/Aldehyde/Acid)": [1700, 1740, "Strong"],
    "C=C (Alkene/Aromatic)": [1450, 1680, "Medium"],
    "C-O Stretch": [1000, 1300, "Strong"],
    "Aromatic C-H (oop)": [675, 900, "Strong"]
}

uploaded_file = st.file_uploader("Upload Graph Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Exact Analysis"):
        with st.spinner("Analyzing vertical peaks..."):
            reader = easyocr.Reader(['en'])
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            table_data = []
            for (bbox, text, prob) in results:
                # FIXED CLEANING: Keeps the decimals exactly as printed
                clean_text = text.replace("I", "1").replace("l", "1").replace(" ", "")
                clean_text = "".join(re.findall(r'[0-9.]+', clean_text))
                
                try:
                    if len(clean_text) < 3: continue
                    peak_val = float(clean_text)
                    if 400 <= peak_val <= 4000:
                        for group, info in ir_db.items():
                            if (info[0]-15) <= peak_val <= (info[1]+15):
                                table_data.append({"Peak Observed": peak_val, "Interpretation": group, "Range": f"{info[0]}-{info[1]}"})
                except: continue

            if table_data:
                df = pd.DataFrame(table_data).drop_duplicates(subset=["Peak Observed"]).sort_values("Peak Observed", ascending=False)
                st.success("Analysis Complete!")
                st.table(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", data=csv, file_name="IR_Report.csv")
            else:
                st.warning("No matches found. Check the image clarity.")
