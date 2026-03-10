"""
Proper Noun Consistency Normalizer

Runs on the raw Deepgram response (as dict) BEFORE the LLM corrector.
Groups phonetically similar proper nouns, picks the most frequent / 
highest-confidence variant as canonical, and normalizes outliers.
"""

import re
from difflib import SequenceMatcher
from collections import defaultdict


# --- Configuration ---
SIMILARITY_THRESHOLD = 0.70   # SequenceMatcher ratio to consider two words "similar"
MIN_GROUP_SIZE = 2            # Only normalize if a group has ≥2 distinct variants


def _is_proper_noun(word_text):
    """
    Heuristic: a word is a candidate for technical noun normalization if:
    1. It starts with an uppercase letter.
    2. It has internal capitalization (e.g., OpenClaw, CLI, MCP) 
       OR it is a relatively long word (e.g., Cloudbot, Opencloud) (> 7 chars).

    """
    if not word_text or len(word_text) < 3:
        return False
    if not word_text[0].isupper():
        return False
        
    # Technical noun heuristic:
    # 1. Has internal capitalization (e.g., OpenClaw, CLI, SQL)
    #    Checked by looking for any uppercase letter after the first char.
    has_internal_cap = any(c.isupper() for c in word_text[1:])
    
    # 2. Is a relatively long proper noun (e.g., Cloudbot, Opencloud, Kubernetes)
    #    Most common sentence starters are short (They, This, That, etc.)
    is_long = len(word_text) > 7
    
    return has_internal_cap or is_long


def _phonetic_similarity(a, b):
    """Returns similarity ratio between two strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _extract_proper_nouns(utterances):
    """
    Extracts all proper-noun-like words from utterances with their 
    confidence scores and locations.
    
    Returns: list of dicts:
        { "word": str, "confidence": float, "utterance_id": int, "word_idx": int }
    """
    results = []
    for u_idx, utt in enumerate(utterances):
        words = utt.get("words", [])
        for w_idx, w in enumerate(words):
            punctuated = w.get("punctuated_word", "") or w.get("word", "")
            # Strip trailing punctuation for analysis
            clean = re.sub(r'[.,!?;:\'"]+$', '', punctuated)
            
            if _is_proper_noun(clean):
                results.append({
                    "word": clean,
                    "confidence": w.get("confidence", 1.0),
                    "utterance_id": u_idx,
                    "word_idx": w_idx,
                })
    return results


def _group_similar(proper_nouns):
    """
    Groups proper nouns by phonetic similarity.
    
    Returns: list of groups, where each group is a list of proper noun entries
    that are phonetically similar to each other.
    """
    # Deduplicate to get unique word forms
    unique_words = list(set(pn["word"] for pn in proper_nouns))
    
    # Build adjacency: which unique words are similar to each other?
    groups = []  # list of sets of word forms
    assigned = set()
    
    for i, w1 in enumerate(unique_words):
        if w1 in assigned:
            continue
        group = {w1}
        assigned.add(w1)
        for j, w2 in enumerate(unique_words):
            if j <= i or w2 in assigned:
                continue
            if _phonetic_similarity(w1, w2) >= SIMILARITY_THRESHOLD:
                group.add(w2)
                assigned.add(w2)
        groups.append(group)
    
    # Now attach all entries to their group
    result = []
    for group_words in groups:
        if len(group_words) < MIN_GROUP_SIZE:
            continue  # Only care about groups with multiple variants
        entries = [pn for pn in proper_nouns if pn["word"] in group_words]
        result.append(entries)
    
    return result


def _pick_canonical(group_entries):
    """
    Given a group of similar proper noun entries, pick the canonical form.
    Strategy: most frequent variant wins; ties broken by highest average confidence.
    
    Returns: the canonical word string, or None if group is trivial.
    """
    # Count frequency and avg confidence per variant
    variant_stats = defaultdict(lambda: {"count": 0, "total_conf": 0.0})
    
    for entry in group_entries:
        word = entry["word"]
        variant_stats[word]["count"] += 1
        variant_stats[word]["total_conf"] += entry["confidence"]
    
    # Sort by (count DESC, avg_confidence DESC)
    ranked = sorted(
        variant_stats.items(),
        key=lambda x: (x[1]["count"], x[1]["total_conf"] / max(x[1]["count"], 1)),
        reverse=True,
    )
    
    canonical = ranked[0][0]
    return canonical


def normalize_proper_nouns(response_dict):
    """
    Main entry point. Operates on the Deepgram response dict IN-PLACE.
    
    1. Extracts proper-noun-like words with confidence
    2. Groups phonetically similar words
    3. Picks canonical form per group  
    4. Replaces non-canonical variants in utterance transcripts + words
    
    Returns: the (modified) response_dict
    """
    try:
        utterances = response_dict.get("results", {}).get("utterances", [])
        if not utterances:
            return response_dict
        
        # 1. Extract
        proper_nouns = _extract_proper_nouns(utterances)
        if not proper_nouns:
            print("   📋 Normalizer: No proper nouns found.")
            return response_dict
        
        # 2. Group
        groups = _group_similar(proper_nouns)
        if not groups:
            print("   ✅ Normalizer: All proper nouns are consistent.")
            return response_dict
        
        # 3 & 4. Normalize each group
        total_replacements = 0
        
        for group_entries in groups:
            canonical = _pick_canonical(group_entries)
            variants = set(e["word"] for e in group_entries) - {canonical}
            
            if not variants:
                continue
            
            # Calculate canonical form's average confidence as baseline
            canonical_confs = [e["confidence"] for e in group_entries if e["word"] == canonical]
            canonical_avg_conf = sum(canonical_confs) / len(canonical_confs) if canonical_confs else 1.0
            
            # Confidence gate: only normalize variants whose avg confidence
            # is meaningfully lower than the canonical's. High-confidence words
            # that happen to sound similar are likely intentionally different names.
            CONFIDENCE_GATE = 0.95  # variant must be below 95% of canonical's confidence
            
            print(f"   🔗 Normalizer: Canonical form = '{canonical}' (avg conf {canonical_avg_conf:.3f})")
            for var in sorted(variants):
                var_count = sum(1 for e in group_entries if e["word"] == var)
                var_conf = [e["confidence"] for e in group_entries if e["word"] == var]
                avg_conf = sum(var_conf) / len(var_conf) if var_conf else 0
                will_normalize = avg_conf < canonical_avg_conf * CONFIDENCE_GATE
                status = "→" if will_normalize else "⏩ SKIP (high confidence)"
                print(f"      ↳ '{var}' (×{var_count}, avg conf {avg_conf:.3f}) {status} '{canonical}'")
            
            # Apply replacements in utterances
            for entry in group_entries:
                if entry["word"] == canonical:
                    continue
                
                # Confidence gate check per-word
                if entry["confidence"] >= canonical_avg_conf * CONFIDENCE_GATE:
                    continue
                
                u_idx = entry["utterance_id"]
                w_idx = entry["word_idx"]
                old_word = entry["word"]
                utt = utterances[u_idx]
                
                # Replace in the transcript string
                # We need to handle the punctuated form (may have trailing punctuation)
                old_transcript = utt.get("transcript", "")
                # Replace the word preserving any trailing punctuation
                new_transcript = re.sub(
                    re.escape(old_word) + r'(?=[.,!?;:\s\'"]|$)',
                    canonical,
                    old_transcript,
                    count=1,
                )
                if new_transcript != old_transcript:
                    utt["transcript"] = new_transcript
                    total_replacements += 1
                
                # Also update the words array entry
                words = utt.get("words", [])
                if w_idx < len(words):
                    pw = words[w_idx].get("punctuated_word", "")
                    # Preserve punctuation suffix
                    suffix_match = re.search(r'[.,!?;:\'"]+$', pw)
                    suffix = suffix_match.group() if suffix_match else ""
                    words[w_idx]["punctuated_word"] = canonical + suffix
                    words[w_idx]["word"] = canonical.lower()
        
        # Rebuild the global transcript from utterances
        if total_replacements > 0:
            full_transcript = " ".join(u["transcript"] for u in utterances)
            try:
                response_dict["results"]["channels"][0]["alternatives"][0]["transcript"] = full_transcript
            except (KeyError, IndexError):
                pass
        
        print(f"   ✨ Normalizer: Applied {total_replacements} proper noun corrections.")
        return response_dict
    
    except Exception as e:
        print(f"   ⚠️ Normalizer error (non-fatal): {e}")
        return response_dict
