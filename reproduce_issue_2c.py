
import os
from matcher import find_matching_translation

print("=== TEST CASE: Repeated Phrase 'Can I go in?' (Exact User Text) ===")

# Block 43:
block_43_org = "Opus, really have to like, you have to have plan mode, you have to push it harder to like go in these directions because it's it's just like like, yeah, can I go in?"
# Block 44:
block_44_org = "Can I go in?"

# Target Window (The full translation text provided by the user)
# "No Opus, tens mesmo de… tens de pôr em modo plano, tens de apertar mais com ele para ir nessas direções, porque ele é mais do género: “ya, posso ir? posso ir?”"
target_window = "No Opus, tens mesmo de… tens de pôr em modo plano, tens de apertar mais com ele para ir nessas direções, porque ele é mais do género: “ya, posso ir? posso ir?”"


print(f"--- Testing Block 43 ---")
print(f"Source: '{block_43_org}'")
print(f"Next Source: '{block_44_org}'")
print(f"Target Window: '{target_window}'")

matched_43 = find_matching_translation(
    original_language_block_text=block_43_org,
    target_language_search_window=target_window,
    context_preview="",
    next_block_text=block_44_org
)

print(f"MATCHED: '{matched_43}'")

# Expected: The match should include only the FIRST "posso ir?".
# The second "posso ir?" belongs to Block 44.

count_posso = matched_43.count("posso ir?")
print(f"Count of 'posso ir?': {count_posso}")

if count_posso > 1:
    print("❌ FAILURE: Match included 'posso ir?' multiple times.")
elif count_posso == 0:
    print("❌ FAILURE: Match did not include 'posso ir?'.")
else:
    print("✅ SUCCESS: Match included 'posso ir?' exactly once.")
