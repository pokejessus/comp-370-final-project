import pandas as pd
"""
This is to double check
"""
df = pd.read_csv("simpsons_project/data/processed/annotation_dataset.csv")
print(df["character"].value_counts())
print("Total:", len(df))