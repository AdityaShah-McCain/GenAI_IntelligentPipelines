# import os
# import json
# import requests
# import textwrap
# import argparse

# # --- LangChain Imports ---
# # Required: pip install langchain langchain-google-genai
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.output_parser import StrOutputParser

# # --- Configuration from Environment Variables ---
# # These will be set in the GitHub Actions workflow file.
# TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")
# GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# PIPELINE_STATUS = os.environ.get("PIPELINE_STATUS")
# PIPELINE_NAME = os.environ.get("PIPELINE_NAME", "N/A")
# PIPELINE_URL = os.environ.get("PIPELINE_URL", "#")
# COMMIT_SHA = os.environ.get("COMMIT_SHA", "N/A")
# AUTHOR = os.environ.get("AUTHOR", "N/A")

# def get_langchain_analysis(logs: str) -> str:
#     """
#     Invokes a LangChain chain to get a concise, natural-language
#     explanation of the error from the provided logs.
#     """
#     try:
#         # Initialize the LLM. We're using Gemini Flash for speed and cost-effectiveness.
#         llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-pro", temperature=0.3, google_api_key=GOOGLE_API_KEY)
        
#         # Define the prompt template for the LLM

#         # Error Analysis Prompt Template
#         prompt_template = textwrap.dedent("""
#             You are a senior DevOps engineer and an expert in CI/CD pipelines.
#             Your task is to analyze the following CI/CD pipeline logs, identify the root cause of the failure,
#             and explain it in 2-3 concise sentences.
#             Focus on the most likely reason for the failure. Do not suggest solutions, just explain the error clearly.

#             Here are the logs:
#             ---
#             {logs}
#             ---
#         """)

#         # Code Fixes Prompt Template
#         # prompt_template = textwrap.dedent("""
#         #     You are an expert DevOps engineer and a senior software developer reviewing a failed CI/CD pipeline. Your sole task is to analyze the following logs, identify the root cause of the failure, and provide a direct, actionable code or configuration fix. Do not provide a summary of the error. Focus only on the solution.
#         #     If possible, present the fix as a clear "before" and "after" code block. If the fix involves a command, provide the exact command to run.

#         #     ---
#         #     Logs:
#         #     {logs}
#         #     ---
#         # """)

#         # Error Analysis and Code Fixes Prompt Template
#         # prompt_template = textwrap.dedent("""
#         #     You are an expert DevOps engineer and a senior software developer reviewing a failed CI/CD pipeline. Your task is to analyze the following logs and provide a complete and concise report.
#         #     Your report must contain two distinct sections:
#         #     1.  **Error Analysis:** In 1-2 sentences, clearly explain the root cause of the failure in plain language.
#         #     2.  **Suggested Fix:** Provide a specific, actionable code or configuration change to resolve the error. If possible, show the change with "before" and "after" code blocks.

#         #     ---
#         #     Logs:
#         #     {logs}
#         #     ---
#         # """)

#         prompt = ChatPromptTemplate.from_template(prompt_template)
        
#         # Define the output parser and the full chain
#         chain = prompt | llm | StrOutputParser()
        
#         # The .invoke() method runs the entire chain: prompt -> llm -> output_parser
#         # Truncate logs to avoid exceeding token limits and focus on the most recent events.
#         analysis = chain.invoke({"logs": logs[-8000:]}) 
#         return analysis
#     except Exception as e:
#         print(f"Error calling LangChain chain: {e}")
#         return f"Error connecting to the analysis service: {e}"

# def send_to_teams(card: dict):
#     """Sends a formatted Adaptive Card to the configured MS Teams webhook."""
#     if not TEAMS_WEBHOOK_URL:
#         print("ERROR: TEAMS_WEBHOOK_URL is not configured. Cannot send notification.")
#         return

#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "type": "message",
#         "attachments": [
#             {
#                 "contentType": "application/vnd.microsoft.card.adaptive",
#                 "content": card
#             }
#         ]
#     }
    
#     try:
#         response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
#         response.raise_for_status()
#         print(f"Successfully sent message to Teams. Status: {response.status_code}")
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to send message to Teams: {e}")
#         print(f"Response Body: {e.response.text if e.response else 'No response'}")

# def create_teams_failure_card(analysis_text):
#     """Creates the JSON for a failure Adaptive Card."""
#     return {
#         "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4",
#         "body": [
#             {"type": "TextBlock", "text": f"CI/CD Pipeline Failed: {PIPELINE_NAME}", "weight": "Bolder", "size": "Large", "color": "Attention"},
#             {"type": "FactSet", "facts": [{"title": "Status:", "value": "🔴 Failure"}, {"title": "Author:", "value": AUTHOR}, {"title": "Commit:", "value": COMMIT_SHA[:7]}], "spacing": "Medium"},
#             {"type": "TextBlock", "text": "**AI Error Analysis:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
#             {"type": "TextBlock", "text": analysis_text, "wrap": True, "spacing": "Small"}
#         ],
#         "actions": [{"type": "Action.OpenUrl", "title": "View Pipeline Run", "url": PIPELINE_URL}]
#     }

# def main():
#     """
#     Main function to read logs, get analysis, and send a notification.
#     """
#     if PIPELINE_STATUS != "failure":
#         print(f"Pipeline status is '{PIPELINE_STATUS}'. No failure analysis needed.")
#         return

#     print("Pipeline failed. Reading logs for analysis...")
    
#     # The GitHub Actions workflow will place logs in this file.
#     log_file_path = 'failure_logs.txt'
    
#     try:
#         with open(log_file_path, 'r') as f:
#             logs = f.read()
        
#         if not logs:
#             analysis = "No logs were captured from the failed job."
#         else:
#             analysis = get_langchain_analysis(logs)
            
#         teams_card = create_teams_failure_card(analysis)
#         send_to_teams(teams_card)

#     except FileNotFoundError:
#         print(f"Error: Log file not found at '{log_file_path}'.")
#         analysis = "Log file was not found. Could not perform analysis."
#         teams_card = create_teams_failure_card(analysis)
#         send_to_teams(teams_card)
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")

# if __name__ == "__main__":
#     # Ensure critical environment variables are set
#     if not GOOGLE_API_KEY:
#         raise ValueError("GOOGLE_API_KEY environment variable not set.")
#     if not TEAMS_WEBHOOK_URL:
#         raise ValueError("TEAMS_WEBHOOK_URL environment variable not set.")
        
#     main()


# ----------------------------------------------------------------------------------------


# import os
# import json
# import requests
# import textwrap
# import argparse

# # --- LangChain Imports ---
# # Required: pip install langchain langchain-google-genai
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.output_parser import StrOutputParser

# # --- Configuration from Environment Variables ---
# # These will be set in the GitHub Actions workflow file.
# TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")
# GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# PIPELINE_STATUS = os.environ.get("PIPELINE_STATUS")
# PIPELINE_NAME = os.environ.get("PIPELINE_NAME", "N/A")
# PIPELINE_URL = os.environ.get("PIPELINE_URL", "#")
# COMMIT_SHA = os.environ.get("COMMIT_SHA", "N/A")
# AUTHOR = os.environ.get("AUTHOR", "N/A")

# def get_langchain_analysis(logs: str) -> str:
#     """
#     Invokes a LangChain chain to get a structured report containing
#     analysis, remediation, and a code fix.
#     """
#     try:
#         # This new prompt asks for three distinct sections with clear separators.
#         prompt_template = textwrap.dedent("""
#             You are an expert DevOps engineer and a senior software developer reviewing a failed CI/CD pipeline. Your task is to analyze the following logs and provide a complete and concise report.

#             Your report MUST be structured into exactly three sections, separated by '---ANALYSIS-BREAK---' and '---CODE-BREAK---'.

#             SECTION 1: ERROR ANALYSIS
#             In 1-2 sentences, clearly explain the root cause of the failure in plain language.

#             ---ANALYSIS-BREAK---

#             SECTION 2: REMEDIATION
#             In natural language, explain the steps required to fix the error.

#             ---CODE-BREAK---

#             SECTION 3: CODE FIX
#             Provide only the specific, actionable code or configuration snippet required to resolve the error. Do not include any explanatory text in this section. If possible, show the change with "before" and "after" code blocks.

#             ---
#             Logs:
#             {logs}
#             ---
#         """)
        
#         llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3, google_api_key=GOOGLE_API_KEY)
#         prompt = ChatPromptTemplate.from_template(prompt_template)
#         chain = prompt | llm | StrOutputParser()
        
#         analysis = chain.invoke({"logs": logs[-8000:]}) 
#         return analysis
#     except Exception as e:
#         print(f"Error calling LangChain chain: {e}")
#         return f"Error connecting to the analysis service: {e}"

# def send_to_teams(card: dict):
#     """Sends a formatted Adaptive Card to the configured MS Teams webhook."""
#     if not TEAMS_WEBHOOK_URL:
#         print("ERROR: TEAMS_WEBHOOK_URL is not configured. Cannot send notification.")
#         return

#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "type": "message",
#         "attachments": [
#             {
#                 "contentType": "application/vnd.microsoft.card.adaptive",
#                 "content": card
#             }
#         ]
#     }
    
#     try:
#         response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
#         response.raise_for_status()
#         print(f"Successfully sent message to Teams. Status: {response.status_code}")
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to send message to Teams: {e}")
#         print(f"Response Body: {e.response.text if e.response else 'No response'}")

# def create_teams_failure_card(error_analysis, remediation, code_fix):
#     """Creates the JSON for a failure Adaptive Card with separate sections."""
    
#     # Start with the base elements of the card
#     body_elements = [
#         {"type": "TextBlock", "text": f"CI/CD Pipeline Failed: {PIPELINE_NAME}", "weight": "Bolder", "size": "Large", "color": "Attention"},
#         {"type": "FactSet", "facts": [{"title": "Status:", "value": "🔴 Failure"}, {"title": "Author:", "value": AUTHOR}, {"title": "Commit:", "value": COMMIT_SHA[:7]}], "spacing": "Medium"},
#     ]

#     # Conditionally add each section to the card body if it exists
#     if error_analysis:
#         body_elements.extend([
#             {"type": "TextBlock", "text": "**Error Analysis:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
#             {"type": "TextBlock", "text": error_analysis, "wrap": True, "spacing": "Small"}
#         ])

#     if remediation:
#         body_elements.extend([
#             {"type": "TextBlock", "text": "**Remediation:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
#             {"type": "TextBlock", "text": remediation, "wrap": True, "spacing": "Small"}
#         ])

#     if code_fix:
#         body_elements.extend([
#             {"type": "TextBlock", "text": "**Code Fix:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
#             {"type": "TextBlock", "text": code_fix, "wrap": True, "spacing": "Small", "fontType": "Monospace"}
#         ])
    
#     return {
#         "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
#         "type": "AdaptiveCard",
#         "version": "1.4",
#         "body": body_elements,
#         "actions": [{"type": "Action.OpenUrl", "title": "View Pipeline Run", "url": PIPELINE_URL}]
#     }

# def main():
#     """
#     Main function to read logs, get analysis, and send a notification.
#     """
#     if PIPELINE_STATUS != "failure":
#         print(f"Pipeline status is '{PIPELINE_STATUS}'. No failure analysis needed.")
#         return

#     print("Pipeline failed. Reading logs for analysis...")
    
#     log_file_path = 'failure_logs.txt'
    
#     try:
#         with open(log_file_path, 'r') as f:
#             logs = f.read()
        
#         if not logs:
#             analysis = "No logs were captured from the failed job."
#             parts = [analysis, "", ""]
#         else:
#             full_response = get_langchain_analysis(logs)
#             # Parse the structured response
#             parts = full_response.split('---ANALYSIS-BREAK---')
#             error_analysis_raw = parts[0]
#             remediation_raw = ""
#             code_fix_raw = ""
#             if len(parts) > 1:
#                 remediation_parts = parts[1].split('---CODE-BREAK---')
#                 remediation_raw = remediation_parts[0]
#                 if len(remediation_parts) > 1:
#                     code_fix_raw = remediation_parts[1]

#         # Clean up each part and apply Teams-specific formatting
#         error_analysis = error_analysis_raw.replace("SECTION 1: ERROR ANALYSIS", "").strip().replace('\n', '  \n')
#         remediation = remediation_raw.replace("SECTION 2: REMEDIATION", "").strip().replace('\n', '  \n')
#         code_fix = code_fix_raw.replace("SECTION 3: CODE FIX", "").strip().replace('\n', '  \n')
        
#         teams_card = create_teams_failure_card(error_analysis, remediation, code_fix)
#         send_to_teams(teams_card)

#     except FileNotFoundError:
#         print(f"Error: Log file not found at '{log_file_path}'.")
#         # Create a card even on local script error
#         teams_card = create_teams_failure_card("Log file was not found. Could not perform analysis.", "", "")
#         send_to_teams(teams_card)
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         teams_card = create_teams_failure_card(f"An unexpected error occurred in the notification script: {e}", "", "")
#         send_to_teams(teams_card)

# if __name__ == "__main__":
#     if not GOOGLE_API_KEY:
#         raise ValueError("GOOGLE_API_KEY environment variable not set.")
#     if not TEAMS_WEBHOOK_URL:
#         raise ValueError("TEAMS_WEBHOOK_URL environment variable not set.")
        
#     main()


# ------------------------------------------------------------------------------------------


import os
import json
import requests
import textwrap
import argparse

# --- LangChain Imports ---
# Required: pip install langchain langchain-google-genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# --- Configuration from Environment Variables ---
# These will be set in the GitHub Actions workflow file.
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
PIPELINE_STATUS = os.environ.get("PIPELINE_STATUS")
PIPELINE_NAME = os.environ.get("PIPELINE_NAME", "N/A")
PIPELINE_URL = os.environ.get("PIPELINE_URL", "#")
COMMIT_SHA = os.environ.get("COMMIT_SHA", "N/A")
AUTHOR = os.environ.get("AUTHOR", "N/A")

def get_langchain_analysis(logs: str) -> str:
    """
    Invokes a LangChain chain to get a structured report containing
    analysis, remediation, and a code fix.
    """
    try:
        # This new prompt asks for three distinct sections with clear separators.
        prompt_template = textwrap.dedent("""
            You are an expert DevOps engineer and a senior software developer reviewing a failed CI/CD pipeline. Your task is to analyze the following logs and provide a complete and concise report.

            Your report MUST be structured into exactly three sections, separated by '---ANALYSIS-BREAK---' and '---CODE-BREAK---'.

            SECTION 1: ERROR ANALYSIS
            In 1-2 sentences, clearly explain the root cause of the failure in plain language.

            ---ANALYSIS-BREAK---

            SECTION 2: REMEDIATION
            In natural language, explain the steps required to fix the error.

            ---CODE-BREAK---

            SECTION 3: CODE FIX
            Provide only the specific, actionable code or configuration snippet required to resolve the error. Do not include any explanatory text in this section. If possible, show the change with "before" and "after" code blocks.

            ---
            Logs:
            {logs}
            ---
        """)
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3, google_api_key=GOOGLE_API_KEY)
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm | StrOutputParser()
        
        analysis = chain.invoke({"logs": logs[-8000:]}) 
        return analysis
    except Exception as e:
        print(f"Error calling LangChain chain: {e}")
        return f"Error connecting to the analysis service: {e}"

def send_to_teams(card: dict):
    """Sends a formatted Adaptive Card to the configured MS Teams webhook."""
    if not TEAMS_WEBHOOK_URL:
        print("ERROR: TEAMS_WEBHOOK_URL is not configured. Cannot send notification.")
        return

    headers = {"Content-Type": "application/json"}
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card
            }
        ]
    }
    
    # --- DEBUGGING STEP ---
    print("\n--- DEBUG: Full JSON Payload being sent to Teams ---")
    print(json.dumps(payload, indent=2))
    print("--- END DEBUG ---\n")
    
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print(f"Successfully sent message to Teams. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Teams: {e}")
        print(f"Response Body: {e.response.text if e.response else 'No response'}")

def create_teams_failure_card(error_analysis, remediation, code_fix_display, raw_code_fix):
    """Creates the JSON for a failure Adaptive Card with separate sections and a copy button."""
    
    # Start with the base elements of the card body
    body_elements = [
        {"type": "TextBlock", "text": f"CI/CD Pipeline Failed: {PIPELINE_NAME}", "weight": "Bolder", "size": "Large", "color": "Attention"},
        {"type": "FactSet", "facts": [{"title": "Status:", "value": "🔴 Failure"}, {"title": "Author:", "value": AUTHOR}, {"title": "Commit:", "value": COMMIT_SHA[:7]}], "spacing": "Medium"},
    ]

    # Conditionally add each section to the card body if it exists
    if error_analysis:
        body_elements.extend([
            {"type": "TextBlock", "text": "**Error Analysis:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
            {"type": "TextBlock", "text": error_analysis, "wrap": True, "spacing": "Small"}
        ])

    if remediation:
        body_elements.extend([
            {"type": "TextBlock", "text": "**Remediation:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
            {"type": "TextBlock", "text": remediation, "wrap": True, "spacing": "Small"}
        ])

    if code_fix_display:
        body_elements.extend([
            {"type": "TextBlock", "text": "**Code Fix:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
            {"type": "TextBlock", "text": code_fix_display, "wrap": True, "spacing": "Small", "fontType": "Monospace"}
        ])
    
    # Start with the base actions
    actions = [{"type": "Action.OpenUrl", "title": "View Pipeline Run", "url": PIPELINE_URL}]

    # If there is a code fix, add a button to copy it to the clipboard.
    if raw_code_fix:
        actions.append({
            "type": "Action.CopyToClipboard",
            "title": "Copy Code Fix",
            "text": raw_code_fix # Use the raw, unformatted code here
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body_elements,
        "actions": actions
    }

def main():
    """
    Main function to read logs, get analysis, and send a notification.
    """
    if PIPELINE_STATUS != "failure":
        print(f"Pipeline status is '{PIPELINE_STATUS}'. No failure analysis needed.")
        return

    print("Pipeline failed. Reading logs for analysis...")
    
    log_file_path = 'failure_logs.txt'
    
    try:
        with open(log_file_path, 'r') as f:
            logs = f.read()
        
        if not logs:
            analysis = "No logs were captured from the failed job."
            parts = [analysis, "", ""]
        else:
            full_response = get_langchain_analysis(logs)
            
            # --- DEBUGGING STEP ---
            print("\n--- DEBUG: Raw LLM Response ---")
            print(full_response)
            print("--- END DEBUG ---\n")

            # Parse the structured response
            parts = full_response.split('---ANALYSIS-BREAK---')
            error_analysis_raw = parts[0]
            remediation_raw = ""
            code_fix_raw = ""
            if len(parts) > 1:
                remediation_parts = parts[1].split('---CODE-BREAK---')
                remediation_raw = remediation_parts[0]
                if len(remediation_parts) > 1:
                    code_fix_raw = remediation_parts[1]

        # Clean up each part for display and keep raw code for the copy button
        error_analysis_display = error_analysis_raw.replace("SECTION 1: ERROR ANALYSIS", "").strip().replace('\n', '  \n')
        remediation_display = remediation_raw.replace("SECTION 2: REMEDIATION", "").strip().replace('\n', '  \n')
        code_fix_display = code_fix_raw.replace("SECTION 3: CODE FIX", "").strip().replace('\n', '  \n')
        
        # Keep the raw, clean code fix for the copy-paste action
        raw_code_fix = code_fix_raw.replace("SECTION 3: CODE FIX", "").strip()
        
        # --- DEBUGGING STEP ---
        print("\n--- DEBUG: Parsed Content ---")
        print(f"Analysis: {error_analysis_display}")
        print(f"Remediation: {remediation_display}")
        print(f"Code Fix (Display): {code_fix_display}")
        print(f"Code Fix (Raw): {raw_code_fix}")
        print("--- END DEBUG ---\n")

        teams_card = create_teams_failure_card(error_analysis_display, remediation_display, code_fix_display, raw_code_fix)
        send_to_teams(teams_card)

    except FileNotFoundError:
        print(f"Error: Log file not found at '{log_file_path}'.")
        teams_card = create_teams_failure_card("Log file was not found. Could not perform analysis.", "", "", "")
        send_to_teams(teams_card)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        teams_card = create_teams_failure_card(f"An unexpected error occurred in the notification script: {e}", "", "", "")
        send_to_teams(teams_card)

if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    if not TEAMS_WEBHOOK_URL:
        raise ValueError("TEAMS_WEBHOOK_URL environment variable not set.")
        
    main()
