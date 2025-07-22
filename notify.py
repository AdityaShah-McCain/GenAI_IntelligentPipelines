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
    Invokes a LangChain chain to get a concise, natural-language
    explanation of the error from the provided logs.
    """
    try:
        # --- THIS PROMPT IS UPDATED ---
        # It now explicitly tells the LLM to avoid Markdown fences and use indentation.
        prompt_template = textwrap.dedent("""
            You are an expert DevOps engineer and a senior software developer reviewing a failed CI/CD pipeline. Your task is to analyze the following logs and provide a complete and concise report.

            Your report must contain two distinct sections:

            1.  **Error Analysis:** In 1-2 sentences, clearly explain the root cause of the failure in plain language.
            2.  **Suggested Fix:** Provide a specific, actionable code or configuration change to resolve the error. **IMPORTANT: Do not use Markdown code fences (```). Instead, format any code by indenting each line with four spaces.**

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
    
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print(f"Successfully sent message to Teams. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Teams: {e}")
        print(f"Response Body: {e.response.text if e.response else 'No response'}")

def create_teams_failure_card(analysis_text):
    """Creates the JSON for a failure Adaptive Card."""
    return {
        "$schema": "[http://adaptivecards.io/schemas/adaptive-card.json](http://adaptivecards.io/schemas/adaptive-card.json)", "type": "AdaptiveCard", "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": f"CI/CD Pipeline Failed: {PIPELINE_NAME}", "weight": "Bolder", "size": "Large", "color": "Attention"},
            {"type": "FactSet", "facts": [{"title": "Status:", "value": "🔴 Failure"}, {"title": "Author:", "value": AUTHOR}, {"title": "Commit:", "value": COMMIT_SHA[:7]}], "spacing": "Medium"},
            {"type": "TextBlock", "text": "**AI Error Analysis:**", "wrap": True, "size": "Medium", "weight": "Bolder"},
            {"type": "TextBlock", "text": analysis_text, "wrap": True, "spacing": "Small", "fontType": "Monospace"}
        ],
        "actions": [{"type": "Action.OpenUrl", "title": "View Pipeline Run", "url": PIPELINE_URL}]
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
        else:
            analysis = get_langchain_analysis(logs)
            
        # Replace every newline with '  \n' to force a hard line break in Teams.
        teams_compatible_analysis = analysis.replace('\n', '  \n')
        
        teams_card = create_teams_failure_card(teams_compatible_analysis)
        send_to_teams(teams_card)

    except FileNotFoundError:
        print(f"Error: Log file not found at '{log_file_path}'.")
        analysis = "Log file was not found. Could not perform analysis."
        teams_card = create_teams_failure_card(analysis)
        send_to_teams(teams_card)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    if not TEAMS_WEBHOOK_URL:
        raise ValueError("TEAMS_WEBHOOK_URL environment variable not set.")
        
    main()
