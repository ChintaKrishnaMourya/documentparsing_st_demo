import streamlit as st
import tempfile
import os
import pdfplumber
import openai
import json
import pandas as pd

# Define your OpenAI API key
api_key = st.secrets["api_key"]
openai.api_key = api_key

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = '' 
            
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                all_text += text 
        return all_text
    except Exception as e:
        st.error(f"Error converting file {pdf_path} to text: {e}")
        return ""

def get_choice_text_from_prompt(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0,
            max_tokens=10000
        )
        choice_text = response.choices[0]["message"]["content"]
        return choice_text
    except Exception as e:
        print("Error in get_choice_text_from_prompt:", str(e))
        st.error(f"Error communicating with OpenAI: {e}")

def parser(all_text):
    try:
        system = """
        Your task is to analyze and parse the text into a meaningful structured JSON format.
        You will be provided with text extracted from 'invoices', 'packing list', 'bill of lading', 'cargo permit' PDFs.

        The system instruction is:
        
        Step-1: 
        Analyze and parse the following information from the PDF text, do not just extract the data, rephrase it meaningfully:
        Choose the valid fields from the PDF text that you feel necessary and make 
        If text is not an 'invoice', 'packing list', 'bill of lading', 'cargo permit', then give output as this is not 'invoices', 'packing list', 'bill of lading', 'cargo permit' .

        Step-2:
        Return the meaningful parsed data in a structured JSON format with keys and corresponding values-
        
        If text is not an 'invoice', 'packing list', 'bill of lading', 'cargo permit', then give output as this is not 'invoices', 'packing list', 'bill of lading', 'cargo permit'.

        Step-3:
        Only return the parsed JSON format, nothing else.
        """
        prompt = f"""
        Only return the structured parsed JSON format of 'invoice', 'packing list', 'bill of lading', 'cargo permit'.
        Extracted text is delimited by triple backticks below.

        Extracted Text:```{all_text}```
        """

        messages =  [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ]

        structured = get_choice_text_from_prompt(messages)
        structured_json = json.loads(structured)
        return structured_json
    except Exception as e:
        print(f"Error parsing Document: {e}")
        st.error(f"Error parsing Document: {e}")

st.set_page_config(page_title="Document Parser", page_icon="📄")
st.header("Document Parsing")
resume = st.file_uploader("Upload Document", accept_multiple_files=False)

if st.button("Submit"):
    if resume:
        try:
            temp_dir = tempfile.TemporaryDirectory()
            file_path = os.path.join(temp_dir.name, resume.name)

            with open(file_path, "wb") as f:
                f.write(resume.read())

            extracted_text = extract_text_from_pdf(file_path)
            st.write("Text Extracted\n")
            parsed_json = parser(extracted_text)
            st.write("Information Parsed\n")
            # Display the parsed JSON

        # Display a message before showing the parsed JSON
            st.write("Parsed info from the doc: \n")
            st.json(parsed_json)


            # Convert the JSON to a DataFrame
            df = pd.DataFrame.from_dict(parsed_json, orient='index').T
            
            # Save the DataFrame to a CSV file
            csv_path = os.path.join(temp_dir.name, 'parsed_doc.csv')
            df.to_csv(csv_path, index=False)
            
            # Provide a download link for the CSV file
            # Provide a download link for the CSV file with the correct MIME type
            st.download_button("Download Parsed Document (CSV)", data=open(csv_path, 'rb'), key='parsed_doc', mime='text/csv')


        except Exception as e:
            st.error(f"An error occurred: {e}")
