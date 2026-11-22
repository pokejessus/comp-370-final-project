import pandas as pd
"""
This is to calculate how many episodes per character and the mean words per line, for data/analys8is
"""

df = pd.read_csv("simpsons_project/data/processed/annotation_dataset.csv")

episodes_per_char = df.groupby("character")["episode_id"].nunique()
print("Distinct episodes per character:")
print(episodes_per_char)
print(f"Range [X-Y]: {episodes_per_char.min()}-{episodes_per_char.max()}")

mean_words = df["word_count"].mean()
print(f"Mean words per line [Z]: {mean_words:.2f}")