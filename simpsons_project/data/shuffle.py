from pathlib import Path
import pandas as pd

in_path = Path("simpsons_project/data/processed/annotation_dataset.csv")
out_path = Path("simpsons_project/data/processed/annotation_dataset_shuffled.csv")

df = pd.read_csv(in_path)
shuffled_df = df.sample(frac=1, random_state=42).reset_index(drop=True)

shuffled_df.to_csv(out_path, index=False)
print(f"Shuffled {len(shuffled_df)} rows -> {out_path}")