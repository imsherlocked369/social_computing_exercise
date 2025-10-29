import pandas as pd
from gensim.corpora import Dictionary
from gensim.models.ldamodel import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
import math

def main():
    # Download necessary NLTK data
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)

    # Load data
    data = pd.read_csv("posts.csv")

   
    if 'content' not in data.columns:
        raise ValueError("posts.csv must contain a 'content' column.")
    data['content'] = data['content'].fillna('').astype(str)

  
    stop_words = set(stopwords.words('english'))

    '
    stop_words.update([
        'would', 'best', 'always', 'amazing', 'bought', 'quick', 'people', 'new', 'fun', 'think', 'know',
        'believe', 'many', 'thing', 'need', 'small', 'even', 'make', 'love', 'mean', 'fact', 'question',
        'time', 'reason', 'also', 'could', 'true', 'well',  'life', 'said', 'year', 'going', 'good',
        'really', 'much', 'want', 'back', 'look', 'article', 'host', 'university', 'reply', 'thanks',
        'mail', 'post', 'please'
    ])

    
    lemmatizer = WordNetLemmatizer()

   
    bow_list = []

    for _, row in data.iterrows():
        text = row['content']
        tokens = word_tokenize(text.lower())  # tokenise 
        tokens = [t for t in tokens if t.isalpha()]  
        tokens = [t for t in tokens if len(t) > 2]   
        tokens = [t for t in tokens if t not in stop_words]  
        tokens = [lemmatizer.lemmatize(t) for t in tokens]   
       
        if len(tokens) > 0:
            bow_list.append(tokens)

    if not bow_list:
        raise ValueError("No documents left after preprocessing. Check input text and stopwords.")

   
    dictionary = Dictionary(bow_list)
   
    dictionary.filter_extremes(no_below=2, no_above=0.3)

   
    valid_ids = set(dictionary.token2id.keys())
    texts_filtered = [[t for t in doc if t in dictionary.token2id] for doc in bow_list]

    # Build corpus and drop empty bows created by filtering
    corpus = [dictionary.doc2bow(tokens) for tokens in texts_filtered]
    nonempty = [(doc, bow) for doc, bow in zip(texts_filtered, corpus) if len(bow) > 0]
    if not nonempty:
        raise ValueError("All documents became empty after dictionary filtering.")
    texts_filtered, corpus = zip(*nonempty)
    texts_filtered, corpus = list(texts_filtered), list(corpus)

 
    K = 10

    # Train LDA model 
    lda = LdaModel(
        corpus=corpus,
        num_topics=K,
        id2word=dictionary,
        passes=10,
        random_state=2,
        alpha='auto',
        eta='auto'
    )


    try:
        coherence_model = CoherenceModel(model=lda, texts=texts_filtered, dictionary=dictionary, coherence='c_v')
        coherence_score = coherence_model.get_coherence()
        print(f'c_v coherence (K={K}): {coherence_score:.4f}')
    except Exception as e:
        print("Could not compute coherence:", e)

    
    print(f'These are the words most representative of each of the {K} topics:')
    for i, topic in lda.print_topics(num_words=5):
        print(f"Topic {i}: {topic}")

   
    topic_counts = [0] * K  
    total_docs = len(corpus)

    for bow in corpus:
        topic_dist = lda.get_document_topics(bow, minimum_probability=0.0)  
        if not topic_dist:
            continue  
        dominant_topic = max(topic_dist, key=lambda x: x[1])[0]  
        topic_counts[dominant_topic] += 1  

   
    print("\nTopic popularity (document counts and shares):")
    for i, count in enumerate(topic_counts):
        share = count / total_docs if total_docs > 0 else 0.0
        print(f"Topic {i}: {count} posts ({share:.2%})")

if __name__ == '__main__':
    main()

