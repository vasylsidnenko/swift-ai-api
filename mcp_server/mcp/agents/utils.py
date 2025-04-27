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

def escape_newlines_in_json_strings(text):
    """
    Escapes real newlines (U+000A) and carriage returns (U+000D) inside JSON string literals with \\n and \\r respectively.
    Only affects content inside double-quoted strings.
    Example:
        '{"code": "line1\nline2"}' -> '{"code": "line1\\nline2"}'
        '{"code": "line1\rline2"}' -> '{"code": "line1\\rline2"}'
    """
    result = []
    in_string = False
    escape = False
    for c in text:
        if not in_string:
            if c == '"':
                in_string = True
            result.append(c)
        else:
            if escape:
                result.append(c)
                escape = False
            elif c == '\\':
                result.append(c)
                escape = True
            elif c == '"':
                in_string = False
                result.append(c)
            elif c == '\n':
                result.append('\\n')
            elif c == '\r':
                result.append('\\r')
            else:
                result.append(c)
    return ''.join(result)

# Example usage:
# fixed = escape_newlines_in_json_strings(json_str)

def fix_missing_commas_in_json(text):
    """
    Inserts missing commas between JSON values and keys if absent.
    Example:
        '{"a": 1 "b": 2}' -> '{"a": 1, "b": 2}'
    This is a best-effort fix for common AI mistakes.
    """
    import re
    # Insert comma between a closing quote/number/} and a quote/[/letter
    # Examples: "..." "key":  -> "...", "key":
    #           123 "key":    -> 123, "key":
    #           } "key":      -> }, "key":
    pattern = r'([\]"|\d|\})\s+(?=[\"]|\[|\{)'  # after string/number/} before key/array/object
    return re.sub(pattern, r'\1, ', text)

# Example usage:
# fixed = fix_missing_commas_in_json(json_str)

def fix_omitted_elements_in_json(text):
    """
    Removes omitted elements in JSON like '"key": ,' and trailing commas before }} or ]].
    Example:
        '{"a": , "b": 1}' -> '{"b": 1}'
        '{"a": 1,}' -> '{"a": 1}'
        '[1, 2,]' -> '[1, 2]'
    """
    import re
    # Remove key-value pairs with omitted value
    text = re.sub(r'"[^"]+"\s*:\s*,', '', text)
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text

# Example usage:
# fixed = fix_omitted_elements_in_json(json_str)
