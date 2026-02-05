import re
import os

def parse_vtt_simple(file_path):
    """
    Parses VTT to get a list of cues: {'start': float, 'end': float, 'text': str, 'lines': int}
    """
    if not os.path.exists(file_path):
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find timestamps and text
    # 00:00:00.000 --> 00:00:05.000
    pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s-->\s(\d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)

    cues = []
    for start_str, end_str, text_block in matches:
        start = parse_time(start_str)
        end = parse_time(end_str)
        
        # Clean text
        text_clean = text_block.strip()
        lines = text_clean.split('\n')
        line_count = len([l for l in lines if l.strip()])
        
        cues.append({
            "start": start,
            "end": end,
            "duration": end - start,
            "text": text_clean,
            "lines": line_count
        })
    return cues

def parse_time(t_str):
    parts = t_str.replace(',', '.').split(':')
    if len(parts) == 3:
        return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0])*60 + float(parts[1])
    return 0.0

def validate_vtt_structure(original_vtt_path, target_vtt_path):
    """
    Checks the generated VTT for:
    1. Line Count (Max 2 ideal, 3 warning, >3 fail)
    2. Global Timing (Duration consistency)
    3. Reading Speed (CPS)
    
    Returns a dict with report and simple boolean status.
    """
    print(f"\n   🔍 Running VTT Validation...")
    
    original_cues = parse_vtt_simple(original_vtt_path)
    target_cues = parse_vtt_simple(target_vtt_path)
    
    errors = []
    warnings = []
    
    if not original_cues:
        errors.append("Original VTT file is empty or missing.")
    if not target_cues:
        errors.append("Generated Target VTT file is empty or missing.")
        
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    # --- 1. Line Count Check ---
    max_lines_found = 0
    for i, cue in enumerate(target_cues):
        if cue['lines'] > max_lines_found:
            max_lines_found = cue['lines']
            
        if cue['lines'] > 3:
            errors.append(f"Block {i+1} has {cue['lines']} lines (Limit is 3).")
        elif cue['lines'] == 3:
             warnings.append(f"Block {i+1} has 3 lines (Ideal is 2).")

    # --- 2. Global Timing Check ---
    orig_start = original_cues[0]['start']
    orig_end = original_cues[-1]['end']
    orig_duration = orig_end - orig_start
    
    target_start = target_cues[0]['start']
    target_end = target_cues[-1]['end']
    target_duration = target_end - target_start
    
    # Allow 10% variance or 10 seconds, whichever is larger
    # (Translations can be longer/shorter, but total video time shouldn't vanish)
    time_diff = abs(orig_duration - target_duration)
    tolerance = max(10.0, orig_duration * 0.10) 
    
    if time_diff > tolerance:
        warnings.append(f"Duration mismatch: Original={orig_duration:.1f}s, Target={target_duration:.1f}s (Diff: {time_diff:.1f}s)")

    # --- 3. Reading Speed Check (CPS) ---
    high_cps_count = 0
    for i, cue in enumerate(target_cues):
        # Ignore very short silences or empty cues
        if cue['duration'] < 0.1 or not cue['text']: 
            continue
            
        char_count = len(cue['text'])
        cps = char_count / cue['duration']
        
        if cps > 25:
             high_cps_count += 1
             # Only log first few to avoid spam
             if high_cps_count <= 3:
                 warnings.append(f"Block {i+1} is too fast ({cps:.1f} CPS). Text: {cue['text'][:30]}...")

    if high_cps_count > 0:
        warnings.append(f"Found {high_cps_count} blocks with CPS > 25.")

    # --- Summary ---
    is_valid = len(errors) == 0
    
    if is_valid:
        print("   ✅ VTT Structure Validated. Looks good.")
        if warnings:
            print(f"   ⚠️  ({len(warnings)} Warnings found)")
    else:
        print(f"   ❌ VTT Validation FAILED with {len(errors)} errors.")
        
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "max_lines": max_lines_found,
            "orig_duration": orig_duration,
            "target_duration": target_duration
        }
    }
