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
    This ensures technical terms (Noise -> Ruído) and idioms (Bridge the gap -> Preencher a lacuna)
    are translated professionally, regardless of the video topic.
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