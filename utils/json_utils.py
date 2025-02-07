import json
import re
def fix_malformed_json(response_text):
    try:
        return json.loads(response_text)  
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}") 
        fixed_text = response_text.strip().strip("`")  # try remove bad symbols
        try:
            return json.loads(fixed_text)  # try again JSON
        except json.JSONDecodeError:
            return {"error": "Bad JSON"}
        
def extract_json(text):
    """
    Get right JSON from string with ```json ... ```
    """
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    return match.group(1) if match else text