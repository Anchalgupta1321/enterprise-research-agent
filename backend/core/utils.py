import json
import re

def parse_json_from_llm(text):
    """Robustly parses JSON from LLM output, handling markdown blocks and other weirdness."""
    # Sometimes LangChain returns a list of content blocks instead of a string
    if isinstance(text, list):
        # Extract the actual text from the blocks
        text_parts = []
        for block in text:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
        text = "".join(text_parts)
    elif not isinstance(text, str):
        text = str(text)
        
    text = text.strip()
    
    # Try to find a JSON block using regex
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass # Fall through to fallback
            
    # Fallback: try to find the first [ or { and the last ] or }
    start_list = text.find('[')
    start_obj = text.find('{')
    
    start = -1
    if start_list != -1 and start_obj != -1:
        start = min(start_list, start_obj)
    elif start_list != -1:
        start = start_list
    elif start_obj != -1:
        start = start_obj
        
    end_list = text.rfind(']')
    end_obj = text.rfind('}')
    
    end = max(end_list, end_obj)
    
    if start != -1 and end != -1 and end >= start:
        json_str = text[start:end+1].strip()
        return json.loads(json_str)
        
    # Absolute fallback
    return json.loads(text)

def robust_invoke(chain, inputs, max_retries=5):
    """Manually handles rate limits since LangChain's internal retry sometimes fails on new SDKs."""
    import time
    for attempt in range(max_retries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                if attempt == max_retries - 1:
                    raise
                # Extract wait time if present, otherwise default to 15s
                wait_time = 15
                import re
                match = re.search(r'retry in ([\d\.]+)s', error_str)
                if match:
                    wait_time = float(match.group(1)) + 1
                print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt+1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                raise
