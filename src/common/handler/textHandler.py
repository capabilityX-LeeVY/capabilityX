import re
import string
import unicodedata

def textSimilarity(str1, str2):
    first_word1 = re.search(r'\b\w+\b', str1)
    first_word2 = re.search(r'\b\w+\b', str2)

    set1 = set(str1)
    set2 = set(str2)
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
        
    similarity = len(intersection) / len(union) if len(union) > 0 else 0
    if similarity > 0.7 and first_word1 and first_word2 and first_word1.group() != first_word2.group():
        return 0                    

    return similarity

def replaceSensitiveInfo(input_string):
    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    
    def replace_url(match):
        url = match.group(0)
        parts = url.split('/')
        for i in range(2, len(parts)):
            parts[i] = '***'
        return '/'.join(parts)
    
    input_string = url_pattern.sub(replace_url, input_string)
    digit_pattern = re.compile(r'\b\d{4,}\b')
    input_string = digit_pattern.sub(lambda x: '*' * len(x.group()), input_string)
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def replace_email(match):
        email = match.group(0)
        local, domain = email.split('@')
        local = '*' * len(local)
        domain_parts = domain.split('.')
        domain_parts[0] = '*' * len(domain_parts[0])
        domain = '.'.join(domain_parts)
        return f'{local}@{domain}'
    
    input_string = email_pattern.sub(replace_email, input_string)
    sensitive_pattern = re.compile(r'\b([A-Z]+_[A-Z]+)_(\d+)_([A-Z]+)(_SHA\d+)?\b')
    
    def replace_sensitive(match):
        if match.group(4):
            return f'{match.group(1)}_***_{match.group(3)}_SHA***'
        else:
            return f'{match.group(1)}_***_{match.group(3)}'
    
    input_string = sensitive_pattern.sub(replace_sensitive, input_string)
    
    return input_string

def preProcessString(input_string, timestamp_prefix="20250819151001_", total_length_limit=100):
    input_string = input_string.strip()
    # Replace newlines and tabs with a space before stripping other control characters
    input_string = input_string.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    forbidden_chars = r'<>:"/\\|?*[]+'
    processed = ''.join(
        char for char in input_string
        if char not in forbidden_chars and not unicodedata.category(char).startswith('C')
    )
    # Collapse multiple spaces into one
    processed = ' '.join(processed.split())
    max_content_length = total_length_limit - len(timestamp_prefix)
    if len(processed) > max_content_length:
        processed = processed[:max_content_length]
    if not processed:
        processed = "unknown"

    return f"{processed}"

def parse_position_from_description(description):
    """
    Parse 'X of Y' pattern from full description string.
    E.g. "Selected, 1 of 3, Use left/right key to navigate" -> (1, 3)
    Returns (current_pos, total) or (None, None) if not found.
    """
    if description is None:
        return None, None
    match = re.search(r'(\d+)\s+of\s+(\d+)', description)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None
