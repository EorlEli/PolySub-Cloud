import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_matching_translation(original_language_block_text, target_language_window_text):
    """
    Finds the exact target language substring corresponding to the original language text.
    Retries automatically if the AI returns an empty result.
    """
    
    # 1. THE ROBUST PROMPT
    # We explicitly tell the AI about the "Sliding Window" artifacts (broken words).
    system_prompt = """
    You are a Translation Matcher.
    INPUT: An original language text segment and a target language text window.
    TASK: Identify the target language text segment that corresponds to the original language input.
    
    CRITICAL RULES:
    1. CONTEXT AWARENESS: The target language text is a "sliding window". It may start in the middle of a word or sentence.
    2. KEY INSTRUCTION: DO NOT ignore text at the start of the window. If the original language input corresponds to the text at the very beginning of the window (even if it looks like a fragment), YOU MUST MATCH IT.
    3. PARTIAL MATCHING: The original language input is often just a fragment of a sentence. You must find the corresponding target fragment. Do NOT look for a "complete sentence" if the input is only a clause.
    4. FULL COVERAGE: If the input requires it, select across multiple sentences.
    5. EXACT EXTRACT: Extract the substring EXACTLY as it appears in the target language text. No corrections.
    6. JSON OUTPUT: { "target_language_substring": "..." }
    """

    user_prompt = f"""
    --- ORIGINAL LANGUAGE SEGMENT ---
    {original_language_block_text}

    --- TARGET LANGUAGE WINDOW (Search here) ---
    {target_language_window_text}
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
            matched_text = result_json.get("target_language_substring", "")

            # RETRY LOGIC: If AI returns empty string, try again.
            if not matched_text.strip():
                debug_trap = True
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

