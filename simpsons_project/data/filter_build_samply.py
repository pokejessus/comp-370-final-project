import re
from pathlib import Path
import pandas as pd

# Configuration
INPUT_CSV = Path("simpsons_project/data/raw/csv/script_lines.csv")
OUT_DIR = Path("simpsons_project/data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Picked these characters, include a couple nicknames
CHARACTER_MAP = {
    "Mr. Burns": ["C. Montgomery Burns", "Mr. Burns"],
    "Moe": ["Moe Szyslak"],
    "Skinner": ["Seymour Skinner", "Principal Skinner"],
    "Flanders": ["Ned Flanders"],
}

MIN_LINES_PER_CHAR = 300
SAMPLE_PER_CHAR = 350   # 350 per character = 1,400 total (safe buffer >= 300)
OPEN_CODE_PER_CHAR = 100
MIN_WORDS = 3
RANDOM_SEED = 42

# We picked these trivial words, otherwise picking sentences above a threshold would exclude too many relevent sentences
TRIVIAL_EXACT = {
    "uh", "um", "er", "hmm", "huh", "ah", "oh", "ooh", "ow", "ugh", 
    "aw", "eh", "whoa", "wow", "yay", "boo", "sigh", "gasp", "groan", 
    "cough", "yes", "yeah", "yep", "yup", "no", "nope", "nah", "ok", 
    "okay", "sure", "right", "fine", "alright", "all right", "true", 
    "maybe", "please", "thanks", "thank you", "sorry", "excuse me", "pardon",
    "hi", "hey", "hello", "bye", "goodbye", "see ya", "d'oh", "excellent",
    "release the hounds", "smithers", "hi-diddly-ho", "okily-dokily", 
    "uh oh", "oh no", "oh boy", "my god", "good lord", "what", "why", 
    "how", "who", "where", "when", "really"
}

# Not all columns are relevent, so decided to keep these, more details in report. 
KEEP_COLUMNS = [
    "id",
    "episode_id",
    "number",
    "character",
    "location",
    "dialogue",
    "word_count",
    "topic",
]


def clean_dialogue(text: str) -> str:
    """
    Keep readable punctuation/casing, remove parenthetical stage directions.
    """

    if not isinstance(text, str):
        return ""
    no_parens = re.sub(r"\([^)]*\)", " ", text)
    return re.sub(r"\s+", " ", no_parens).strip()



def is_non_trivial(cleaned_text: str, min_words: int = MIN_WORDS) -> bool:
    """
    Filter out stage-only lines, pure interjections, and minimal banter.
    """

    if not cleaned_text:
        return False

    norm = re.sub(r"[^a-zA-Z0-9'\s-]", "", cleaned_text).lower()
    norm = re.sub(r"\s+", " ", norm).strip()

    if not norm or norm in TRIVIAL_EXACT:
        return False

    words = [w for w in norm.split(" ") if w]
    if len(words) < min_words:
        return False

    # To remove words like la la la, blah blah blah, proud of that :D
    if len(words) <= 4 and (len(set(words)) / len(words)) <= 0.5:
        return False

    return True


def main() -> None:
    df = pd.read_csv(INPUT_CSV, low_memory=False)

    raw_to_canonical = {
        raw_name: canon
        for canon, raw_list in CHARACTER_MAP.items()
        for raw_name in raw_list
    }

    speaking_mask = df["speaking_line"].astype(str).str.strip().str.lower() == "true"
    df["character"] = df["raw_character_text"].map(raw_to_canonical)
    sub = df[speaking_mask & df["character"].notna()].copy()

    # Use spoken_words directly (already omits "Character: " prefix and keeps punctuation)
    sub["dialogue"] = sub["spoken_words"].apply(clean_dialogue)
    sub["location"] = sub["raw_location_text"].fillna("Unknown").astype(str).str.strip()
    sub["word_count"] = sub["dialogue"].apply(lambda s: len(s.split()))
    sub["non_trivial"] = sub["dialogue"].apply(is_non_trivial)

    summary = (
        sub.groupby("character")
        .agg(total_speaking=("id", "count"), non_trivial_lines=("non_trivial", "sum"))
        .reset_index()
    )
    print("=== Speaking vs. Non-Trivial Lines ===") 
    print(summary.to_string(index=False)) # printing the number of non-trivial lines and total speaking

    filtered = sub[sub["non_trivial"]].copy()

    # Here, use an unbiased random sample across episodes for each character
    sampled_parts = []
    for canon in CHARACTER_MAP:
        char_df = filtered[filtered["character"] == canon]
        assert len(char_df) >= MIN_LINES_PER_CHAR, f"{canon} has < {MIN_LINES_PER_CHAR} lines"
        sampled_parts.append(
            char_df.sample(n=min(SAMPLE_PER_CHAR, len(char_df)), random_state=RANDOM_SEED)
        )

    sampled = (
        pd.concat(sampled_parts, ignore_index=True)
        .sort_values(["character", "episode_id", "number"])
        .reset_index(drop=True)
    )
    sampled["topic"] = ""
    sampled = sampled[KEEP_COLUMNS]

    # Save main annotation dataset
    sampled.to_csv(OUT_DIR / "annotation_dataset.csv", index=False, encoding="utf-8-sig")

    # Save 100 line per character open-coding subset. There are 400 lines in total
    open_code = (
        pd.concat(
            [
                sampled[sampled["character"] == canon].sample(
                    n=OPEN_CODE_PER_CHAR, random_state=RANDOM_SEED + 1
                )
                for canon in CHARACTER_MAP
            ],
            ignore_index=True,
        )
        .sort_values(["character", "episode_id", "number"])
        .reset_index(drop=True)
    )
    open_code.to_csv(OUT_DIR / "open_coding_400.csv", index=False, encoding="utf-8-sig")

    print(f"\nSaved clean annotation_dataset.csv ({len(sampled)} rows, {len(KEEP_COLUMNS)} cols)")
    print(f"Saved clean open_coding_400.csv ({len(open_code)} rows, {len(KEEP_COLUMNS)} cols)")


if __name__ == "__main__":
    main()