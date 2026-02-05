import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_translations(original_text, text_v1, text_v2, target_language="Portuguese"):
    """
    Compares two translation versions and logs the winner.
    Run this in a background task.
    
    text_v1: The initial translation.
    text_v2: The verified/refined translation.
    """
    print(f"\n   ⚖️  Starting Background Evaluation of Translations...")

    system_prompt = f"""
    You are an expert impartial judge of translation quality.
    Target Language: {target_language}.
    
    You will receive:
    1. The [ORIGINAL ENGLISH TEXT].
    2. [TRANSLATION V1] 
    3. [TRANSLATION V2] 

    YOUR TASK:
    Compare V1 and V2 against the Original.
    Determine which one is better based on:
    - Accuracy to the original meaning.
    - Natural flow and grammar in {target_language}.
    - Correct terminology and consistency.
    - Whether the 'refinement' actually improved the text or introduced errors.

    OUTPUT FORMAT (JSON):
    {{
        "better_version": "V1" or "V2",
        "score_v1": <0-10 score>,
        "score_v2": <0-10 score>,
        "reasoning": "<Concise explanation of why one is better>"
    }}
    """

    user_content = f"""
    [ORIGINAL ENGLISH TEXT]:
    {original_text}

    [TRANSLATION V1]:
    {text_v1}

    [TRANSLATION V2]:
    {text_v2}
    """

    try:
        start_time = time.perf_counter()
        
        # Using a capable model for evaluation. 
        # If gpt-4o is not enabled, fallback to gpt-4-turbo or gpt-3.5-turbo, or the same model used for translation.
        # Assuming gpt-4o or similar is available.
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        # We assume evaluate_translations is run strictly in background,
        # so logging cost here won't affect the HTTP response that was already sent.
        # But it's good for console tracking.
        log_openai_usage("EVALUATOR", start_time, response)
        
        result_json = response.choices[0].message.content
        
        # Append to log file
        log_entry = f"""
--------------------------------------------------
Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}
Target Language: {target_language}
Original Len: {len(original_text)} chars

Evaluation Result:
{result_json}
--------------------------------------------------
"""
        with open("translation_quality_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        print(f"   ✅ Evaluation Complete. Logged to translation_quality_log.txt")

    except Exception as e:
        print(f"   ❌ Evaluation Error: {e}")
