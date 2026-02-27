from matcher import find_matching_translation
from distributor import distribute_translation

def run_alignment_engine(blocks, full_target_text):
    """
    The Core Logic: Takes Source VTT Blocks + Translated Text
    Returns: A list of aligned segment dictionaries.
    """
    pt_cursor = 0
    final_segments = []
    WINDOW_SIZE = 500  # Adjust if needed for Nano context limits

    print(f"   🚀 Starting Alignment Engine on {len(blocks)} blocks...")
    i = 0
    while i < len(blocks):
        block = blocks[i]
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
        
        # --- PRE-VERIFY MATCH: PREVENT LARGE JUMPS ---
        if matched_text:
            found_idx = target_language_search_window.find(matched_text)
            # If the match skips too much text, it's likely a future occurrence of a repeated word.
            MAX_GAP = max(40, len(original_language_block_text) * 1.5)
            if found_idx > MAX_GAP:
                print(f"   ⚠️ [Block {i+1}] Match '{matched_text}' found but skips {found_idx} chars (Max allowed: {MAX_GAP}). Rejecting match to prevent misalignment.")
                matched_text = ""

        # --- NEW: MERGE RECOVERY STRATEGY ---
        if not matched_text and i + 1 < len(blocks):
            print(f"   ⚠️ [Block {i+1}] No match found. Attempting MERGE RECOVERY with next block...")
            merged_source_text = original_language_block_text + " " + next_block_text
            
            # Use block i+2 as the new negative constraint
            next_next_block_text = ""
            if i + 2 < len(blocks):
                 next_next_block_text = " ".join([l['text'] for l in blocks[i+2]])
                 
            # Try matching the merged block
            merged_match = find_matching_translation(merged_source_text, target_language_search_window, context_preview, next_next_block_text)
            
            if merged_match:
                 print(f"   ✅ [Block {i+1} + {i+2}] MERGE RECOVERY SUCCESSFUL. Found unified translation.")
                 block = block + blocks[i+1] # Combine the VTT lines
                 original_language_block_text = merged_source_text
                 matched_text = merged_match
                 # Skip the next block since we consumed it
                 i += 1 

        print(f"   [DEBUG_ENGINE] Block {i} Input: '{original_language_block_text[:30]}...'")
        print(f"   [DEBUG_ENGINE] Block {i} Match: '{matched_text}'")
        with open("debug_engine.log", "a", encoding="utf-8") as log:
            log.write(f"BLOCK {i} ({block_start} -> {block_end}):\nORG: {original_language_block_text}\nMATCH: {matched_text}\n\n")
        
        if not matched_text:
            print(f"   ⚠️ [Block {i+1}] No match found even after recovery. Cursor at {pt_cursor}.")
            
            # --- LOOKAHEAD RECOVERY ---
            recov = False
            if i + 1 < len(blocks):
                 next_block_txt = next_block_text 
                 
                 # Anchor Strategy: Find Block N+1 to recover Block N
                 print(f"   🔍 ANCHOR SEARCH: Looking for Block {i+2} to anchor mismatched Block {i+1}...")
                 peek_match = find_matching_translation(next_block_txt, target_language_search_window, "", "")
                 
                 if peek_match:
                     idx = target_language_search_window.find(peek_match)
                     if idx != -1: 
                         # Found the anchor!
                         # Everything from 0 to idx is the "Gap".
                         gap_text = target_language_search_window[:idx]
                         
                         print(f"   ⚓ ANCHOR FOUND: Block {i+2} starts at index {idx}.")
                         print(f"   ✨ Gap Filled: Assigning '{gap_text[:30]}...' to Block {i+1}.")
                         
                         pt_cursor += idx
                         matched_text = gap_text # Fallback to using the gap as the match
                         recov = True

            if not recov:
                # Original Fallback: Force advance cursor to prevent stagnation.
                estimated_len = len(original_language_block_text)
                print(f"   Fallback: Advancing cursor by {estimated_len}")
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
        
        i += 1

    return final_segments