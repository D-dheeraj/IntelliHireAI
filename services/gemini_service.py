import os
import time
import random
import re
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError


load_dotenv(override=True)


_client = None


def get_gemini_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Try to get from Streamlit secrets
            try:
                import streamlit as st
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Please add it to your .env file locally "
                "or configure it in Streamlit Cloud Secrets."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def ask_gemini(prompt):
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    max_retries = 7
    base_delay = 2.0

    try:
        api_client = get_gemini_client()
    except ValueError as e:
        print(f"[Error] {e}")
        raise e

    for attempt in range(max_retries):
        try:
            response = api_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except APIError as e:
            # retry on rate limit (429) or anything 5xx
            is_retryable = (e.code == 429) or (e.code is not None and 500 <= e.code < 600)
            if is_retryable and attempt < max_retries - 1:
                # gemini sometimes tells you exactly how long to wait - use that if available
                match = re.search(r"Please retry in (\d+\.?\d*)s", str(e))
                if match:
                    delay = float(match.group(1)) + 1.0
                    print(f"[Warning] Rate limit hit. Sleeping for {delay:.2f}s as requested by Gemini API...")
                else:
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                    print(f"[Warning] Gemini API error {e.code} ({e.status}) on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                print(f"[Error] Gemini API request failed with APIError: {e}")
                raise e
        except Exception as e:
            # catches stuff like network timeouts, not just API errors
            if attempt < max_retries - 1:
                delay = (base_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                print(f"[Warning] Network error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                print(f"[Error] Request failed after {attempt + 1} attempts with exception: {e}")
                raise e