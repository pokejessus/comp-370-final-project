from pathlib import Path
import pandas as pd

DATA_DIR = Path("simpsons_project/data")
episodes = pd.read_csv(DATA_DIR / "raw/csv/episodes.csv", low_memory=False)
lines = pd.read_csv(DATA_DIR / "raw/csv/script_lines.csv", low_memory=False)

ep_id_col = "id" if "id" in episodes.columns else "episode_id"

# Ensure season is numeric
episodes["season_num"] = pd.to_numeric(episodes["season"], errors="coerce")

total_episodes_in_csv = episodes[ep_id_col].nunique()
min_season = int(episodes["season_num"].min())
max_season = int(episodes["season_num"].max())
num_seasons = int(episodes["season_num"].nunique())

# Episodes that actually have rows in script_lines.csv
ep_with_lines = episodes[episodes[ep_id_col].isin(lines["episode_id"].unique())]

print(f"Total unique episodes in episodes.csv: {total_episodes_in_csv}")
print(f"Episodes with lines in script_lines.csv: {ep_with_lines[ep_id_col].nunique()}")
print(f"Season range: Season {min_season} to Season {max_season} ({num_seasons} distinct seasons)")

print("\n=== Episodes per season (in episodes.csv vs. with script lines) ===")
by_season = (
    episodes.groupby("season_num")[ep_id_col]
    .nunique()
    .rename("episodes_in_csv")
    .to_frame()
)
by_season["episodes_with_lines"] = (
    ep_with_lines.groupby("season_num")[ep_id_col].nunique()
)
by_season["episodes_with_lines"] = by_season["episodes_with_lines"].fillna(0).astype(int)
print(by_season.to_string())
print(f"Total episodes with lines: {ep_with_lines[ep_id_col].nunique()} / Total in episodes.csv: {total_episodes_in_csv}")