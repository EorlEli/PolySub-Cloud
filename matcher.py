import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_matching_translation(english_block_text, pt_window_text):
    """
    Finds the exact Portuguese substring corresponding to the English text.
    Retries automatically if the AI returns an empty result.
    """
    
    # 1. THE ROBUST PROMPT
    # We explicitly tell the AI about the "Sliding Window" artifacts (broken words).
    system_prompt = """
    You are a Translation Matcher.
    INPUT: An English text segment and a Portuguese text window.
    TASK: Identify the Portuguese text segment that corresponds to the English input.
    
    CRITICAL RULES:
    1. CONTEXT AWARENESS: The Portuguese text is a "sliding window". It may start in the middle of a word (e.g., "ing to the store") or sentence. IGNORE any broken fragments at the very beginning of the window. Look for the first COMPLETE sentence that matches the meaning.
    2. FLEXIBILITY: The translation may be non-literal, inverted, or missing small emphasis words. Match based on MEANING.
    3. EXACT EXTRACT: Once you locate the matching segment, extract the substring EXACTLY as it appears in the Portuguese text. Do not correct typos, punctuation, or grammar. Copy it byte-for-byte.
    4. BOUNDARIES: Do not include text from the next sentence.
    5. JSON OUTPUT: { "portuguese_substring": "..." }
    """

    user_prompt = f"""
    --- ENGLISH SEGMENT ---
    {english_block_text}

    --- PORTUGUESE WINDOW (Search here) ---
    {pt_window_text}
    """

    current_model = "gpt-5-nano"
    max_retries = 3

    for attempt in range(max_retries):
        
        # --- TRACE START ---
        start_time = time.perf_counter()

        try:
            # print(f"   >>> [DEBUG MATCHER] Attempt {attempt+1}/{max_retries}")
            
            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                response_format={"type": "json_object"}
            )
            
            # --- TRACE LOG ---
            log_openai_usage(f"MATCHER-Try{attempt+1}", start_time, response)

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from API")
                
            result_json = json.loads(content)
            matched_text = result_json.get("portuguese_substring", "")

            # RETRY LOGIC: If AI returns empty string, try again.
            if not matched_text.strip():
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Matcher returned empty string. Retrying... ({attempt+1}/{max_retries})")
                    continue # Try again
                else:
                    print(f"   ❌ Matcher failed to find text after {max_retries} attempts.")
                    return ""

            return matched_text

        except Exception as e:
            print(f"   ⚠️ Matcher Error (Attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return ""
            time.sleep(1) # Small pause before retry

    return ""

