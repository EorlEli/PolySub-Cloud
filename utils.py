import time
import logging

# Setup a specific logger for tracing
trace_logger = logging.getLogger("openai_trace")
trace_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
trace_logger.addHandler(handler)

def log_openai_usage(func_name, start_time, response):
    """
    Extracts and logs: Latency, Token Usage, and Model.
    """
    duration = time.perf_counter() - start_time
    
    # Extract usage data safely
    try:
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        model = response.model

        # --- PRICING FOR GPT-5-NANO (Standard Tier) ---
        # Input: $0.05 per 1M
        # Output: $0.40 per 1M
        input_cost = (prompt_tokens * 0.05) / 1_000_000
        output_cost = (completion_tokens * 0.40) / 1_000_000
        total_cost = input_cost + output_cost
        
        # Log the detailed trace
        print(f"\n   📊 [TRACE] {func_name}")
        print(f"      ├─ Model:      {model}")
        print(f"      ├─ Time:       {duration:.4f}s")
        print(f"      ├─ Tokens:     {total_tokens} (In: {prompt_tokens}, Out: {completion_tokens})")
        print(f"      └─ Est. Cost:  ${total_cost:.6f}")
        
    except Exception as e:
        print(f"   ⚠️ [TRACE ERROR] Could not extract usage: {e}")