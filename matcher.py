import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_matching_translation(original_language_block_text, target_language_search_window, context_preview="", next_block_text=""):
    """
    Finds the exact target language substring corresponding to the original language text.
    Retries automatically if the AI returns an empty result.
    
    Args:
        original_language_block_text: The source text block.
        target_language_search_window: The target text to search within (starting from current cursor).
        context_preview: The text immediately preceding the search window (for context only).
        next_block_text: The text of the NEXT source block. Used as a negative constraint (STOP here).
    """
    
    # 1. THE ROBUST PROMPT
    # We explicitly tell the AI about the "Sliding Window" artifacts (broken words).
    system_prompt = """
    You are a Translation Matcher.
    INPUT: An original language text segment, a target language search window, and previous context.
    TASK: Identify the target language text segment WITHIN THE SEARCH WINDOW that corresponds to the original language input.
    
    CRITICAL RULES:
    1. CONTEXT AWARENESS: The prompt includes "Context (Previous Translation)". Do NOT match text inside the Context block. Only match text inside the "Search Window".
    2. KEY INSTRUCTION: DO NOT ignore text at the start of the search window. If the original language input corresponds to the text at the very beginning of the search window (even if it looks like a fragment), YOU MUST MATCH IT.
    3. PARTIAL MATCHING: The original language input is often just a fragment of a sentence. You must find the corresponding target fragment. Do NOT look for a "complete sentence" if the translation of the original language input has been satisfied
    4. QUOTE INDEPENDENCE: If the target text has quotes that wrap multiple sentences, but the source text only corresponds to one of them, YOU MUST BREAK THE QUOTE. Do not include the closing quote if it belongs to a later sentence.
    5. LENGTH CHECK: Do not include subsequent sentences or text that is not visually present in the source input.
    6. NEGATIVE CONSTRAINT: You are provided with the "Next Source Segment". You MUST STOP matching BEFORE the translation of this next segment begins. Do not include any part of the translation that corresponds to the next source segment.
       - SPECIAL CASE: If the "Next Source Segment" is a short question or phrase (e.g., "Right?", "No?", "Okay?"), and the translation window contains its corresponding translation (e.g., "¿no?", "¿verdad?", "¿vale?"), YOU MUST EXCLUDE IT from the current match.
       - REPEATED TEXT: If the next source segment is a repeat of the end of the current segment, STOP before the repetition begins in the translation.
    7. EXACT EXTRACT: Extract the substring EXACTLY as it appears in the target language text. Do NOT add closing quotes or punctuation that is not present in the window at that exact position.
    8. JSON OUTPUT: { "target_language_substring": "..." }
    """

    user_prompt = f"""
    --- CONTEXT (PREVIOUS TRANSLATION - DO NOT MATCH HERE) ---
    ...{context_preview}

    --- ORIGINAL LANGUAGE SEGMENT (MATCH THIS) ---
    {original_language_block_text}
    
    --- NEXT SOURCE SEGMENT (DO NOT MATCH) ---
    {next_block_text}

    --- TARGET LANGUAGE SEARCH WINDOW (SEARCH HERE) ---
    {target_language_search_window}
    """

    current_model = "gpt-5.2"
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
            if matched_text not in target_language_search_window:
                # Try stripping trailing quotes/punctuation
                stripped = matched_text.strip('"').strip("'").strip()
                if stripped in target_language_search_window:
                    # print(f"   🔧 Fixed hallucinated quotes: '{matched_text}' -> '{stripped}'")
                    matched_text = stripped
                else:
                    # Try stripping just the last character (common for single hallucinated punct like " or .)
                    if matched_text[:-1] in target_language_search_window:
                         matched_text = matched_text[:-1]

            # --- HEURISTIC WATCHDOG (NEW) ---
            # Protection against "Colon Merges" or "Run-on Matches"
            matched_text = heuristic_trim_match(original_language_block_text, matched_text)

            return matched_text

        except Exception as e:
            print(f"   ⚠️ Matcher Error (Attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return ""
            time.sleep(1) # Small pause before retry

    return ""

def heuristic_trim_match(source_text, match_text):
    """
    Safeguard: If the match is suspiciously long (> 2x source) and contains splitters (like : or .),
    we programmatically check if splitting it yields a better length ratio.
    """
    if not source_text or not match_text:
        return match_text

    src_len = len(source_text)
    match_len = len(match_text)
    
    # Only apply to non-trivial sentences (short words might have long translations naturally)
    if src_len < 10:
        return match_text
        
    ratio = match_len / src_len
    
    # If match is > 1.5x length of source, suspect a merge.
    # (Target languages are usually ~1.2-1.4x Source, so 1.5 is a tight but safe upper bound for "suspicious")
    if ratio > 1.5:
        # Check for strong splitters
        # We look for sentence-ending or clause-breaking punctuation
        splitters = [':', '.', ';', '—', ' – ', ' - '] 
        
        best_candidate = match_text
        best_diff = abs(ratio - 1.3) # Target a theoretical 1.3x ratio
        was_trimmed = False
        
        for punct in splitters:
            if punct in match_text:
                # Try splitting by the FIRST occurrence of the splitter
                parts = match_text.split(punct)
                if len(parts) > 1:
                    candidate = parts[0].strip() + punct # Keep the punctuation? Usually yes.
                    # Actually, if we split by colon, the colon might be part of the first sentence.
                    # "Label: content". If source is "Label", match should be "Label:"? 
                    # Or "Label". Let's keep it consistent.
                    
                    cand_len = len(candidate)
                    if cand_len < 5: continue # Too short
                    
                    cand_ratio = cand_len / src_len
                    
                    # If this candidate is CLOSER to the ideal ratio (1.0 - 1.5 range)
                    # We penalize very short (<0.5) and very long (>2.0)
                    
                    # Simple check: Is the candidate ratio "better" than the original monster ratio?
                    # Original: 2.8. Candidate: 0.9.  0.9 is closer to 1.3 than 2.8.
                    
                    diff = abs(cand_ratio - 1.3)
                    if diff < best_diff:
                        best_candidate = candidate
                        best_diff = diff
                        was_trimmed = True
        
        if was_trimmed:
             print(f"   ✂️ WATCHDOG TRIMMED: '{match_text[:20]}...' -> '{best_candidate[:20]}...' (Ratio {ratio:.1f}->{len(best_candidate)/src_len:.1f})")
             return best_candidate
             
    return match_text

