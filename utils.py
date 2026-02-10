import sys

# --- PRICING TABLE (Adjust as needed) ---
# Prices in USD
PRICING = {
    # Cost per 1 Million Tokens
    "gpt-5-nano":  {"input": 0.05, "output": 0.40},
    "gpt-5.2":  {"input": 1.75, "output": 14.00},
    "whisper-1":   0.0043  # Cost per MINUTE of audio
}

# Global accumulation variable
TOTAL_SESSION_COST = 0.0

def reset_session_cost():
    """Resets the cost counter to zero (call at start of job)."""
    global TOTAL_SESSION_COST
    TOTAL_SESSION_COST = 0.0

def get_session_cost():
    return TOTAL_SESSION_COST

def log_openai_usage(stage_name, start_time, response):
    """
    Logs usage AND calculates cost for Chat Completions (GPT).
    """
    global TOTAL_SESSION_COST
    
    # Calculate duration
    import time
    duration = time.perf_counter() - start_time
    
    # Extract token usage
    usage = response.usage
    in_tokens = usage.prompt_tokens
    out_tokens = usage.completion_tokens
    model = response.model
    
    # Calculate Cost
    # Calculate Cost
    cost = 0.0
    
    # pricing keys are "gpt-5.2", "gpt-5-nano", etc.
    # The response.model might be specific like "gpt-5.2-turbo-2025..." so we check containment or exact match
    price_key = "gpt-5-nano" # Default
    
    for key in PRICING:
        if key in model:
            price_key = key
            break
            
    if price_key not in PRICING:
         print(f"   ⚠️ Warning: Model '{model}' not found in pricing. Using default '{price_key}'")

    input_price = PRICING[price_key]["input"] / 1_000_000
    output_price = PRICING[price_key]["output"] / 1_000_000
    
    cost = (in_tokens * input_price) + (out_tokens * output_price)
    TOTAL_SESSION_COST += cost

    # Log to console
    print(f"   📊 [{stage_name}] {in_tokens}in/{out_tokens}out | Time: {duration:.2f}s | Cost: ${cost:.5f}")

def log_whisper_cost(duration_seconds):
    """
    Calculates cost for Whisper (billed by minute).
    """
    global TOTAL_SESSION_COST
    minutes = duration_seconds / 60.0
    # Whisper rounds up to nearest second, but usually billed per minute
    cost = minutes * PRICING["whisper-1"]
    
    TOTAL_SESSION_COST += cost
    print(f"   📊 [WHISPER] Audio Duration: {minutes:.2f} min | Cost: ${cost:.4f}")