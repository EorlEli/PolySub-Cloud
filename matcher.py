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
    3. PARTIAL MATCHING: The original language input is often just a fragment of a sentence. You must find the corresponding target fragment. Do NOT look for a "complete sentence" if the translation of the original lnaguage input has been satisfied
    4. QUOTE INDEPENDENCE: If the target text has quotes that wrap multiple sentences, but the source text only corresponds to one of them, YOU MUST BREAK THE QUOTE. Do not include the closing quote if it belongs to a later sentence.
    5. LENGTH CHECK: Do not include subsequent sentences or text that is not visually present in the source input.
    6. EXACT EXTRACT: Extract the substring EXACTLY as it appears in the target language text. Do NOT add closing quotes or punctuation that is not present in the window at that exact position.
    7. JSON OUTPUT: { "target_language_substring": "..." }
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

            # --- PROGRAMMATIC VERIFICATION ---
            # If the specific text isn't found in the window, it might be a hallucination (e.g. added quote).
            if matched_text not in target_language_window_text:
                # Try stripping trailing quotes/punctuation
                stripped = matched_text.strip('"').strip("'").strip()
                if stripped in target_language_window_text:
                    # print(f"   🔧 Fixed hallucinated quotes: '{matched_text}' -> '{stripped}'")
                    matched_text = stripped
                else:
                    # Try stripping just the last character (common for single hallucinated punct like " or .)
                    if matched_text[:-1] in target_language_window_text:
                         matched_text = matched_text[:-1]

            return matched_text

        except Exception as e:
            print(f"   ⚠️ Matcher Error (Attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return ""
            time.sleep(1) # Small pause before retry

    return ""

