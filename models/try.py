import pandas as pd
from textblob import TextBlob

data = pd.read_csv("../datasets/labelled.csv")

data.head()

'''
Heading	Body	Category	URL
0	free speech not hate speech madras high court ...	madras high court issue significant remark ami...	Judiciary	https://www.indiatoday.in/law/high-courts/stor...
1	comment take context say us cop mock indian st...	seattle police officer guild friday come defen...	Crime	https://www.indiatoday.in/world/story/indian-s...
2	first meeting one nation one election committe...	first official meeting one nation one election...	Politics	https://www.indiatoday.in/india/story/one-nati...
3	us airlines flight depressurize midair plummet...	united airlines jet head rome turn around less...	Crime	https://www.indiatoday.in/world/story/us-fligh...
4	terrorist kill security force foil infiltratio...	three terrorist kill infiltration bid foil sec...	Crime	https://www.indiatoday.in/india/story/one-terr...
'''

sentiment_scores = []
sentiment_classes = []

for index, row in data.iterrows():
    heading = row["Heading"]
    body = row["Body"]

    combined_text = heading + " " + body

    # sentiment analysis using TextBlob
    analysis = TextBlob(combined_text)
    sentiment_score = analysis.sentiment.polarity

    # Classify the sentiment
    if sentiment_score > 0:
        sentiment_class = "positive"
    elif sentiment_score < 0:
        sentiment_class = "negative"
    else:
        sentiment_class = "neutral"

    sentiment_scores.append(sentiment_score)
    sentiment_classes.append(sentiment_class)
    
data["sentiment_score"] = sentiment_scores
data["sentiment_class"] = sentiment_classes

data.to_csv("news_data_with_sentiment.csv", index=False)