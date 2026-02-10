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
        block_start = block[0]['start']
        block_end = block[-1]['end']
        print(f"[{i+1}/{len(blocks)}] Processing lines {block[0]['id']}-{block[-1]['id']} ({block_start}->{block_end})...")
        
        # --- STEP A: Window and Context ---
        CONTEXT_SIZE = 100
        search_window_start = pt_cursor
        search_window_end = min(len(full_target_text), pt_cursor + WINDOW_SIZE)
        
        # Context looks backwards from cursor
        context_start = max(0, pt_cursor - CONTEXT_SIZE)
        context_preview = full_target_text[context_start : pt_cursor]
        
        target_language_search_window = full_target_text[search_window_start : search_window_end]
        
        # --- STEP B: Find Match ---
        # Look ahead for Negative Constraint
        next_block_text = ""
        if i + 1 < len(blocks):
            next_block_text = " ".join([l['text'] for l in blocks[i+1]])

        matched_text = find_matching_translation(original_language_block_text, target_language_search_window, context_preview, next_block_text)
        
        print(f"   [DEBUG_ENGINE] Block {i} Input: '{original_language_block_text[:30]}...'")
        print(f"   [DEBUG_ENGINE] Block {i} Match: '{matched_text}'")
        with open("debug_engine.log", "a", encoding="utf-8") as log:
            log.write(f"BLOCK {i} ({block_start} -> {block_end}):\nORG: {original_language_block_text}\nMATCH: {matched_text}\n\n")
        
        if not matched_text:
            print(f"   ⚠️ [Block {i+1}] No match found. Cursor at {pt_cursor}.")
            # Fallback: Force advance cursor to prevent stagnation.
            estimated_len = len(original_language_block_text)
            pt_cursor += estimated_len 
            matched_text = "" 
        else:
            # --- STEP C: Update Cursor ---
            # Search specifically in the SEARCH WINDOW
            found_index = target_language_search_window.find(matched_text)
            
            if found_index != -1:
                # Found strictly inside the search window (ahead of cursor)
                absolute_start = search_window_start + found_index
                absolute_end = absolute_start + len(matched_text)
                
                # Jump to the end of the match
                pt_cursor = absolute_end
            else:
                print(f"   ⚠️ [Block {i+1}] Match text returned by AI not found in search window.")
                pt_cursor += len(matched_text)

        # --- STEP D: Distribute Lines ---
        # distribute_translation uses GPT-5-nano internally now
        new_segments = distribute_translation(block, matched_text)
        final_segments.extend(new_segments)

    return final_segments