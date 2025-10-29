def recommend(user_id, filter_following): 
 
    import re, collections 
 
    liked_posts_content = query_db(''' 
        SELECT p.content FROM posts p 
        JOIN reactions r ON p.id = r.post_id 
        WHERE r.user_id = ? 
    ''', (user_id,)) 
 
     
    followed_rows = query_db('SELECT followed_id FROM follows WHERE follower_id = ?', 
(user_id,)) 
    followed_ids = [r['followed_id'] for r in followed_rows] 
    followed_set = set(followed_ids) 
 
    # If the user hasn't liked any posts return the 5 newest posts  
    if not liked_posts_content: 
        # Prefer newest posts from followed users if any; otherwise global newest 
        if filter_following and followed_ids: 
            placeholders = ','.join(['?'] * len(followed_ids)) 
            return query_db(f''' 
                SELECT p.id, p.content, p.created_at, u.username, u.id as user_id 
                FROM posts p JOIN users u ON p.user_id = u.id 
                WHERE p.user_id IN ({placeholders}) AND p.user_id != ? 
                ORDER BY p.created_at DESC LIMIT 5 
            ''', tuple(followed_ids + [user_id])) 
        else: 
            if followed_ids: 
                placeholders = ','.join(['?'] * len(followed_ids)) 
                followed_posts = query_db(f''' 
                    SELECT p.id, p.content, p.created_at, u.username, u.id as user_id 
                    FROM posts p JOIN users u ON p.user_id = u.id 
                    WHERE p.user_id IN ({placeholders}) AND p.user_id != ? 
                    ORDER BY p.created_at DESC LIMIT 5 
                ''', tuple(followed_ids + [user_id])) 
                if followed_posts: 
                    return followed_posts 
            return query_db(''' 
                SELECT p.id, p.content, p.created_at, u.username, u.id as user_id 
                FROM posts p JOIN users u ON p.user_id = u.id 
                WHERE p.user_id != ? ORDER BY p.created_at DESC LIMIT 5 
            ''', (user_id,)) 
 
     
    word_counts = collections.Counter() 
    # A simple list of common words to ignore 
    stop_words = {'a', 'an', 'the', 'in', 'on', 'is', 'it', 'to', 'for', 'of', 'and', 'with'} 
     
    for post in liked_posts_content: 
         
        words = re.findall(r'\b\w+\b', (post['content'] or '').lower()) 
        for word in words: 
            if word not in stop_words and len(word) > 2: 
                word_counts[word] += 1 
     
    top_keywords = [word for word, _ in word_counts.most_common(10)] 
 
    query = "SELECT p.id, p.content, p.created_at, u.username, u.id as user_id FROM posts p JOIN 
users u ON p.user_id = u.id" 
    params = [] 
     
     
    if filter_following: 
        query += " WHERE p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = 
?)" 
        params.append(user_id) 
         
    all_other_posts = query_db(query, tuple(params)) 
     
    recommended_posts = [] 
    liked_post_ids = {post['id'] for post in query_db('SELECT post_id as id FROM reactions WHERE 
user_id = ?', (user_id,))} 
 
    # added 
    scored_candidates = [] 
    for post in all_other_posts: 
        if post['id'] in liked_post_ids or post['user_id'] == user_id: 
            continue 
 
        content_lc = (post['content'] or '').lower() 
        content_score = sum(1 for kw in top_keywords if kw in content_lc) 
        follow_boost = 2 if post['user_id'] in followed_set else 0 
        total_score = content_score + follow_boost 
 
        if total_score > 0: 
            scored_candidates.append((total_score, post)) 
 
    
    scored_candidates.sort(key=lambda t: (t[0], t[1]['created_at']), reverse=True) 
    recommended_posts = [p for _, p in scored_candidates][:5] 
 
    # added 
    if len(recommended_posts) < 5: 
        have_ids = {p['id'] for p in recommended_posts} 
         
        backfill = sorted( 
            [p for p in all_other_posts if p['id'] not in have_ids and p['id'] not in liked_post_ids and 
p['user_id'] != user_id], 
            key=lambda p: ((1 if p['user_id'] in followed_set else 0), p['created_at']), 
            reverse=True 
        ) 
        for p in backfill: 
            if len(recommended_posts) >= 5: 
                break 
            recommended_posts.append(p) 
 
    recommended_posts.sort(key=lambda p: p['created_at'], reverse=True) 
    return recommended_posts[:5]