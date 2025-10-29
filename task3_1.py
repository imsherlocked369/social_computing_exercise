def moderate_content(content): 
    original_content = content 
    score = 0.0 
    #  Tier 1 words  
    if TIER1_WORDS: 
        TIER1_PATTERN = r'\b(?:' + '|'.join(re.escape(w) for w in TIER1_WORDS) + r')\b' 
        if re.search(TIER1_PATTERN, original_content, flags=re.IGNORECASE): 
            return "[content removed due to severe violation]", 5.0 
 
    #  Tier 2 phrases  
    if TIER2_PHRASES: 
        TIER2_PATTERN = r'(?:' + '|'.join(re.escape(p) for p in TIER2_PHRASES) + r')' 
        if re.search(TIER2_PATTERN, original_content, flags=re.IGNORECASE): 
            return "[content removed due to spam/scam policy]", 5.0 
 
    # Tier 3 words  
    TIER3_PATTERN = r'\b(' + '|'.join(re.escape(w) for w in TIER3_WORDS) + r')\b' 
    matches = re.findall(TIER3_PATTERN, original_content, flags=re.IGNORECASE) 
    score += len(matches) * 2.0 
    moderated_content = re.sub( 
        TIER3_PATTERN, 
        lambda m: '*' * len(m.group(0)), 
        original_content, 
        flags=re.IGNORECASE 
    ) 
 
    # Rule 1.2.2 
    URL_PATTERN = r'(?i)\b(?:https?://|www\.)[^\s<>()]+' 
    url_hits = re.findall(URL_PATTERN, moderated_content) 
    if url_hits: 
        score += len(url_hits) * 2.0 
        moderated_content = re.sub(URL_PATTERN, '[link removed]', moderated_content) 
 
    # Rule 1.2.3 
    letters = [c for c in original_content if c.isalpha()] 
    if len(letters) > 15: 
        upper_ratio = sum(1 for c in letters if c.isupper()) / float(len(letters)) 
        if upper_ratio > 0.70: 
             score += 0.5 
 
    # Added: Remove content if high risk  
    # If score exceeds the "high risk" threshold (>5.0), remove the content entirely 
    if score > 5.0: 
        moderated_content = "[content removed due to policy violations]" 
 
    # Return the updated content string and the score 
    return moderated_content, float(score) 
 
    # Return the updated content string and the score 
    return moderated_content, float(score)