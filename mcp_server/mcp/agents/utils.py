import re

def escape_json_strings(obj):
    """
    Recursively escape all string values in a Python object to be valid JSON strings.
    Useful for cleaning up AI responses before parsing as JSON.
    """
    if isinstance(obj, dict):
        return {k: escape_json_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [escape_json_strings(v) for v in obj]
    elif isinstance(obj, str):
        # Escape backslashes, double quotes, newlines, tabs, etc.
        s = obj
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        # Remove raw newlines/tabs if present
        s = re.sub(r'(?<!\\)\n', r'\\n', s)
        s = re.sub(r'(?<!\\)\t', r'\\t', s)
        s = re.sub(r'(?<!\\)\r', r'\\r', s)
        return s
    else:
        return obj


def remove_triple_backticks_from_outer_markdown(text):
    """
    Remove triple backticks (``` and ```json, ```swift, etc.) only if they are used to wrap the ENTIRE response (i.e. markdown block at the outermost level).
    Do NOT remove triple backticks inside JSON string values.
    """
    import re
    # Remove only the outermost markdown block if present
    pattern = r'^```[a-zA-Z]*\s*([\s\S]*?)\s*```$'
    match = re.match(pattern, text.strip())
    if match:
        return match.group(1)
    return text

# Example usage:
# cleaned = remove_triple_backticks_from_outer_markdown(raw_ai_response_text)


def fix_unterminated_strings_in_json(text):
    """
    Fixes unterminated string literals in JSON-like text by adding a closing quote if needed.
    This is a best-effort fix for AI-generated, truncated, or malformed JSON.
    """
    import re
    result = []
    in_string = False
    escape = False
    for i, c in enumerate(text):
        if not in_string:
            if c == '"':
                in_string = True
                result.append(c)
            else:
                result.append(c)
        else:
            result.append(c)
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                in_string = False
    # If we are still in a string at the end, close it
    if in_string:
        result.append('"')
    return ''.join(result)

# Example usage:
# fixed = fix_unterminated_strings_in_json(json_str)
