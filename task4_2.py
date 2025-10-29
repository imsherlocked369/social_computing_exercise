import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# Download the VADER lexicon (quiet to avoid noisy logs)
nltk.download('vader_lexicon', quiet=True)

# ---- Load ----
df = pd.read_csv('reviews.csv')

# Validate expected columns early (same names you used)
required = {'Review', 'location', 'Date'}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"reviews.csv is missing columns: {missing}")

# Clean review text for VADER
df['Review'] = df['Review'].fillna('').astype(str)

# ---- VADER sentiment ----
sia = SentimentIntensityAnalyzer()
df['sentiment_score'] = df['Review'].apply(lambda t: sia.polarity_scores(t)['compound'])

# ---- Per-location stats (count + mean) ----
location_stats = df.groupby('location')['sentiment_score'].agg(['count', 'mean'])

# Filter locations with at least 3 reviews
MIN_REVIEWS = 3
filtered_sentiment_by_location = location_stats[location_stats['count'] >= MIN_REVIEWS]

# Sort by mean sentiment (desc)
sorted_filtered_sentiment = filtered_sentiment_by_location.sort_values(by='mean', ascending=False)

print("Average sentiment score for each location with at least 3 reviews:")
print(sorted_filtered_sentiment)

# ---- Plot change of rating over time ----

# Clean/parse dates robustly (keep your intent, safer ops)
# - strip spaces and double quotes even if Date isn't string-typed
date_clean = df['Date'].astype(str).str.strip().str.replace('"', '', regex=False)
df['Date'] = pd.to_datetime(date_clean, errors='coerce')

# Drop rows with invalid dates, set index for resampling
df = df.dropna(subset=['Date']).copy()
df.set_index('Date', inplace=True)
df.sort_index(inplace=True)

# Resample by calendar year-end ('Y' as in your code) and compute mean sentiment
yearly_sentiment = df['sentiment_score'].resample('Y').mean()

# Create plot
plt.figure(figsize=(6, 4))
yearly_sentiment.plot(marker='o', linestyle='-')

# Formatting
plt.axhline(0, color='grey', linestyle='--', linewidth=0.8)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.title('Average Sentiment by Year')
plt.xlabel('Year')
plt.ylabel('Mean VADER Compound Score')
plt.tight_layout()

# Display the plot
plt.show()
