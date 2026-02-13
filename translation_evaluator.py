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
    You are an expert impartial judge of translation quality, specializing in {target_language}.
    
    YOUR GOAL:
    Compare two translation versions (V1 and V2) of a source text and determine which is definitively better.
    
    CRITERIA FOR PERFECT TRANSLATION (Score 10/10):
    1. **Accuracy**: Zero loss of meaning. All nuances are preserved.
    2. **Fluency**: Reads like a high-quality original text in {target_language}, not a translation.
    3. **Tone**: Perfectly matches the register (formal/informal/technical) of the source.
    4. **Terminology**: Uses standard, domain-appropriate terminology consistently.
    5. **Grammar**: Flawless grammar and punctuation.
    
    SCORING GUIDE:
    - 9-10: Exceptional. Native-level naturalness, perfect accuracy.
    - 7-8: Good. Accurate but may sound slightly "translated" or have minor stylistic issues.
    - 5-6: Acceptable. Convey meaning but with noticeable errors or awkward phrasing.
    - <5: Poor. Major inaccuracies or grammatical failures.
    
    OUTPUT FORMAT (JSON):
    {{
        "better_version": "V1" or "V2",
        "score_v1": <0-10 score>,
        "score_v2": <0-10 score>,
        "reasoning": "<Detailed explanation of why one version is better, citing specific examples if possible.>"
    }}
    """

    user_content = f"""
    [ORIGINAL SOURCE TEXT]:
    {original_text}

    [TRANSLATION V1 (Initial)]:
    {text_v1}

    [TRANSLATION V2 (Refined)]:
    {text_v2}
    """

    try:
        start_time = time.perf_counter()
        
        # Using a capable model for evaluation. 
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
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
