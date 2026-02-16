import sys
import os

print("Testing imports...")
try:
    import core_processor
    print("✅ core_processor imported")
except Exception as e:
    print(f"❌ core_processor failed: {e}")

try:
    import main
    print("✅ main imported")
except Exception as e:
    print(f"❌ main failed: {e}")

try:
    import cloud_worker
    print("✅ cloud_worker imported")
except Exception as e:
    print(f"❌ cloud_worker failed: {e}")
