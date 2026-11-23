import pandas as pd
import numpy as np
import re
from collections import Counter
import math

df = pd.read_csv("data/processed/annotation_dataset_shuffled.csv")

# ---- TEMPORARY: fake topics for testing. DELETE once real annotations exist ----
topics = ["Religion/Faith", "Social Life", "Conflict/Safety", "Everyday Conversation",
          "School/Education", "Food", "Business/Finance"]
rng = np.random.default_rng(42)            # random number generator; 42 = fixed seed so results repeat
df["topic"] = rng.choice(topics, size=len(df))   # give every row a random topic
# ---------------------------------------------------------------------------------

# Overall: what share of all 1,400 lines falls in each topic?
print((df["topic"].value_counts(normalize=True) * 100).round(1))

# Per character: number of lines in each topic
counts = pd.crosstab(df["character"], df["topic"])
print(counts)

# Per character: percentage of that character's lines in each topic (each row adds to 100)
percent = pd.crosstab(df["character"], df["topic"], normalize="index") * 100
print(percent.round(1))

# ---------- TF-IDF part 1: count words per topic ----------

def tokenize(text):
    # lowercase the line, then pull out every run of letters/apostrophes as a word
    return re.findall(r"[a-z']+", text.lower())

word_counts = {}                                  # will map topic -> word counts
for topic, group in df.groupby("topic"):          # loop over the lines one topic at a time
    counter = Counter()
    for line in group["dialogue"]:
        counter.update(tokenize(line))            # add this line's words to the topic's tally
    word_counts[topic] = counter

# Check: show the 5 most common words in each topic
for topic, counter in word_counts.items():
    print(topic, counter.most_common(5))


# ---------- TF-IDF part 2: score words and keep the top 10 per topic ----------

N = len(word_counts)                     # number of topics (7)

# For each word, count how many topics it appears in at least once
topics_containing = Counter()
for counter in word_counts.values():
    topics_containing.update(counter.keys())   # .keys() = each distinct word, counted once per topic

top_words = {}
for topic, counter in word_counts.items():
    scores = {}
    for word, tf in counter.items():
        idf = math.log(N / topics_containing[word])
        scores[word] = tf * idf
    top10 = sorted(scores, key=scores.get, reverse=True)[:10]
    top_words[topic] = top10
    print(topic, [(w, round(scores[w], 2)) for w in top10])