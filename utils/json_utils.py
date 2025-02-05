import json

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