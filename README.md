# 
### AI AGENT

## Project Description

The **AI Agent** is an interactive web application that enables users to provide a CSV file or a Google Sheet link and select a column from the provided data and ask the agent a dynamic query about the slected column. The agent then performs web search based on the query and then returns the url's and the snippets of information found on the web. The agent leverages AI models (LangChain, Groq API) and uses this data to  produce precise, actionable data based on the user query. The extracted data is displayed in the dashboard, and it can be downloaded as a CSV file.

## Setup Instructions

### 1. Prerequisites

* Python 3.8 or above
* Install required dependencies
* Obtain API keys for:
  * SerpAPI
  * Groq API
  * Google Cloud Service Account

### 2. Clone the Repository

```
git clone 
cd <repository-name>

```

### 3. Install Dependencies

```
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the project directory with the following keys:

```
SERP_API_KEY=your_serp_api_key
GROQ_API_KEY=your_groq_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_service_account_json

```

### 5. Run the Application

Start the Streamlit server:

streamlit run ai_agent.py

## Usage Guide

### Step 1: Select Data Source

* **Upload CSV** : Upload a CSV file containing data.
* **Google Sheets** : Provide a valid Google Sheets URL. Make sure the google sheet is accessible by the agent.

### Step 2: Define the Query

* Input a prompt template like `Get the email address of {entity}`, where `{entity}` will be replaced by data from the selected column in your dataset.
* The application also allows advanced query templates, like extracting multiple fields in a single query. Ex: `Get the email and address for {entity}`

### Step 3: Extract Data

* Click the **Run Data Extraction** button to start the process.
* Application aupports robust error-handling mechanisms like sending the user a notification on an API call fail or LLM fetch fail.
* Preview the extracted data in a table.
* Download the data as a CSV file .

## API Keys and Environment Variables

### Required API Keys

1. **SerpAPI** : For web search queries.
2. **Groq API** : For AI-powered data extraction.
3. **Google Cloud Service Account** : For Google Sheets API access.

### Setting Up Environment Variables

Store the keys in a `.env` file:

```
SERP_API_KEY=your_serp_api_key
GROQ_API_KEY=your_groq_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_service_account_json

```

Ensure the Google service account JSON file is accessible and contains the required credentials for Sheets API.

## Technical Stack Used

* **Dashboard/UI** : Streamlit
* **Data Handling** : pandas for CSV files and Google Sheets API for Google Sheets Integration
* **Search API** : SerpAPI (with ratelimit set)
* **LLM API** : Groq API  (with ratelimit set)
* **Backend** : Python
* **Agents** : LangChain

## Optional Advanced Features

### Advanced Query Templates

Application allows users to extract multiple fields in a single prompt, such as "Get the email and address for {entity}."

### Error Handling

Robust error-handling mechanisms for failed API calls or unsuccessful LLM queries, with user notifications.

### Google Sheets Output Integration

The option has has been provided in the UI but it is not functioning as expected.

### RATE LIMIT
Rate limit has been set for both Groq API and Serp API so that the application wont crash when API call frequency crosses the limit. 

### VIDEO LINK:
https://drive.google.com/file/d/1dvSTwDK2hABpI4C_Zc2lYzI5FdsRSj4q/view?usp=sharing
