import pandas as pd
import streamlit as st
from concurrent.futures import as_completed
from stqdm import stqdm
import glob
import streamlit as st
from streamlit_extras.app_logo import add_logo
from zipfile import ZipFile

import sys, os
workingDirectory = os.getcwd()
chromaDirectory = os.path.join(workingDirectory, "ChromaDB")
sys.path.append(chromaDirectory)

from ingestPdf import pdfUpload, smallChunkCollection

st.set_page_config(layout="wide")
add_logo("images/htpd_text.png", height=100)

st.markdown("<h1 style='text-align: left; color: Black;'>PDF Analysis</h1>", unsafe_allow_html=True)
st.markdown('#')
st.header('PDF Analysis')

if 'pdf_filtered' not in st.session_state:
    st.session_state.pdf_filtered = False

if not st.session_state.pdf_filtered:
    input = st.text_input("Research Prompt", placeholder='Enter your research prompt')

    st.markdown('##')
    uploaded_file = st.file_uploader("Upload your zip folder here", type=['zip'], help='Upload a zip folder containing only PDF research articles')

    st.markdown('##')
    col1, col2, col3 , col4, col5, col6, col7 = st.columns(7)

    with col4:
        button = st.button('Submit')
        
    if button:
        if input and not uploaded_file:
            st.error("Please upload a zip folder")
        elif not input and uploaded_file:
            st.error("Please enter a research prompt")
        elif not input or not uploaded_file:
            st.error("Please enter a research prompt and upload a zip folder")
        else:
            with ZipFile(uploaded_file, 'r') as zip:
                extraction_path = "data/"
                zip.extractall(extraction_path)

            pdfList = glob.glob(os.path.join('data', uploaded_file.name[:-4], '*.pdf'))
            (issues, executor, futures) = pdfUpload(pdfList)
            progessBar1 = st.progress(0, text="Uploading main pdf sections:")
            
            numDone, numFutures = 0, len(futures)
            for future in stqdm(as_completed(futures)):
                result = future.result()
                numDone += 1
                progessBar1.progress((numDone/numFutures),text="Uploading main pdf sections:")

            progessBar1.progress((numDone/numFutures), text="Done uploading main pdf sections")    
            
            progessBar2 = st.progress(0, text="Uploading pdf child sections:")
            executor, child_futures = smallChunkCollection()
            numDone, numFutures = 0, len(child_futures) 
            for future in stqdm(as_completed(child_futures)):
                result = future.result()
                numDone += 1
                progessBar2.progress((numDone/numFutures), text="Uploading pdf child sections:")

            progessBar2.progress((numDone/numFutures), text="Done uploading pdf child sections") 

            st.session_state.pdf_filtered = True

if st.session_state.pdf_filtered:
    st.subheader("Here are the articles relevant to your prompt:")