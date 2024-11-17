import os
import streamlit as st
import pandas as pd
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain.tools import Tool
from groq import Groq
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

# Initialize API keys
SERP_API_KEY = os.environ.get("SERP_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

# Google Sheets API setup
def get_google_sheets_service():
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build("sheets", "v4", credentials=credentials)
    return service

def read_google_sheet(spreadsheet_id, range_name):
    try:
        service = get_google_sheets_service()
        sheet_data = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, 
            range=range_name
        ).execute()
        return pd.DataFrame(
            sheet_data.get("values", [])[1:], 
            columns=sheet_data.get("values", [])[0]
        )
    except Exception as e:
        st.error(f"Error reading Google Sheet: {e}")
        return None

def update_google_sheet(spreadsheet_id, range_name, data):
    try:
        service = get_google_sheets_service()
        body = {"values": data}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return result
    except Exception as e:
        st.error(f"Error updating Google Sheet: {e}")
        raise e


# Setting max 20 requests per minute
MAX_CALLS = 15
PERIOD = 60

# Function for web search using SerpAPI
@sleep_and_retry
@limits(calls=MAX_CALLS, period=PERIOD)
def search_web(query):
    search_url = "https://serpapi.com/search"
    params = {"q": query, "api_key": SERP_API_KEY, "num": 1}
    
    try:
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            return response.json().get("organic_results", [])
        else:
            # Log detailed error information
            st.error(f"SerpAPI error: {response.status_code} - {response.reason}")
            st.error(f"Response content: {response.text}")
            return []
    except Exception as e:
        st.error(f"An exception occurred while querying SerpAPI: {e}")
        return []

# Function to query Groq for information extraction
def query_groq(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", 
                 "content":(
                    "You are a data extraction assistant designed to help users retrieve specific "
                    "information from various sources like CSV files, Google Sheets, and web searches. "
                    "Your task is to analyze user queries and extract relevant data based on the provided context. "
                    "You can utilize tools such as a web search and data extraction APIs to gather necessary information. "
                    "Please provide concise and accurate results in the format requested by the user, "
                    "and ensure that the answers are tailored to the specific data source (CSV or Google Sheets)."
                ),
                 },
                {"role": "user", "content": prompt},
            ],
            model="mixtral-8x7b-32768",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API error: {e}")
        return "Error"

# Create LangChain tools
search_tool = Tool(
    name="Search Web",
    func=search_web,
    description="Searches the web for information using SerpAPI based on the query."
)

groq_tool = Tool(
    name="Query Groq",
    func=query_groq,
    description="Queries Groq API for extracting specific information."
)

# Streamlit UI
st.title("AI Agent for Data Extraction")
st.write("Upload a CSV file or connect to a Google Sheet to extract information.")

# File upload or Google Sheets connection
data_source = st.radio("Choose your data source:", ("Upload CSV", "Google Sheets"))

df = None
spreadsheet_id = None

if data_source == "Upload CSV":
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
elif data_source == "Google Sheets":
    google_sheet_url = st.text_input("Enter Google Sheets URL:")
    if google_sheet_url:
        try:
            spreadsheet_id = google_sheet_url.split("/")[5]
            if not spreadsheet_id:
                st.error("Invalid Google Sheets URL")
            else:
                df = read_google_sheet(spreadsheet_id, "Sheet1")
        except Exception as e:
            st.error(f"Error processing Google Sheets URL: {e}")

if df is not None:
    st.write("Preview of Uploaded Data:")
    st.write(df.head())
    
    main_column = st.selectbox(
        "Select the column to extract data from:", 
        df.columns
    )

    # Prompt input
    prompt_template = st.text_input(
        "Enter your query (use `{entity}` as a placeholder): Look at below example ", 
        "Get the email address of {entity}"
    )

    # Initialize LangChain LLM
    llm = ChatGroq(
        model="mixtral-8x7b-32768",
        temperature=0.0,
        max_retries=2,
    )

    # Initialize LangChain agent
    agent = initialize_agent(
        tools=[search_tool, groq_tool],
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )

    # Run data extraction
    if st.button("Run Data Extraction"):
        extracted_data = []
        progress_bar = st.progress(0)
        total_entities = len(df[main_column].unique())

        for idx, entity in enumerate(df[main_column].unique()):
            formatted_prompt = prompt_template.replace("{entity}", entity)
            st.write(f"Running extraction for: {entity}")

            try:
                agent_response = agent.run(formatted_prompt)
                extracted_data.append({
                    "Entity": entity, 
                    "Extracted Data": agent_response
                })
            except Exception as e:
                st.error(f"Error processing {entity}: {e}")
                extracted_data.append({
                    "Entity": entity, 
                    "Extracted Data": "Error during extraction"
                })

            # Update progress bar
            progress_bar.progress((idx + 1) / total_entities)

        # Display and save extracted data
        if extracted_data:
            extracted_df = pd.DataFrame(extracted_data)
            st.write("Extracted Data")
            
            # Add scrollable table style
            st.markdown(
                """
                <style>
                .scrollable-table {
                    overflow-x: auto;
                    display: block;
                    white-space: nowrap;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Display table
            st.markdown('<div class="scrollable-table">', unsafe_allow_html=True)
            st.write(extracted_df.to_html(index=False, escape=False), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Download as CSV
            csv = extracted_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Extracted Data",
                csv,
                "extracted_data.csv",
                "text/csv"
            )

            # Update Google Sheet if using Google Sheets
            if data_source == "Google Sheets" and spreadsheet_id:
                if st.button("Update Google Sheet", key="update_sheet"):
                    try:
                        with st.spinner("Updating Google Sheet..."):
                            # Preview data to be updated
                            st.write("Preview of data to be updated:")
                            st.dataframe(extracted_df)

                            # Prepare data for Google Sheets
                            header = [["Entity", "Extracted Data"]]
                            data_rows = extracted_df.values.tolist()
                            data_to_update = header + data_rows

                            # Update Google Sheet
                            update_google_sheet(
                                spreadsheet_id=spreadsheet_id,
                                range_name="Sheet1!C1",
                                data=data_to_update
                            )
                            st.success("Google Sheet updated successfully!")
                    except Exception as e:
                        st.error(f"Failed to update Google Sheet: {e}")
        else:
            st.warning("No extracted data to display.")
else:
    st.warning("Please upload a file or provide a valid Google Sheets URL.")