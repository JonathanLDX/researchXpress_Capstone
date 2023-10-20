import streamlit as st
from streamlit_extras.app_logo import add_logo
import pandas as pd
from langchain.callbacks import get_openai_callback
from json.decoder import JSONDecodeError



# Build path from working directory and add to system paths to facilitate local module import
import os, sys

workingDirectory = os.getcwd()
dataDirectory = os.path.join(workingDirectory, "data")
chromaDirectory = os.path.join(workingDirectory, "ChromaDB")
analysisDirectory = os.path.join(workingDirectory, "Analysis")
miscellaneousDirectory = os.path.join(workingDirectory, "Miscellaneous")
costDirectory = os.path.join(workingDirectory, "cost_breakdown")

sys.path.append(chromaDirectory)
sys.path.append(analysisDirectory)
sys.path.append(miscellaneousDirectory)
sys.path.append(costDirectory)


import chromaUtils
from chromaUtils import getCollection, getDistinctFileNameList
from hypSupport import get_llm_response, correct_format_json, get_stance_and_evidence, get_support_chart, get_support_table, get_full_cleaned_df
from Individual_Analysis import get_yes_pdf_filenames
from update_cost import update_usage_logs, Stage


st.set_page_config(layout="wide")
add_logo("images/htpd_text.png", height=100)

st.markdown("<h1 style='text-align: left; color: Black;'>Support Analysis</h1>", unsafe_allow_html=True)
st.markdown('#')

if 'pdf_filtered' not in st.session_state:
    st.session_state.pdf_filtered = False
if 'collection' not in st.session_state:
    st.session_state.collection = None




if 'support_analysis_prompt' not in st.session_state:
    st.session_state.support_analysis_prompt = False

if not st.session_state.support_analysis_prompt: 
    input_collection_name = st.selectbox(
        'Input Collection', chromaUtils.getListOfCollection(), 
        placeholder="Select the Collection you would like to use"
    )
    input = st.text_input("Research Prompt", placeholder='Enter your research prompt (e.g. Is drug A more harmful than drug B?)')
    st.markdown('##')
    col1, col2 = st.columns(2)
    with col1: 
        start_analysis = st.button("Submit")
    with col2:
        analyse_all_articles = st.toggle("All articles", value=False, 
                                        help="Select the toggle to analyse all uploaded articles. If not selected, analysis will only be conducted on filtered articles.")
        st.session_state.analyse_all_articles = analyse_all_articles

    # Run if "Analyse literature support" button is clicked
    if start_analysis:
        #If there is a collection name
        if input_collection_name: 
            #If prompt
            if input:
                # Initialise empty article title list
                article_title_list = []
                total_num_articles = len(article_title_list)

                # 2 options: Analyse only filtered PDF articles or all PDF articles
                if not st.session_state.analyse_all_articles:
                    # Retrieve output dataframe of PDF analysis from Streamlit session state
                    if 'pdf_ind_fig2' not in st.session_state:
                        st.error("You have no filtered PDF articles")
                    else: 
                        # Extract output of PDF upload and filtering stage
                        ind_findings_df = st.session_state.pdf_ind_fig2
                        article_title_list = get_yes_pdf_filenames(ind_findings_df)
                        total_num_articles = len(article_title_list)
                else:
                    article_title_list = getDistinctFileNameList("pdf")
                    total_num_articles = len(article_title_list)
                    if total_num_articles == 0:
                        st.error("You have no PDF articles in the database. Please use the PDF Analysis page to upload the articles.")

                # Obtain dataframe of LLM responses. Only run if number of articles > 0
                if total_num_articles > 0:
                    # Connect to database
                    db = getCollection("pdf")

                    # Initialise holder lists to temporarily store output
                    response_list = ['']*total_num_articles
                    source_docs_list = ['']*total_num_articles
                    stance_list = ['']*total_num_articles
                    evidence_list = ['']*total_num_articles
                    # Holder list to store article titles with error in obtaining output
                    article_error_list = []

                    with get_openai_callback() as usage_info:
                        progressBar = st.progress(0, text="Analysing articles...")

                        for i in range(total_num_articles):
                            try: 
                                article_title = article_title_list[i]
                                # Make LLM call to get response
                                response, source_docs = get_llm_response(db, input, article_title)
                                response_list[i] = response
                                source_docs_list[i] = source_docs
                                # Extract stance and evidence from response
                                stance, evidence = get_stance_and_evidence(response)
                                stance_list[i] = stance
                                evidence_list[i] = evidence
                            except JSONDecodeError:
                                corrrected_response = correct_format_json(response_list[i])
                                response_list[i] = corrrected_response
                                try: 
                                    stance, evidence = get_stance_and_evidence(response_list[i])
                                    stance_list[i] = stance
                                    evidence_list[i] = evidence
                                except Exception:
                                    article_error_list.append(article_title)
                            except Exception:
                                article_error_list.append(article_title)

                            # Update progress
                            progress_display_text = f"Analysing articles: {i+1}/{total_num_articles} completed."
                            progressBar.progress((i+1)/total_num_articles, text=progress_display_text)
                            
                        support_df_raw = pd.DataFrame({"article": article_title_list, "stance": stance_list, "evidence": evidence_list, "source_docs": source_docs_list, "raw_output": response_list})
                        # Store dataframe as Excel file in local output folder
                        support_df_cleaned = get_full_cleaned_df(support_df_raw)
                        support_df_cleaned.to_excel("output/support_analysis_results.xlsx", index=False)
                        
                        # Display success message
                        progressBar.empty()
                        st.success(f"Analysis Complete.")

                        # Display error message if there are articles that cannot be analysed due to error
                        if len(article_error_list) > 0:
                            st.error("Error in extracting output for the articles below")
                            with st.expander("Articles with error:"):
                                for article_title in article_error_list:
                                    st.markdown(f"- {article_title}")
                        
                        # Update usage info
                        update_usage_logs(Stage.SUPPORT_ANALYSIS.value, input, 
                            usage_info.prompt_tokens, usage_info.completion_tokens, usage_info.total_cost)
                        
                        # TEST
                        # support_df_raw = pd.read_csv("C:/Users/laitz/OneDrive/Documents/BT4103_Capstone_MHA/output/support_output [Is cannabis more harmful than tobacco_].csv")
                        # support_df_cleaned = get_full_cleaned_df(support_df_raw)
                        # support_df_cleaned.to_excel("output/support_analysis_results.xlsx", index=False)

                        st.session_state.support_analysis_prompt = input
                        st.experimental_rerun()
            else:
                st.error("Please input a prompt")
        else:
            st.error("Please choose a collection")

else:
    st.subheader("Prompt")
    st.markdown(st.session_state.support_analysis_prompt)
    support_analysis_scope = "All articles" if st.session_state.analyse_all_articles else "Filtered articles"
    st.markdown(f"Scope: {support_analysis_scope}")

    # Read output Excel file
    support_df = pd.read_excel("output/support_analysis_results.xlsx")
    st.subheader("Results")
    
    st.markdown("Support Summary Chart:")
    fig1 = get_support_chart(support_df)
    fig1.update_layout(title_text='Distribution of article response')
    st.session_state.support_chart = fig1
    st.plotly_chart(st.session_state.support_chart, use_container_width=True)

    st.markdown("Support Summary Table:")
    fig2 = get_support_table(support_df)
    fig2.update_layout(title_text='Article response and evidence', margin_autoexpand=True, height=800)
    st.session_state.support_table = fig2
    st.plotly_chart(st.session_state.support_table, use_container_width=True)

    # Download Plotly figure as HTML
    # st.download_button(
    #     label="Download HTML",
    #     data=fig2.to_html(),
    #     file_name="figure.html",
    #     mime="text/html",
    # )

    st.markdown("Download Output File:")
    # Download output as Excel file
    with open("output/support_analysis_results.xlsx", 'rb') as my_file:
        st.download_button(label="Download Excel",
                            # Store output results in a csv file
                            data=my_file,
                            # Query appended at end of output file name
                            file_name=f'support_output [{st.session_state.support_analysis_prompt}].xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    st.markdown("#")
    col1, col2, col3 = st.columns(3)
    with col2: 
        retry_button = st.button('Submit another prompt')
    if retry_button:
        st.session_state.support_analysis_prompt = False
        st.experimental_rerun()