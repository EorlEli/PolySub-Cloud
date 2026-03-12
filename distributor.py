import re

def distribute_translation(original_block, translated_text, is_vertical=False):
    if not translated_text:
        return []

    # 1. Get Total Duration
    start_seconds = parse_time(original_block[0]['start'])
    end_seconds = parse_time(original_block[-1]['end'])
    total_duration = end_seconds - start_seconds

    # --- HIGH DENSITY MODE DETECTION ---
    # If the user speaks very fast, we need to allow longer subtitles (e.g. 3 lines) 
    # to prevent rapid flashing of short text on screen.
    # 22 Characters Per Second is considered fast speech.
    char_count = len(translated_text)
    cps = char_count / total_duration if total_duration > 0 else 0
    is_high_density = cps > 22.0
    
    if is_vertical:
        max_chars_per_block = 50 if is_high_density else 35
        max_line_len = 20
    else:
        max_chars_per_block = 110 if is_high_density else 80
        max_line_len = 42

    print(f"   [DEBUG DISTRIBUTOR] Start: {start_seconds}s | End: {end_seconds}s | Dur: {total_duration}s")
    print(f"   [DEBUG DISTRIBUTOR] Char Count: {char_count} | CPS: {cps:.1f} | High Density: {is_high_density}")
    print(f"   [DEBUG DISTRIBUTOR] Text: {translated_text[:30]}...")

    # 2. SPLIT PHASE: Sentence -> Comma -> Space
    # We use a hierarchical splitting strategy
    raw_chunks = intelligent_split(translated_text, max_chars_per_block)
 
    #print(f"DEBUG: distribute_translation total_chars={len(translated_text)}")
    #print(f"DEBUG: raw_chunks count={len(raw_chunks)}")
    #for rc in raw_chunks:
    #    print(f"   -> Chunk ({len(rc)}): {rc[:20]}...")
    
    # 3. TIMING PHASE: Assign tentative times
    temp_segments = []
    total_chars = sum(len(c) for c in raw_chunks)
    current_time = start_seconds
    
    if total_chars == 0: return []

    for chunk in raw_chunks:
        # Calculate weight
        chunk_weight = len(chunk) / total_chars
        chunk_duration = total_duration * chunk_weight
        
        seg_start = current_time
        seg_end = current_time + chunk_duration
        
        temp_segments.append({
            "start_sec": seg_start,
            "end_sec": seg_end,
            "text": chunk.strip()
        })
        current_time = seg_end

    # 4. MERGE PHASE (The Fix for "The Stutter")
    # If a block is too short (< 1.5s) or text is too short (< 15 chars),
    # merge it with the next one to create a readable subtitle.
    merged_segments = merge_micro_segments(temp_segments, max_chars_per_block)

    # 5. FORMATTING PHASE
    final_segments = []
    
    # Calculate ideal line length. For high density (3 lines), we wrap at roughly ~42 chars per line (110 / 3 = ~36, using 42 is safe).
    # Standard is also 42 for 2 lines (max 80 chars).
    for seg in merged_segments:
        final_segments.append({
            "start": format_timestamp(seg["start_sec"]),
            "end": format_timestamp(seg["end_sec"]),
            "text": wrap_text(seg["text"], max_line=max_line_len, high_density=is_high_density)
        })

    return final_segments

# --- INTELLIGENT SPLITTER ---

def intelligent_split(text, max_len=80):
    """
    Splits text into chunks. 
    Priority 1: Split by Sentence Endings (. ? !)
    Priority 2: If sentence > max_len chars, Split by Comma
    Priority 3: If part > max_len chars, Split by Space
    """
    # 1. Split by Sentence
    sentences = re.split(r'(?<=[.?!])\s+', text)
    final_chunks = []
    
    for sent in sentences:
        if not sent.strip(): continue
        
        # 2. Check Length
        if len(sent) < max_len:
            final_chunks.append(sent)
            continue
            
        # 3. Split by Comma (Only if long)
        if ',' in sent:
            comma_parts = sent.split(',')
        else:
            # If there are no commas and it's > max_len, we MUST hard split it now
            final_chunks.extend(split_hard_by_space(sent, max_len))
            continue
            
        buffer = ""
        
        for i, part in enumerate(comma_parts):
            # Re-add comma
            suffix = "," if i < len(comma_parts) - 1 else ""
            fragment = part.strip() + suffix
            
            # Accumulate buffer
            if len(buffer) + len(fragment) < max_len: # Try to fill up to max chars
                buffer += " " + fragment
            else:
                # Flush buffer
                if buffer:
                    # Check if buffer is HUGE (because one comma segment was massive)
                    if len(buffer) > max_len:
                        final_chunks.extend(split_hard_by_space(buffer, max_len))
                    else:
                        final_chunks.append(buffer.strip())
                
                buffer = fragment
        
        if buffer:
            # Check if the leftover buffer is huge
            if len(buffer) > max_len:
                final_chunks.extend(split_hard_by_space(buffer, max_len))
            else:
                final_chunks.append(buffer.strip())
                
    return final_chunks

def split_hard_by_space(text, max_len=80):
    """
    Last resort: chop by words if > max_len chars.
    Uses balanced splitting instead of greedy filling.
    """
    return balanced_split_helper(text, max_len)

def balanced_split_helper(text, max_len):
    if len(text) <= max_len: 
        return [text]
    
    # Find midpoint
    mid = len(text) // 2
    
    # Range to search for spaces (try to stay central)
    search_radius = max(10, len(text) // 10) 
    
    # Find nearest space to midpoint
    # rfind search range is [start, end)
    # searches backwards from end.
    left_search_end = min(len(text), mid + search_radius)
    left = text.rfind(' ', 0, left_search_end)
    
    # find search starts at mid - radius
    right_search_start = max(0, mid - search_radius)
    right = text.find(' ', right_search_start)
    
    # Heuristic: Pick the one closer to mid
    split_idx = -1
    
    dist_left = abs(mid - left) if left != -1 else float('inf')
    dist_right = abs(mid - right) if right != -1 else float('inf')
    
    if left != -1 and dist_left <= dist_right:
        split_idx = left
    elif right != -1:
        split_idx = right
        
    # If standard search failed, expand search to whole string to find ANY space
    if split_idx == -1:
        # Just find central-most space in the whole string
        left = text.rfind(' ', 0, mid)
        right = text.find(' ', mid)
        dist_left = abs(mid - left) if left != -1 else float('inf')
        dist_right = abs(mid - right) if right != -1 else float('inf')
        if left != -1 and dist_left <= dist_right:
            split_idx = left
        elif right != -1:
            split_idx = right

    if split_idx == -1: 
        # No space found at all? Hard chop at mid.
        split_idx = mid
        return [text[:split_idx], text[split_idx:]]
        
    part1 = text[:split_idx].strip()
    part2 = text[split_idx+1:].strip()
    
    # Check if we made progress (avoid infinite recursion if space is at 0 or end)
    if not part1 or not part2:
         # Failed to split meaningfully. Hard chop.
         split_idx = mid
         return [text[:split_idx], text[split_idx:]]

    # Recursively split chunks
    return balanced_split_helper(part1, max_len) + balanced_split_helper(part2, max_len)



# --- THE MERGER (NEW) ---

def merge_micro_segments(segments, max_chars_per_block=80):
    """
    Iterates through segments. If one is too short, glues it to the next.
    Prevents 0.3s flashes.
    Enforces that merged segments do not exceed max_chars_per_block (approx 80 chars / 2 lines, or 110/3).
    """
    if not segments: return []
    
    refined = []
    current_seg = segments[0]
    
    for next_seg in segments[1:]:
        duration = current_seg["end_sec"] - current_seg["start_sec"]
        text_len = len(current_seg["text"])
        
        # Check next segment properties (Lookahead for widows)
        next_duration = next_seg["end_sec"] - next_seg["start_sec"]
        next_text_len = len(next_seg["text"])
        
        # MERGE CONDITION 1: Current is too short (and not end of sentence)
        current_too_short = (duration < 1.5 or text_len < 15)
        current_ends_sentence = current_seg["text"].endswith(('.', '?', '!'))
        
        # MERGE CONDITION 2: Next is a TINY widow (flash)
        # If the NEXT segment is < 1.0s, we should absorb it into CURRENT, 
        # even if CURRENT ends with a period. "Sentence end. Widow." -> One block.
        next_is_tiny_widow = next_duration < 1.0 or next_text_len < 10
        
        # Safety Check: Don't create giant blocks
        combined_len = len(current_seg["text"]) + len(next_seg["text"]) + 1
        will_be_too_long = combined_len > max_chars_per_block
        
        should_merge_current = (current_too_short and not current_ends_sentence)
        should_absorb_next = next_is_tiny_widow
        
        if (should_merge_current or should_absorb_next) and not will_be_too_long:
            # MERGE
            current_seg["end_sec"] = next_seg["end_sec"]
            current_seg["text"] += " " + next_seg["text"]
        else:
            # APPEND AND MOVE ON
            refined.append(current_seg)
            current_seg = next_seg
            
    refined.append(current_seg)
    return refined

# --- HELPERS ---

def wrap_text(text, max_line=42, high_density=False):
    """
    Wraps text to max_line.
    Standard mode: Ensures at most 2 balanced lines.
    High Density mode: Can split into 3 lines if text > max_line * 2.
    Uses textwrap for safety.
    """
    # 1. If it fits on one line, return it.
    if len(text) <= max_line:
        return text

    # 2. Try to split into balanced lines
    import textwrap
    
    # If the text is fundamentally too massive because greedy merging failed to constrain it, 
    # we force a hard cap. (e.g. A 200 char block should NOT be in one subtitle cue, it should have been 2 cues).
    # If we get here, textwrap will just do what it has to do, which might result in 4+ lines.
    # We will let textwrap handle it, but we log a warning locally.
    if len(text) > (max_line * 3):
        print(f"   [WARNING] Text extremely long for wrapping ({len(text)} chars). Wrapper will exceed 3 lines.")

    if high_density and len(text) > (max_line * 1.8):
        # We likely need 3 lines. 
        # Calculate optimal width for 3 lines to make them look balanced.
        optimal_width = max(20, (len(text) // 3) + 2)
        # Ensure optimal width doesn't exceed screen limits
        optimal_width = min(optimal_width, max_line)
        lines = textwrap.wrap(text, width=optimal_width)
        
        # Failsafe for long words (like Russian/German) that cause textwrap to cascade into 4+ lines
        if len(lines) > 3:
             # Force a literal 3-way balanced split
             return _force_balanced_split(text, 3)
             
        return "\n".join(lines)
    else:
        # Standard 2-line balancing (same as before, but delegated to textwrap logic for simplicity 
        # unless specifically needed to be middle-aligned). 
        # For strict 2-line balancing, the existing middle split is actually better:
        mid_point = len(text) // 2
        
        # Search for the best space to split on near the middle
        best_split = -1
        min_diff = 100
        
        # Look for spaces
        for i in range(len(text)):
            if text[i] == ' ':
                # How balanced would this split be?
                len_a = i
                len_b = len(text) - (i + 1)
                
                # Constraints: Both must be <= max_line
                if len_a <= max_line and len_b <= max_line:
                    diff = abs(len_a - len_b)
                    if diff < min_diff:
                        min_diff = diff
                        best_split = i
                        
        if best_split != -1:
             return text[:best_split] + '\n' + text[best_split+1:]

        # 3. Fallback: standard textwrap
        lines = textwrap.wrap(text, width=max_line)
        
        # Failsafe for long words avoiding 4+ lines on standard density
        if len(lines) > 2 and len(text) <= (max_line * 2):
            return _force_balanced_split(text, 2)
            
        return "\n".join(lines)

def _force_balanced_split(text, num_lines):
    """
    Forces text into N lines as evenly as possible using spaces, 
    ignoring `max_line` widths if words are too long.
    """
    words = text.split(' ')
    if not words: return text
    
    # Calculate ideal characters per line
    target_length = len(text) / num_lines
    
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        # If adding this word exceeds the target length, AND we have words in the current line,
        # AND we haven't reached the final line yet -> commit the line
        if current_length + len(word) > target_length and current_line and len(lines) < num_lines - 1:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1 # +1 for space
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return "\n".join(lines)

def parse_time(t_str):
    parts = t_str.replace(',', '.').split(':')
    if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
    return int(parts[0])*60 + float(parts[1])

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"