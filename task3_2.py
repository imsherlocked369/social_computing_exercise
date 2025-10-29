def user_risk_analysis(user_id): 
 
     
    score = 0 
     
    #  existing behavior: sum risk from all posts/comments  
    user_posts = query_db('SELECT content FROM posts WHERE user_id = ?', (user_id,)) 
    user_comments = query_db('SELECT content FROM comments WHERE user_id = ?', (user_id,)) 
 
    # Collect texts for extra measure (duplicate-content spam) 
    all_texts = [] 
 
    for post in user_posts: 
        content_text = post['content'] or '' 
        all_texts.append(content_text) 
        _, post_risk_score = moderate_content(content_text) 
        score += post_risk_score 
             
    for comment in user_comments: 
        content_text = comment['content'] or '' 
        all_texts.append(content_text) 
        _, comment_risk_score = moderate_content(content_text) 
        score += comment_risk_score 
 
    # ADDED: Spam analysis 
    # add 2 points for each additional repeat beyond the first occurrence. 
    try: 
        import re 
        from collections import Counter 
 
        def _normalize_for_dup(s: str) -> str: 
            s = s.lower() 
            s = re.sub(r'\s+', ' ', s) 
            s = re.sub(r'[^a-z0-9\s]+', '', s)  # remove punctuations 
            return s.strip() 
 
        normalized = [_normalize_for_dup(t) for t in all_texts if t and t.strip()] 
        counts = Counter(n for n in normalized if n) 
        duplicate_penalty = sum((cnt - 1) * 2 for cnt in counts.values() if cnt > 1) 
        score += duplicate_penalty 
    except Exception: 
        pass 
 
    return float(score)