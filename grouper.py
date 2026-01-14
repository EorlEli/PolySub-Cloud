import re

def parse_vtt_lines(vtt_content):
    """Parses raw VTT string into a list of line dictionaries."""
    lines = vtt_content.strip().replace('\r\n', '\n').split('\n')
    parsed_lines = []
    current_entry = {}
    time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s-->\s(\d{2}:\d{2}:\d{2}\.\d{3})')
    last_index = None

    for line in lines:
        line = line.strip()
        if not line or line == "WEBVTT": continue
        if line.isdigit():
            last_index = line
            continue
        
        time_match = time_pattern.search(line)
        if time_match:
            if 'text' in current_entry: parsed_lines.append(current_entry)
            current_entry = {
                'id': last_index, 
                'start': time_match.group(1), 
                'end': time_match.group(2), 
                'text': []
            }
        else:
            if 'text' in current_entry: current_entry['text'].append(line)

    if current_entry and 'text' in current_entry: parsed_lines.append(current_entry)
    
    # Clean text
    for p in parsed_lines: 
        p['text'] = " ".join(p['text']).strip()
        
    return parsed_lines

def get_clean_blocks(parsed_lines):
    """Groups lines together until a sentence-ending punctuation is found."""
    blocks = []
    current_block = []
    
    for line in parsed_lines:
        current_block.append(line)
        text = line['text']
        
        # STOP CONDITION: Line ends with . ? or !
        if text.endswith('.') or text.endswith('?') or text.endswith('!'):
            blocks.append(current_block)
            current_block = []
            
    # Add any leftovers
    if current_block: blocks.append(current_block)
    return blocks

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("--- TESTING GROUPER ---")
    mock_vtt = """WEBVTT

1
00:00:01.000 --> 00:00:02.000
This sentence is split

2
00:00:02.000 --> 00:00:03.000
across two lines.

3
00:00:03.000 --> 00:00:04.000
This is a new sentence.
"""
    raw = parse_vtt_lines(mock_vtt)
    blocks = get_clean_blocks(raw)
    
    print(f"Found {len(blocks)} Blocks (Expected 2):")
    for i, b in enumerate(blocks):
        print(f"Block {i+1}: {[l['text'] for l in b]}")