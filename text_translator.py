import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from utils import log_openai_usage
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CHUNK_SIZE = 4000  # Characters (approx 1000 tokens) - Safe size for reliable translation
CONTEXT_SIZE = 200     # Characters of overlap/context
MODEL_NAME = "gpt-5.2" # Global model setting

def split_into_chunks(text, max_size=MAX_CHUNK_SIZE):
    """
    Splits text into chunks of roughly max_size characters, 
    respecting sentence boundaries and preserving whitespace.
    """
    chunks = []
    current_chunk = ""
    
    # Split by sentence endings, capturing the whitespace that follows
    # pattern: lookbehind for punctuation, then capture one or more whitespace chars
    parts = re.split(r'(?<=[.!?])(\s+)', text)
    
    for part in parts:
        if not part: continue # skip empty
        
        # If adding this part stays within limit
        if len(current_chunk) + len(part) <= max_size:
            current_chunk += part
        else:
            # If current chunk is full, push it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If the part itself is huge, we start a new chunk with it
            current_chunk += part
            
    if current_chunk:
        #print (f"Last chunk: {current_chunk}")
        chunks.append(current_chunk)
        
    return chunks

def translate_full_text(full_text, target_language="Portuguese"):
    """
    Translates the full text using a 'Context-Aware' System Prompt.
    Returns: (full_translated_text, source_chunks, translated_chunks)
    """
    print(f"\n   🌍 Translating full text to {target_language}...")
    
    chunks = split_into_chunks(full_text)
    translated_chunks = []
    previous_context = ""
    
    print(f"   ℹ️ Text split into {len(chunks)} chunks.")

    system_prompt_base = f"""
    You are a world-class subtitle translator and linguist specializing in {target_language}.
    
    YOUR MISSION:
    Produce a translation that is 100% natural, idiomatic, and culturally appropriate for {target_language} audiences.
    massively improving upon literal or machine-like translations.
    
    GUIDELINES:
    1. **Natural Flow**: The text must read as if it was originally written in {target_language}. Avoid "translationese".
    2. **Accuracy**: Preserve the exact meaning, tone, and nuance of the source.
    3. **Terminology**: Use precise and consistent terminology.
    4. **Conciseness**: Subtitles must be easy to read. Avoid unnecessary wordiness.
    5. **Idioms**: Translate the *meaning*, not the words. Replace source idioms with {target_language} equivalents.
    6. **Context**: Use the provided context to maintain continuity.
    7. **Structure**: Use natural sentence structure in {target_language}.    
    8. **Completeness**: Translate every single sentence. Do not summarize or skip text.
    9. **Repetitions**: Keep repeated phrases (e.g., "Doing good. Doing good." -> "Estou bem. Estou bem.").
    10. **1:1 rule**: Translate one original sentence, the one which ends with a dot, question mark or exclamation mark, into one translated sentence, which ends with a dot, question mark or exclamation mark.
    11. **Short words and fillers**: Pay meticulous attention to short sentences, interjections, and filler words (e.g., "Yeah.", "Right?", "No?", "Okay.", "Well,"). You MUST translate every single one of them. NEVER drop or merge them.

    OUTPUT:
    Return ONLY the translated text. No notes, no explanations, no preambles, no postambles.
    """

    for i, chunk in enumerate(chunks):
        print(f"      Processing Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        
        context_instruction = ""
        if previous_context:
            context_instruction = f"""
            ### CONTEXT FROM PREVIOUS SECTIONS:
            The text continues from: "...{previous_context}"
            Ensure seamless continuity in style, tone, and terminology.
            """
        
        # Add context from the NEXT chunk if available (lookahead) could be useful but complex to implement here.
        
        user_content = f"""
            [SOURCE TEXT TO TRANSLATE]:
            {chunk}
        """

        try:
            start_time = time.perf_counter()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt_base + context_instruction},
                    {"role": "user", "content": user_content}
                ]
            )
            log_openai_usage(f"TRANSLATE-CHUNK-{i+1}", start_time, response)
            
            translated_text = response.choices[0].message.content.strip()
            translated_chunks.append(translated_text)
            
            # Update context for next chunk
            previous_context = translated_text[-CONTEXT_SIZE:] if len(translated_text) > CONTEXT_SIZE else translated_text
            
        except Exception as e:
            print(f"   ❌ Translation Error on chunk {i+1}: {e}")
            translated_chunks.append(chunk) # Fallback to original

    full_translation = " ".join(translated_chunks)
    return full_translation, chunks, translated_chunks

def verify_translation_quality(source_chunks, translated_chunks, target_language="Portuguese"):
    """
    Verifies and refines the translation chunk by chunk using a rigorous QA process.
    """
    print(f"\n   🕵️ Verifying and Refining Translation Quality...")
    
    refined_chunks = []
    
    system_prompt = f"""
    You are a Senior Translation Editor and Quality Assurance Specialist for {target_language}.
    Your goal is perfection. 
    
    TASK:
    Review the [SOURCE] and [DRAFT TRANSLATION]. 
    Identify and correct ANY issues to produce a [PERFECTED TRANSLATION].
    
    CHECKLIST:
    1. **Mistranslations**: Fix any errors in meaning.
    2. **Grammar & Syntax**: Ensure perfect grammar and natural sentence structure.
    3. **Terminological Consistency**: Ensure key terms are used correctly.
    4. **Fluidity**: Improve flow. If a sentence sounds awkward, rewrite it to sound native.
    5. **Formatting**: Preserve original punctuation style where appropriate for subtitles.
    6. **1:1 Sentence Mapping**: Ensure each source sentence corresponds to exactly one translated sentence.
    7. **Sentence Splitting**: If the translation combines sentences using colons, semicolons, or dashes, SPLIT them with a period (.). NEVER combine multiple source sentences into one.
    8. **COMPLETENESS**: CRITICAL. Ensure EVERY source sentence logic is preserved. Do not skip content or summarize.
    9. **Short words and Fillers**: NEVER drop short sentences like "Yeah.", "Right.", or "Okay.". Ensure they are present in the final target text.


    If the draft is already perfect, output it exactly as is.
    If it needs improvement, output ONLY the improved version.
    """
    
    for i, (source, draft) in enumerate(zip(source_chunks, translated_chunks)):
        print(f"      Refining Chunk {i+1}/{len(source_chunks)}...")
        
        user_content = f"""
        [SOURCE]:
        {source}
        
        [DRAFT TRANSLATION]:
        {draft}
        
        OUTPUT THE PERFECTED TRANSLATION ONLY:
        """
        
        try:
            start_time = time.perf_counter()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            log_openai_usage(f"VERIFY-CHUNK-{i+1}", start_time, response)
            
            refined_text = response.choices[0].message.content.strip()
            
            # Sanity check: if refined text is vastly different in length (e.g. empty or double), warn or fallback?
            # For now, trust the model.
            refined_chunks.append(refined_text)
            
        except Exception as e:
            print(f"   ❌ Verification Error on chunk {i+1}: {e}")
            refined_chunks.append(draft) # Fallback to draft

    return " ".join(refined_chunks)