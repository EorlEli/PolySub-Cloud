import re

def parse_vtt_time(timestamp):
    parts = timestamp.replace(',', '.').split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h)*3600 + int(m)*60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m)*60 + float(s)
    return 0.0

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"

def split_whisper_segment(segment):
    """
    CRITICAL FIX: Whisper often puts two sentences in one line:
    "bubble. But beneath..."
    This function splits that into two events:
    1. "bubble."
    2. "But beneath..."
    So that the grouping logic can correctly see the period.
    """
    text = segment['text']
    # If no punctuation in the middle, just return as is
    if '.' not in text and '?' not in text and '!' not in text:
        return [segment]
        
    start = parse_vtt_time(segment['start'])
    end = parse_vtt_time(segment['end'])
    duration = end - start
    
    # Split by punctuation followed by space
    # The regex (?<=[.?!]) keeps the punctuation attached to the left part
    raw_parts = re.split(r'(?<=[.?!])\s+', text)
    
    # MERGE STEP: Re-join parts that were split incorrectly (at abbreviations)
    parts = []
    if raw_parts:
        current_part = raw_parts[0]
        for next_part in raw_parts[1:]:
            # If current_part ends in an abbreviation (like "M."), join with next
            if is_abbreviation(current_part):
                current_part += " " + next_part
            else:
                parts.append(current_part)
                current_part = next_part
        parts.append(current_part)

    if len(parts) <= 1:
        return [segment]
    
    # Re-calculate timestamps for the split parts
    sub_segments = []
    current_time = start
    total_chars = len(text)
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
        
        # Estimate duration based on length
        part_duration = duration * (len(part) / total_chars)
        
        part_start = current_time
        part_end = current_time + part_duration
        
        sub_segments.append({
            "id": f"{segment['id']}_{i}",
            "start": format_timestamp(part_start),
            "end": format_timestamp(part_end),
            "text": part
        })
        current_time = part_end
        
    return sub_segments

def is_abbreviation(text):
    """
    Checks if the text ends with an abbreviation (e.g., "M.", "U.S.", "Ph.D.").
    Rules:
    1. Single Letter + Dot (e.g. "M.", " J.")
    2. Acronyms (sequence of Letter+Dot) (e.g. "U.S.", "U.S.A.")
    """
    text = text.strip()
    if not text.endswith('.'):
        return False

    # Rule 1: Single Capital Letter at end ("... M.")
    # Matches " M." or "^M."
    if re.search(r'(^|\s)[A-Z]\.$', text):
        return True

    # Rule 2: Acronyms ("... U.S.")
    # Matches ends with "X.Y." structure
    if re.search(r'(^|\s)([A-Z]\.)+[A-Z]\.$', text):
        return True

    # Rule 3: Common Titles/Honorifics (Case-insensitive check)
    # Includes "Doctor." specifically as requested.
    common_titles = {
        "Dr.", "Mr.", "Mrs.", "Ms.", "Mx.", "Prof.", "St.", 
        "Rev.", "Gen.", "Rep.", "Sen.", "Gov.", "Pres.", "Hon.",
        "Doctor." 
    }
    
    # Check if the text *ends* with one of these (ignoring case for safety, though titles are usually capped)
    # We use a simple suffix check.
    # Note: "text" is the full segment text. We care about the last word.
    parts = text.split()
    if not parts: return False
    last_word = parts[-1]
    
    # Clean matches
    if last_word in common_titles:
        return True
        
    return False

def read_vtt(file_path):
    # 1. Read Raw File
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. Parse Whisper Blocks (Time-based)
    pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s-->\s(\d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)

    raw_cues = []
    for i, (start, end, text) in enumerate(matches):
        raw_cues.append({
            "id": i,
            "start": start,
            "end": end,
            "text": text.replace('\n', ' ').strip()
        })

    # 3. PRE-PROCESS: Split Multi-Sentence Lines
    # This turns Whisper output into "TurboScribe-style" output
    clean_cues = []
    for cue in raw_cues:
        clean_cues.extend(split_whisper_segment(cue))

    # 4. GROUPING (Your old logic!)
    # Now that the input is clean, we can just "accumulate until period"
    blocks = []
    current_block = []
    current_text = ""
    
    for cue in clean_cues:
        current_block.append(cue)
        current_text += " " + cue['text']
        
        stripped = current_text.strip()
        
        # The condition that worked in your old tool:
        # FIX: Do NOT split if it's an abbreviation
        if stripped.endswith(('.', '?', '!', '."', '?"')) and not is_abbreviation(stripped):
            blocks.append(current_block)
            
            # DEBUG LOGGING
            b_start = current_block[0]['start']
            b_end = current_block[-1]['end']
            #print(f"   [DEBUG GROUPER] Finalized Block {len(blocks)}: IDs {current_block[0]['id']}..{current_block[-1]['id']} | Time: {b_start} -> {b_end}")
            
            current_block = []
            current_text = ""
            
    # Add leftovers
    if current_block:
        blocks.append(current_block)
        
        # DEBUG LOGGING
        b_start = current_block[0]['start']
        b_end = current_block[-1]['end']
        #print(f"   [DEBUG GROUPER] Finalized Block {len(blocks)} (Leftover): IDs {current_block[0]['id']}..{current_block[-1]['id']} | Time: {b_start} -> {b_end}")

    return blocks