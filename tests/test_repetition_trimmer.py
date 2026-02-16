
import re

def trim_repeated_suffix_v2(source_text, match_text):
    if not match_text or not source_text:
        return match_text
        
    def normalize(s):
        return re.sub(r'[^\w]', '', s).lower()

    # 1. Detect repetition in MATCH
    # We check for a suffix S such that match_text ends with S + sep + S
    # where sep is non-word chars.
    
    # Iterate lengths from largest to smallest
    n = len(match_text)
    # Check sequences of length > 3
    for length in range(n // 2, 3, -1):
        suffix = match_text[-length:]
        
        # KEY FIX: Ensure suffix starts with a word boundary to avoid "eating" the separator of the previous part.
        # If suffix starts with ' ' or '?', we might strip it effectively removing the punctuation of the *first* part.
        # We allow starting with quotes or inverted punctuation.
        if not suffix[0].isalnum() and suffix[0] not in ['"', "'", "“", "”", "¿", "¡"]:
            continue
            
        # The remainder is everything before the final suffix
        remainder = match_text[:-length]
        
        # Check if remainder ends with the same CONTENT as suffix
        # We allow for minor punctuation differences, so we normalize.
        # But we need to be careful: "posso ir?" vs "posso ir? " -> diff is space.
        
        norm_suffix = normalize(suffix)
        norm_remainder = normalize(remainder)
        
        if not norm_suffix: continue
        
        if norm_remainder.endswith(norm_suffix):
            # Found a repeat!
            # Pattern: [Prefix] [Repeat1] [Matches Suffix Content]
            
            # The "Repeat1" ends at the end of remainder.
            # We want to keep [Prefix] [Repeat1].
            # We want to discard [Matches Suffix Content] (the actual suffix string).
            
            # BUT: We need to check the Source.
            # Does the Source end with a similar repetition?
            
            # Heuristic:
            # If Source ends with Repeat + Repeat?
            # It's hard to know what "Repeat" is in Source language.
            
            # Use Length Ratio + Repetition Check
            # If source length is short relative to the repeated match (indicating single instance)
            
            # Length of repeated part in chars:
            repeat_len = len(suffix)
            
            # Source length vs Match length
            # "Can I go in?" (12) vs "posso ir? posso ir?" (21).
            # If we trim one "posso ir?", we get ~10. -> 12 vs 10 is good.
            # If we keep both -> 12 vs 21 is ~1.75x ratio.
            
            # "Bye bye" (7) vs "Xau xau" (7).
            
            # Calculate Candidate (Trimmed)
            candidate = match_text[:-length].strip()
            
            len_src = len(source_text)
            len_orig = len(match_text)
            len_cand = len(candidate)
            
            ratio_orig = len_orig / len_src if len_src > 0 else 0
            ratio_cand = len_cand / len_src if len_src > 0 else 0
            
            diff_orig = abs(ratio_orig - 1.3)
            diff_cand = abs(ratio_cand - 1.3)
            
            # Special check for very short sources ("Bye bye")
            if len_src < 5: continue

            if diff_cand < diff_orig:
                 # Trimming improves length ratio.
                 print(f"   ✂️ REPETITION TRIM: Detected '{suffix}' repeated. Trimming improves ratio ({ratio_orig:.2f} -> {ratio_cand:.2f}).")
                 return candidate
            else:
                 print(f"   ⚠️ REPETITION DETECTED but preserved: Trimming worsens ratio ({ratio_orig:.2f} -> {ratio_cand:.2f}). Source might repeat too.")
            
            # If we found a match but decided not to trim, we break? 
            # Or continue searching for smaller repeats?
            # Probably break, largest repeat is most significant.
            return match_text
            
    return match_text

# --- TEST CASES ---
cases = [
    (
        "Can I go in?", 
        "ya, posso ir? posso ir?",
        "ya, posso ir?" # Expected
    ),
    (
        "Bye bye.",
        "Xau xau.",
        "Xau xau." # Expected (Source repeats too, logic should preserve)
    ),
    (
        "I just this was like the the meme.",
        "Esto era como el meme, ¿no?",
        "Esto era como el meme, ¿no?" # Logic shouldn't trigger
    ),
    (
       "Can I go in?",
       "ya, posso ir?    posso ir?", # Whitespace test
       "ya, posso ir?"
    )
]

print("Running Tests...\n")
for src, mtch, expected in cases:
    res = trim_repeated_suffix_v2(src, mtch)
    print(f"SRC: '{src}'")
    print(f"IN : '{mtch}'")
    print(f"OUT: '{res}'")
    if res == expected: print("✅ PASS")
    else: print(f"❌ FAIL (Expected '{expected}')")
    print("-" * 20)
