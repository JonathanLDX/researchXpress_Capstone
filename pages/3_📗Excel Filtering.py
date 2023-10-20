import streamlit as st
from streamlit_extras.app_logo import add_logo
from concurrent.futures import as_completed
from langchain.callbacks import get_openai_callback
import pandas as pd

import sys,os

workingDirectory = os.getcwd()
chromaDirectory = os.path.join(os.getcwd(), "ChromaDB")
costDirectory = os.path.join(os.getcwd(), "cost_breakdown")
cleanDirectory = os.path.join(os.getcwd(), "Miscellaneous")

if chromaDirectory not in sys.path:
    sys.path.append(chromaDirectory)
if costDirectory not in sys.path:
    sys.path.append(costDirectory)
if cleanDirectory not in sys.path:
    sys.path.append(cleanDirectory)

from filterExcel import filterExcel, getOutputDF, generate_visualisation, clean_findings_df
from User_Input_Cleaning import process_user_input
from update_cost import update_usage_logs, Stage


st.set_page_config(layout="wide")
add_logo("images/htpd_text.png", height=100)

st.markdown("<h1 style='text-align: left; color: Black;'>Excel Filtering</h1>", unsafe_allow_html=True)
st.markdown('#')

if 'filtered' not in st.session_state:
    st.session_state.filtered = False

if not st.session_state.filtered:
    input = st.text_input("Research Prompt", placeholder='Enter your research prompt')

    st.markdown('##')
    uploaded_file = st.file_uploader("Upload your Excel file here", type=['xlsx'], help='Upload an excel file that contains a list of research article titles and their abstracts')

    st.markdown('##')
    col1, col2, col3 , col4, col5, col6, col7 = st.columns(7)

    with col4:
        button = st.button('Submit')
    
    if button:
        if input and not uploaded_file: 
            st.error("Please upload an excel file")
        elif not input and uploaded_file:
            st.error("Please enter a research prompt")
        elif not input or not uploaded_file:
            st.error("Please enter a research prompt and upload an excel file")
        else:
            with get_openai_callback() as usage_info:
                corrected_input, relevant_output = process_user_input(input)
                total_input_tokens = usage_info.prompt_tokens
                total_output_tokens = usage_info.completion_tokens
                total_cost = usage_info.total_cost
                update_usage_logs(Stage.MISCELLANEOUS.value, input, total_input_tokens, total_output_tokens, total_cost)
            if relevant_output == 'irrelevant':
                st.error('Irrelevant Output! Please input a relevant prompt')
            else:
                _, futures = filterExcel(uploaded_file,  corrected_input)
                issues, results, numDone, numFutures, total_input_tokens, total_output_tokens, total_cost = [],[], 0, len(futures), 0, 0, 0
                progessBar = st.progress(0, text="Article filtering in progress...")
                for future in as_completed(futures):
                    row = future.result()
                    total_input_tokens += row[5]
                    total_output_tokens += row[6]
                    total_cost += row[7]
                    results.append(row[0:5])
                    numDone += 1
                    progessBar.progress(numDone/numFutures, text="Article filtering in progress...")
                
                update_usage_logs(Stage.EXCEL_FILTERING.value, corrected_input, total_input_tokens,total_output_tokens,total_cost)
                dfOut = pd.DataFrame(results, columns = ["DOI","TITLE","ABSTRACT","llmOutput", "jsonOutput"])
                dfOut = getOutputDF(dfOut)
                dfOut.to_excel("output/excel_result.xlsx", index=False)

                st.session_state.filtered = input
                st.experimental_rerun()

else:
    st.subheader("Prompt")
    st.markdown(st.session_state.filtered)

    st.subheader("Results")

    # Display output (To be changed during integration)
    df = pd.read_excel("output/excel_result.xlsx")
    clean_df = clean_findings_df(df)
    fig = generate_visualisation(clean_df)
    st.session_state.excel_filter_fig1 = fig
    # st.download_button(label="Download Excel file", data="output/test_output_pfa.xlsx", file_name='results.xlsx') 

    with open("output/excel_result.xlsx", 'rb') as my_file:
        st.download_button(label = 'Download Excel', data = my_file, file_name='results.xlsx', mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') 
        
    st.plotly_chart(st.session_state.excel_filter_fig1, use_container_width=True)

    reupload_button = st.button('Reupload another prompt and excel file')
    if reupload_button:
        st.session_state.filtered = False
        st.experimental_rerun()