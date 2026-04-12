import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from scipy.signal import find_peaks
import easyocr
import re

st.set_page_config(page_title="IR Analyzer (Advanced OCR)", layout="wide")

st.title("🔬 IR Spectrum Analyzer (OCR + Rotation + Full DB)")

uploaded_file = st.file_uploader("Upload IR Spectrum", type=["png", "jpg", "jpeg"])

# Initialize OCR
reader = easyocr.Reader(['en'], gpu=False)

# 🔥 Extended IR Database
IR_DB = [
    (3700, 3200, "O-H stretch", "Alcohol / Phenol"),
    (3500, 3300, "N-H stretch", "Amine"),
    (3300, 3000, "C-H stretch", "Alkane"),
    (3100, 3000, "C-H stretch", "Aromatic"),
    (2260, 2220, "C≡N stretch", "Nitrile"),
    (2150, 2100, "C≡C stretch", "Alkyne"),
    (1750, 1700, "C=O stretch", "Ester / Ketone"),
    (1690, 1640, "C=O stretch", "Amide"),
    (1680, 1600, "C=C stretch", "Alkene"),
    (1600, 1450, "C=C stretch", "Aromatic ring"),
    (1300, 1000, "C-O stretch", "Alcohol / Ether"),
    (900, 650, "C-H bending", "Aromatic"),
]

# 🧠 OCR extraction
def extract_text(image):
    results = reader.readtext(np.array(image))
    text = " ".join([res[1] for res in results])
    return text

# 🔍 Extract numbers (cm⁻¹ peaks)
def extract_peaks_from_text(text):
    numbers = re.findall(r'\d{3,4}', text)
    peaks = [int(num) for num in numbers if 400 <= int(num) <= 4000]
    return peaks

# 📊 Match with IR DB
def interpret_peaks(peaks):
    data = []
    sr = 1

    for peak in peaks:
        for high, low, group, outcome in IR_DB:
            if low <= peak <= high:
                data.append([
                    sr,
                    peak,
                    f"{low}-{high}",
                    group,
                    outcome
                ])
                sr += 1
                break

    return pd.DataFrame(data, columns=[
        "SrNo", "ObservedPeak", "LiteratureRange", "KeyFindings", "Outcome"
    ])

# 🔄 Rotate image
def rotate_image(image, angle):
    return image.rotate(angle, expand=True)

if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="Original Image", use_column_width=True)

    if st.button("Analyze Spectrum"):

        st.write("🔄 Processing multiple orientations...")

        images = [
            image,
            rotate_image(image, 90),
            rotate_image(image, 270)
        ]

        all_peaks = []

        for idx, img in enumerate(images):
            text = extract_text(img)
            peaks = extract_peaks_from_text(text)
            all_peaks.extend(peaks)

        # Remove duplicates
        all_peaks = list(set(all_peaks))

        df = interpret_peaks(all_peaks)

        if not df.empty:
            st.success("Analysis Complete ✅")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "ir_analysis.csv", "text/csv")

        else:
            st.warning("No peaks detected. Try clearer image.")
