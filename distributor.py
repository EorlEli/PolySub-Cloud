import re

def distribute_translation(original_block, translated_text):
    if not translated_text:
        return []

    # 1. Get Total Duration
    start_seconds = parse_time(original_block[0]['start'])
    end_seconds = parse_time(original_block[-1]['end'])
    total_duration = end_seconds - start_seconds

    # 2. SPLIT PHASE: Sentence -> Comma -> Space
    # We use a hierarchical splitting strategy
    raw_chunks = intelligent_split(translated_text)
    
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
    merged_segments = merge_micro_segments(temp_segments)

    # 5. FORMATTING PHASE
    final_segments = []
    for seg in merged_segments:
        final_segments.append({
            "start": format_timestamp(seg["start_sec"]),
            "end": format_timestamp(seg["end_sec"]),
            "text": wrap_text(seg["text"])
        })

    return final_segments

# --- INTELLIGENT SPLITTER ---

def intelligent_split(text):
    """
    Splits text into chunks. 
    Priority 1: Split by Sentence Endings (. ? !)
    Priority 2: If sentence > 80 chars, Split by Comma
    Priority 3: If part > 80 chars, Split by Space
    """
    # 1. Split by Sentence
    sentences = re.split(r'(?<=[.?!])\s+', text)
    final_chunks = []
    
    for sent in sentences:
        if not sent.strip(): continue
        
        # 2. Check Length
        if len(sent) < 80:
            final_chunks.append(sent)
            continue
            
        # 3. Split by Comma (Only if long)
        comma_parts = sent.split(',')
        buffer = ""
        
        for i, part in enumerate(comma_parts):
            # Re-add comma
            suffix = "," if i < len(comma_parts) - 1 else ""
            fragment = part.strip() + suffix
            
            # Accumulate buffer until it's substantial
            if len(buffer) + len(fragment) < 40:
                buffer += " " + fragment
            else:
                if buffer: final_chunks.append(buffer.strip())
                buffer = fragment
        
        if buffer:
            # Check if the leftover buffer is huge
            if len(buffer) > 80:
                # Force split by space
                final_chunks.extend(split_hard_by_space(buffer))
            else:
                final_chunks.append(buffer.strip())
                
    return final_chunks

def split_hard_by_space(text):
    """Last resort: chop by words if > 80 chars."""
    words = text.split()
    chunks = []
    current = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) > 80:
            chunks.append(" ".join(current))
            current = [w]
            curr_len = len(w)
        else:
            current.append(w)
            curr_len += len(w) + 1
    if current: chunks.append(" ".join(current))
    return chunks

# --- THE MERGER (NEW) ---

def merge_micro_segments(segments):
    """
    Iterates through segments. If one is too short, glues it to the next.
    Prevents 0.3s flashes.
    """
    if not segments: return []
    
    refined = []
    current_seg = segments[0]
    
    for next_seg in segments[1:]:
        duration = current_seg["end_sec"] - current_seg["start_sec"]
        text_len = len(current_seg["text"])
        
        # MERGE CONDITION:
        # Duration < 1.5s  OR  Text < 15 chars (unless it ends with a period)
        is_too_short = duration < 1.5 or text_len < 15
        is_end_of_sentence = current_seg["text"].endswith(('.', '?', '!'))
        
        if is_too_short and not is_end_of_sentence:
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

def wrap_text(text, max_line=42):
    if len(text) <= max_line: return text
    mid = len(text) // 2
    left = text.rfind(' ', 0, mid + 10)
    right = text.find(' ', mid - 10)
    split = left if (left != -1 and (right == -1 or mid-left < right-mid)) else right
    if split != -1: return text[:split] + '\n' + text[split+1:]
    return text

def parse_time(t_str):
    parts = t_str.replace(',', '.').split(':')
    if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
    return int(parts[0])*60 + float(parts[1])

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"