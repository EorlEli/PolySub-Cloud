
import re

def check_file():
    with open("c:/Users/46760/PolySub/engine.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "target_language_window" in line:
            print(f"Line {i+1}: {repr(line)}")
            # Check for non-ascii in line
            non_ascii = [c for c in line if ord(c) > 127]
            if non_ascii:
                print(f"  WARNING: Non-ASCII characters found: {non_ascii}")
            # Check variable name consistency
            match = re.search(r'\b(target_language_window)\b', line)
            if match:
                print(f"  Found exact match: '{match.group(1)}'")
            else:
                # Check fuzzy match? Maybe 'target_language_window' with weird char?
                pass

if __name__ == "__main__":
    check_file()
