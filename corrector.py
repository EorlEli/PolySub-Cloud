import json
import time

def get_topic(text, client, model="gpt-5-nano"):
    """
    Step 1: Determine the main topic of the text.
    """
    print("   🧠 Analyzing topic...")
    system_prompt = """
    You are a Topic Analyzer. 
    Analyze the provided text and determine the main overarching topic or domain (e.g., "Computer Science", "Gardening", "Astrophysics", "Casual Conversation").
    Be specific but concise (1-5 words).
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:4000]} # Send first 4k chars for context
            ]
        )
        topic = response.choices[0].message.content.strip()
        print(f"   💡 Topic Detected: {topic}")
        return topic
    except Exception as e:
        print(f"   ⚠️ Topic detection failed: {e}")
        return "General"

def get_corrections(utterances, topic, client, model="gpt-5-nano"):
    """
    Step 2: Find corrections based on topic.
    Receives list of Utterance objects (dicts).
    Returns: List of dicts { "utterance_id": int, "original": "...", "replacement": "..." }
    """
    print("   🧐 Checking for mistranscriptions...")
    
    # 1. Prepare numbered transcript for LLM
    numbered_transcript = ""
    for idx, u in enumerate(utterances):
        numbered_transcript += f"[ID: {idx}] {u['transcript']}\n"

    system_prompt = f"""
    You are a Transcription Corrector.
    The text provided is broken into 'utterances' with IDs.
    The topic is: "{topic}".
    
    Your task is to:
    1. Identify words that are likely phonetically similar mistranscriptions and DO NOT make sense in the context of the identified topic.
    2. Check that the adjectives describing nouns make sense in the context of the identified topic.
    
    RULES:
    1. Only correct CLEAR errors where the word is out of place.
    2. Example: "The code is intent" -> "The code is indented" (if topic is Programming).
    3. Example: "The sky is blue" -> NO CHANGE.
    4. Provide the output as a JSON object with a key "corrections" containing a list of objects.
    5. Each object must have: 
       - "utterance_id": The ID of the line containing the error (Usage: reference the [ID: X] tags) It *must* be an int.
       - "original": The exact word/phrase to change.
       - "replacement": The corrected word/phrase.
    6. If no corrections are needed, return "corrections": [].
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": numbered_transcript}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        corrections = result.get("corrections", [])
        return corrections
    
    except Exception as e:
        print(f"   ⚠️ Correction check failed: {e}")
        return []

def patch_response(response_dict, corrections):
    """
    Modifies the deepgram response DICT in-place to apply corrections.
    Targeting specific utterance transcripts ONLY.
    """
    
    # helper to normalize text for insensitive search
    def clean(s): return str(s).lower().strip()

    try:
        # Get reference to the list of utterances in the dict
        utterances = response_dict.get("results", {}).get("utterances", [])
        
        replacement_count = 0
        
        for correction in corrections:
            u_id = correction.get("utterance_id")
            orig = correction.get("original")
            repl = correction.get("replacement")
            
            if u_id is None or u_id >= len(utterances):
                continue
                
            target_utterance = utterances[u_id]
            current_transcript = target_utterance.get("transcript", "")
            
            # Patch the utterance transcript string
            if orig in current_transcript:
                new_transcript = current_transcript.replace(orig, repl)
                print(f"      🔄 [Utterance {u_id}] Replaced '{orig}' -> '{repl}'")
                target_utterance["transcript"] = new_transcript
                replacement_count += 1
            else:
                 print(f"      ⚠️ Warning: Could not find '{orig}' in utterance {u_id}")

        
        # --- Reconstruct the global transcript ---
        # The top-level 'transcript' must match the sum of utterances
        full_transcript = " ".join([u["transcript"] for u in utterances])
        
        # Update the top-level transcript in the dict
        # (This handles the case where simple 'transcript_text' usage reads correction)
        try:
             response_dict["results"]["channels"][0]["alternatives"][0]["transcript"] = full_transcript
        except:
             pass
        
        print(f"   ✨ Applied {replacement_count} corrections.")
        return response_dict, full_transcript

    except Exception as e:
        print(f"   ❌ Error patching response: {e}")
        try:
             safe_transcript = response_dict["results"]["channels"][0]["alternatives"][0]["transcript"]
        except:
             safe_transcript = ""
        return response_dict, safe_transcript

def apply_corrections(deepgram_response, client):
    """
    Orchestrator function.
    """
    try:
        # 0. Convert to dict first to avoid Pydantic frozen errors
        if hasattr(deepgram_response, "to_dict"):
            response_dict = deepgram_response.to_dict()
        elif hasattr(deepgram_response, "model_dump"):
            response_dict = deepgram_response.model_dump()
        elif isinstance(deepgram_response, dict):
            response_dict = deepgram_response
        else:
             # Fallback using json serialization provided by the object usually
             response_dict = json.loads(deepgram_response.to_json())

        # 1. Extract essentials
        try:
            # We strictly need utterances for this new logic
            utterances = response_dict["results"]["utterances"]
            # Also get global text for topic detection
            original_text = response_dict["results"]["channels"][0]["alternatives"][0]["transcript"]
        except KeyError:
            print("   ⚠️ 'utterances' not found in response. Skipping correction.")
            return deepgram_response, ""
        
        # 2. Get Topic (uses global text)
        topic = get_topic(original_text, client)
        
        # 3. Get Corrections (uses utterances)
        corrections = get_corrections(utterances, topic, client)
        
        if not corrections:
            print("   ✅ No corrections suggested.")
            return response_dict, original_text
        
        print(f"   📋 Found {len(corrections)} suggested corrections.")
        for c in corrections:
            print(f"      - [ID: {c.get('utterance_id')}] {c['original']} -> {c['replacement']}")

        # 4. Patch Response
        patched_response_dict, patched_text = patch_response(response_dict, corrections)
        
        return patched_response_dict, patched_text

    except Exception as e:
        print(f"   ⚠️ Correction process failed: {e}")
        # Return original if anything fails
        # If we failed before dict conversion, we return the object, which transcriber handles.
        # If we failed after, we return dict.
        return deepgram_response, ""
