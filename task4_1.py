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
    # Download necessary NLTK data, without these the below functions wouldn't work
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)

    # Load data
    data = pd.read_csv("posts.csv")

    # Make sure 'content' exists and is stringy
    if 'content' not in data.columns:
        raise ValueError("posts.csv must contain a 'content' column.")
    data['content'] = data['content'].fillna('').astype(str)

    # Get a basic stopword list (use a set for O(1) membership)
    stop_words = set(stopwords.words('english'))

    # Add extra words to make our analysis even better
    # NOTE: fixed the missing comma between 'quick' and 'people'
    stop_words.update([
        'would', 'best', 'always', 'amazing', 'bought', 'quick', 'people', 'new', 'fun', 'think', 'know',
        'believe', 'many', 'thing', 'need', 'small', 'even', 'make', 'love', 'mean', 'fact', 'question',
        'time', 'reason', 'also', 'could', 'true', 'well',  'life', 'said', 'year', 'going', 'good',
        'really', 'much', 'want', 'back', 'look', 'article', 'host', 'university', 'reply', 'thanks',
        'mail', 'post', 'please'
    ])

    # this object will help us lemmatise words (i.e. get the word stem)
    lemmatizer = WordNetLemmatizer()

    # after the below for loop, we will transform each post into "bags of words" where each BOW is a set of words from one post 
    bow_list = []

    for _, row in data.iterrows():
        text = row['content']
        tokens = word_tokenize(text.lower())  # tokenise (i.e. get the words from the post)
        tokens = [t for t in tokens if t.isalpha()]  # keep only alphabetic
        tokens = [t for t in tokens if len(t) > 2]   # filter out words with less than 3 letters
        tokens = [t for t in tokens if t not in stop_words]  # filter out stopwords
        tokens = [lemmatizer.lemmatize(t) for t in tokens]   # lemmatise (simple noun-default)
        # if there's at least 1 word left for this post, append to list
        if len(tokens) > 0:
            bow_list.append(tokens)

    if not bow_list:
        raise ValueError("No documents left after preprocessing. Check input text and stopwords.")

    # Create dictionary and corpus
    dictionary = Dictionary(bow_list)
    # Filter words that appear less than 2 times or in more than 30% of posts
    dictionary.filter_extremes(no_below=2, no_above=0.3)

    # Rebuild texts to remove tokens dropped by filter_extremes
    valid_ids = set(dictionary.token2id.keys())
    texts_filtered = [[t for t in doc if t in dictionary.token2id] for doc in bow_list]

    # Build corpus and drop empty bows created by filtering
    corpus = [dictionary.doc2bow(tokens) for tokens in texts_filtered]
    nonempty = [(doc, bow) for doc, bow in zip(texts_filtered, corpus) if len(bow) > 0]
    if not nonempty:
        raise ValueError("All documents became empty after dictionary filtering.")
    texts_filtered, corpus = zip(*nonempty)
    texts_filtered, corpus = list(texts_filtered), list(corpus)

    # -----------------------------
    # Exercise 4.1 requirement: use 10 topics
    # -----------------------------
    K = 10

    # Train LDA model (slightly better defaults)
    lda = LdaModel(
        corpus=corpus,
        num_topics=K,
        id2word=dictionary,
        passes=10,
        random_state=2,
        alpha='auto',
        eta='auto'
    )

    # Optional: evaluate coherence for sanity
    try:
        coherence_model = CoherenceModel(model=lda, texts=texts_filtered, dictionary=dictionary, coherence='c_v')
        coherence_score = coherence_model.get_coherence()
        print(f'c_v coherence (K={K}): {coherence_score:.4f}')
    except Exception as e:
        print("Could not compute coherence:", e)

    # Show top 5 most representative words per topic
    print(f'These are the words most representative of each of the {K} topics:')
    for i, topic in lda.print_topics(num_words=5):
        print(f"Topic {i}: {topic}")

    # Determine popularity: dominant topic per document
    topic_counts = [0] * K  # one counter per topic
    total_docs = len(corpus)

    for bow in corpus:
        topic_dist = lda.get_document_topics(bow, minimum_probability=0.0)  # list of (topic_id, probability)
        if not topic_dist:
            continue  # skip if distribution is empty (shouldn't happen with minimum_probability=0.0)
        dominant_topic = max(topic_dist, key=lambda x: x[1])[0]  # find the top probability
        topic_counts[dominant_topic] += 1  # add 1 to the most probable topic's counter

    # Display the topic counts and shares
    print("\nTopic popularity (document counts and shares):")
    for i, count in enumerate(topic_counts):
        share = count / total_docs if total_docs > 0 else 0.0
        print(f"Topic {i}: {count} posts ({share:.2%})")

if __name__ == '__main__':
    main()
