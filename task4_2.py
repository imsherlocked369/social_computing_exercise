import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# Download the VADER lexicon 
nltk.download('vader_lexicon', quiet=True)


df = pd.read_csv('reviews.csv')


required = {'Review', 'location', 'Date'}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"reviews.csv is missing columns: {missing}")


df['Review'] = df['Review'].fillna('').astype(str)


sia = SentimentIntensityAnalyzer()
df['sentiment_score'] = df['Review'].apply(lambda t: sia.polarity_scores(t)['compound'])


location_stats = df.groupby('location')['sentiment_score'].agg(['count', 'mean'])


MIN_REVIEWS = 3
filtered_sentiment_by_location = location_stats[location_stats['count'] >= MIN_REVIEWS]

sorted_filtered_sentiment = filtered_sentiment_by_location.sort_values(by='mean', ascending=False)

print("Average sentiment score for each location with at least 3 reviews:")
print(sorted_filtered_sentiment)

date_clean = df['Date'].astype(str).str.strip().str.replace('"', '', regex=False)
df['Date'] = pd.to_datetime(date_clean, errors='coerce')


df = df.dropna(subset=['Date']).copy()
df.set_index('Date', inplace=True)
df.sort_index(inplace=True)

yearly_sentiment = df['sentiment_score'].resample('Y').mean()

#  plot
plt.figure(figsize=(6, 4))
yearly_sentiment.plot(marker='o', linestyle='-')
plt.axhline(0, color='grey', linestyle='--', linewidth=0.8)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.title('Average Sentiment by Year')
plt.xlabel('Year')
plt.ylabel('Mean VADER Compound Score')
plt.tight_layout()
plt.show()

