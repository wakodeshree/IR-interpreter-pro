import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

# --- API SETUP ---
# Securely handle your API Key
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- UI ---
st.title("🔬 AI-Powered IR Spectrum Interpreter")
st.markdown("""
Upload your IR graph (e.g., Shimadzu, Agilent). 
The AI will identify peaks and provide a professional chemical interpretation.
""")

uploaded_file = st.file_uploader("Upload IR Spectrum", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Target Spectrum", use_container_width=True)

    if st.button("Interpret with Gemini AI"):
        if not api_key:
            st.error("Please enter your API Key in the sidebar.")
        else:
            with st.spinner("AI is analyzing the molecular vibrations..."):
                try:
                    # The Prompt: Telling the AI exactly what to look for
                    prompt = """
                    Analyze this Infra-Red (IR) Spectrum. 
                    1. List the major peaks identified by the numbers written on the graph.
                    2. For each major peak, provide the functional group assignment (e.g., C=O stretch, O-H broad).
                    3. Give a final conclusion on the likely functional groups present in the molecule.
                    Format the peak list as a Markdown table.
                    """
                    
                    # Generate content (Image + Text)
                    response = model.generate_content([prompt, img])
                    
                    st.subheader("AI Interpretation")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"API Error: {str(e)}")

# Instructions for the user
with st.expander("How to get an API Key?"):
    st.markdown("""
    1. Go to [Google AI Studio](https://aistudio.google.com/).
    2. Click on 'Get API Key'.
    3. Copy and paste it into the sidebar here.
    """)
