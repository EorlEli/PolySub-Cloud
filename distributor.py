import os
import json
import math
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def enforce_line_count_mechanically(pt_lines, target_count):
    """
    The Safety Net:
    - If AI returns too few lines, we CUT sentences in half to fill the void.
    - If AI returns too many lines, we MERGE the extras.
    """
    # Clean empty strings
    pt_lines = [line for line in pt_lines if line.strip()]

    # CASE 1: UNDERFLOW (AI gave 2 lines, we need 3)
    while len(pt_lines) < target_count:
        # Find the longest line
        longest_idx = 0
        max_len = 0
        for i, line in enumerate(pt_lines):
            if len(line) > max_len:
                max_len = len(line)
                longest_idx = i
        
        # Split it in half
        words = pt_lines[longest_idx].split()
        if len(words) > 1:
            mid = math.ceil(len(words) / 2)
            part1 = " ".join(words[:mid])
            part2 = " ".join(words[mid:])
            pt_lines[longest_idx] = part1
            pt_lines.insert(longest_idx + 1, part2)
        else:
            # Emergency: Line is one word long, just duplicate to fill slot
            pt_lines.insert(longest_idx + 1, ".")

    # CASE 2: OVERFLOW (AI gave 4 lines, we need 3)
    while len(pt_lines) > target_count:
        last = pt_lines.pop()
        pt_lines[-1] = pt_lines[-1] + " " + last

    return pt_lines

def distribute_translation(english_lines, portuguese_chunk):

    start_time = time.perf_counter() # <--- START

    total_lines = len(english_lines)
    english_list_str = "\n".join([f"Line {i}: {l['text']}" for i, l in enumerate(english_lines)])

    system_prompt = f"""
    You are a Line Distributor.
    INPUT: {total_lines} empty lines (buckets) and a Portuguese text.
    TASK: Distribute the text into exactly {total_lines} lines.
    CRITICAL: You MUST return {total_lines} lines.
    OUTPUT JSON: {{ "lines": [ "text", "text", ... ] }}
    """
    
    user_prompt = f"--- BUCKETS: {total_lines} ---\n{english_list_str}\n\n--- CONTENT ---\n{portuguese_chunk}"

    pt_lines = []
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            
        )
        log_openai_usage("DISTRIBUTOR", start_time, response) # <--- LOG
        pt_lines = json.loads(response.choices[0].message.content).get("lines", [])
    except Exception as e:
        print(f"AI Error: {e}")

    # FORCE THE COUNT
    final_lines = enforce_line_count_mechanically(pt_lines, total_lines)

    # Rebuild Dictionary Structure
    final_segments = []
    for i, original in enumerate(english_lines):
        final_segments.append({
            'start': original['start'],
            'end': original['end'],
            'text': final_lines[i]
        })
    return final_segments

# --- TEST BLOCK (Your Specific Failure Case) ---
if __name__ == "__main__":
    print("--- TESTING DISTRIBUTOR (MECHANICAL FIX) ---")
    
    # Needs 3 lines
    english_mock = [
        {'text': 'Line A', 'start': '00:01', 'end': '00:02'},
        {'text': 'Line B', 'start': '00:02', 'end': '00:03'},
        {'text': 'Line C', 'start': '00:03', 'end': '00:04'}
    ]
    
    # AI Failure Simulation: Returns only 2 lines
    bad_ai_output = ["Primeira parte da frase", "Segunda parte final"]
    
    print(f"Input: {len(bad_ai_output)} lines from AI.")
    print(f"Target: {len(english_mock)} lines needed.")
    
    fixed_lines = enforce_line_count_mechanically(bad_ai_output, 3)
    
    print("\n--- Result after Mechanical Enforcement ---")
    for i, line in enumerate(fixed_lines):
        print(f"Line {i+1}: {line}")
        
    if len(fixed_lines) == 3:
        print("\n✅ Success: It forced 3 lines.")
    else:
        print("\n❌ Failed.")