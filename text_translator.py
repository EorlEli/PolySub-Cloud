import os
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate_full_text(full_text, target_language="Portuguese"):
    """
    Translates the full text using a 'Context-Aware' System Prompt.
    This ensures technical terms and idioms are translated professionally, regardless of the video topic.
    """
    print(f"\n   🌍 Translating full text to {target_language}...")
    
    system_prompt = f"""
    You are a professional subtitle translator and localization expert.
    Target Language: {target_language}.
    
    Your goal is to produce subtitles that sound like they were originally written in the target language, not translated.
    
    ### CORE GUIDELINES:
    
    1. **Detect Context & Tone:**
       - Read the input to understand the speaker's background (e.g., Scientist, Chef, Gamer).
       - If the text is technical, use precise technical vocabulary (e.g., "Noise" -> "Ruído" in engineering, not "Barulho").
       - If the text is informal, use natural colloquialisms.
       
    2. **Respect Metaphors & Idioms:**
       - Do NOT translate idioms literally. Translate their intended meaning.
       - Example: "Bridge the gap" -> "Preencher a lacuna" (Portuguese) or "Acortar distancias" (Spanish), NOT "Construir uma ponte".
       - Example: "Open the hood" -> "Examinar a fundo" or "Entender o funcionamento", NOT "Abrir o capô" (unless it is literally a car).
       - **Crucial:** If the speaker uses a specific metaphor relevant to their field (e.g., a Biologist saying "Immunity"), preserve the metaphor ("Imunidade") rather than simplifying it to "Protection".

    3. **Sentence Structure:**
       - Avoid English sentence structures.
       - Reorder words to flow naturally in {target_language}.
       
    4. **Output Format:**
       - Return ONLY the translated text. Do not add explanations.

    5. **Consistency:**
       - Maintain consistent terminology and style throughout the translation.
    """
    try:
        start_time = time.perf_counter()
        
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_text}
            ]
        )
        
        log_openai_usage("TEXT-TRANSLATOR", start_time, response)
        return response.choices[0].message.content

    except Exception as e:
        print(f"   ❌ Translation Error: {e}")
        return ""

def verify_translation_quality(source_text, translated_text, target_language="Portuguese"):
    """
    Verifies and refines the translation using a second LLM pass.
    Focuses on accuracy, nuance, clarity, and linguistic flow.
    """
    print(f"\n   🕵️ Verifying translation quality...")

    system_prompt = f"""
    You are a meticulous Translation Quality Assurance Specialist for {target_language}.
    Your task is to review the translation of a text from English to {target_language} and refine it.
    
    You have the [ORIGINAL TEXT] and the [DRAFT TRANSLATION].
    
    YOUR GOAL:
    Return the FINAL, OPTIMIZED translation.
    
    ### INSTRUCTIONS:
    
    1. **Evaluate Accuracy & Nuance:**
       - Compare sentence by sentence. ensure the translation captures the exact meaning and tone of the original.
       - Correct any mistranslations or missed nuances.
       - Adhere to the national variety of the target language. For example, if the target language is written in Brazilian Portuguese, use Brazilian Portuguese. If it is written in European Portuguese, use European Portuguese.
       
    2. **Refine Context & Clarity:**
       - Ensure the language is natural, clear, and resonant for a native speaker.
       - The text should flow smoothly (optimize linguistic flow).
       
    3. **Semantic Quality:**
       - Check phrases for semantic correctness and impact.
       - Replace awkward literal translations with natural idiomatic expressions where appropriate (while preserving the original metaphor's intent if it's specific to the domain).
       
    4. **Output:**
       - **RETURN ONLY THE REFINED TRANSLATED TEXT.**
       - NO explanations, NO markdown formatting, NO "Here is the improved version". Just the text.
    """
    
    user_content = f"""
    [ORIGINAL TEXT]:
    {source_text}
    
    [DRAFT TRANSLATION]:
    {translated_text}
    """

    try:
        start_time = time.perf_counter()
        
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        
        log_openai_usage("TRANSLATION-VERIFIER", start_time, response)
        refined_text = response.choices[0].message.content
        return refined_text

    except Exception as e:
        print(f"   ❌ Verification Error: {e}")
        # If verification fails, return the original translation so the pipeline doesn't break
        return translated_text