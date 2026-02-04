from matcher import find_matching_translation
from distributor import distribute_translation

def run_alignment_engine(blocks, full_target_text):
    """
    The Core Logic: Takes English VTT Blocks + Translated Text
    Returns: A list of aligned segment dictionaries.
    """
    pt_cursor = 0
    final_segments = []
    WINDOW_SIZE = 500  # Adjust if needed for Nano context limits

    print(f"   🚀 Starting Alignment Engine on {len(blocks)} blocks...")

    for i, block in enumerate(blocks):
        original_language_block_text = " ".join([l['text'] for l in block])
        print(f"[{i+1}/{len(blocks)}] Processing lines {block[0]['id']}-{block[-1]['id']}...")
        
        # --- STEP A: Window (With Rearview Mirror) ---
        overlap = 50
        window_start = max(0, pt_cursor - overlap)
        window_end = pt_cursor + WINDOW_SIZE
        target_language_window = full_target_text[window_start : window_end]

        # --- STEP B: Find Match ---
        # Note: find_matching_translation uses GPT-5-nano internally now
        matched_text = find_matching_translation(original_language_block_text, target_language_window)
        
        print(f"   [DEBUG] Block {i} Original: '{original_language_block_text[:30]}...'")
        print(f"   [DEBUG] Block {i} Matched : '{matched_text}'")
        with open("debug_engine.log", "a", encoding="utf-8") as log:
            log.write(f"BLOCK {i}:\nORG: {original_language_block_text}\nMATCH: {matched_text}\n\n")
        
        if not matched_text:
            print(f"   ⚠️ [Block {i+1}] No match found. Cursor at {pt_cursor}.")
            # Fallback: Force advance cursor to prevent stagnation.
            # Estimate length based on English length * 1.0 (rough heuristic for EN->PT)
            estimated_len = len(original_language_block_text)
            pt_cursor += estimated_len 
            matched_text = "" # Still empty for this block, but at least we move on.
        else:
            # --- STEP C: Update Cursor ---
            found_index = target_language_window.find(matched_text)
            
            # Anchor Logic (Optional Backup)
            if found_index == -1 and len(matched_text) > 20:
                anchor = matched_text[:20]
                if target_language_window.count(anchor) == 1:
                    found_index = target_language_window.find(anchor) # Fixed typo 'pt_window' -> 'target_language_window'

            if found_index != -1:
                absolute_end = window_start + found_index + len(matched_text)
                pt_cursor = absolute_end
            else:
                print(f"   ⚠️ [Block {i+1}] Match text returned by AI not found in window.")
                # Fallback: Assume we actally found it but couldn't locate string. 
                # Advance cursor by length of hypothetical match.
                pt_cursor += len(matched_text)

        # --- STEP D: Distribute Lines ---
        # distribute_translation uses GPT-5-nano internally now
        new_segments = distribute_translation(block, matched_text)
        final_segments.extend(new_segments)

    return final_segments