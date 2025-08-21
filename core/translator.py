# slide_translator/translator.py
import os
import openai
import json
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def translate_text_batch(
    texts: Dict[str, str], 
    target_language: str, 
    source_language: str = "auto"
) -> Dict[str, str]:
    """
    Translates a dictionary of texts using their unique IDs as keys.
    Uses the OpenAI API's JSON mode for robust and reliable structured data exchange.

    Args:
        texts: A dictionary of {run_id: text_to_translate}.
        target_language: The language to translate the texts into.
        source_language: The source language of the texts. Defaults to "auto".

    Returns:
        A dictionary of {run_id: translated_text}.
        
    Raises:
        ValueError: If the OpenAI API key is not found or if the API response is malformed.
        Exception: For other API errors.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    openai.api_key = api_key

    if not texts:
        return {}

    system_prompt = f"""You are a highly precise translation engine specialized in business presentations.
You will be given a JSON object where keys are unique identifiers and values are texts with special formatting markers.
The formatting markers are: <BOLD_START>, <BOLD_END>, <ITALIC_START>, <ITALIC_END>
CRITICAL: You MUST preserve these markers exactly in their relative positions in the translated text.
Translate EVERY SINGLE WORD from '{source_language}' to '{target_language}', but keep the formatting markers in appropriate positions.
Your response MUST be a single, valid JSON object with the exact same keys as the input.
Each translated value should maintain the formatting markers around the corresponding translated words.
Do not add any extra commentary, explanations, or greetings. Only the JSON object is allowed.

Example: 
Input: "This is <BOLD_START>important<BOLD_END> text"
Output: "Este é um texto <BOLD_START>importante<BOLD_END>" (if translating to Portuguese)"""

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(texts)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        response_content = response.choices[0].message.content
        if not response_content:
            raise ValueError("API returned an empty response.")

        # Parse the JSON response from the API
        translated_json = json.loads(response_content)

        # Basic validation: check if the response is a dictionary
        if not isinstance(translated_json, dict):
            raise ValueError("API response was not a JSON object (dictionary).")

        return translated_json

    except json.JSONDecodeError:
        raise ValueError("Failed to decode JSON from API response. The response was not valid JSON.")
    except Exception as e:
        print(f"An error occurred during translation: {e}")
        raise
