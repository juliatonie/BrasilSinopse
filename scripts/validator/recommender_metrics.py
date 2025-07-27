import os
import subprocess
import json
import pandas as pd
import math

# === CONFIG ===
CSV_INPUT = './inputs.csv'
GENRES_FILE = '../../data/movies.csv'
USER_INPUT_COL = 'input_user'
ORIGINAL_ID_COL = 'id'
TITLE_COL = 'title'
RECOMMENDER = './run_recommender.js'
TOP_K = 5
OUTPUT_CSV = './metrics_summary.csv'

# === Load movie genres ===
def load_movie_genres():
    df = pd.read_csv(GENRES_FILE)
    df['id'] = df['id'].astype(str).str.strip()
    df['genres'] = df['genres'].astype(str).apply(
        lambda x: [g.strip().lower() for g in x.split(',')] if x.strip() else []
    )
    return {film_id: genres for film_id, genres in zip(df['id'], df['genres']) if genres}

# === Call Node.js recommender ===
def get_recommendations(user_input):
    try:
        result = subprocess.run(
            ['node', RECOMMENDER, user_input],
            capture_output=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout.strip()
        return json.loads(output) if output else []
    except Exception:
        return []

# === Genre helpers ===
def clean_genres(value):
    if isinstance(value, list):
        return [g.strip().lower() for g in value if g.strip()]
    elif isinstance(value, str):
        return [g.strip().lower() for g in value.split(',') if g.strip()]
    return []

# === Metrics ===
def genre_binary_score(input_genres, recommendations):
    input_set = set(input_genres)
    if not input_set:
        return None
    hits, valid = 0, 0
    for movie in recommendations:
        rec_genres = set(clean_genres(movie.get('genres', [])))
        if not rec_genres:
            continue
        valid += 1
        if input_set & rec_genres:
            hits += 1
    return hits / valid if valid else None

def genre_proportional_score(input_genres, recommendations):
    input_set = set(input_genres)
    if not input_set:
        return None
    proportions = []
    for movie in recommendations:
        rec_genres = set(clean_genres(movie.get('genres', [])))
        if not rec_genres:
            continue
        proportions.append(len(input_set & rec_genres) / len(input_set))
    return sum(proportions) / len(proportions) if proportions else None

def precision_at_k(recommendations, original_id):
    ids = [str(m.get('id', '')).strip() for m in recommendations[:TOP_K]]
    return 1.0 if original_id in ids else 0.0

def recall_at_k(recommendations, original_id):
    ids = [str(m.get('id', '')).strip() for m in recommendations[:TOP_K]]
    return 1.0 if original_id in ids else 0.0

def mrr_score(recommendations, original_id):
    ids = [str(m.get('id', '')).strip() for m in recommendations]
    for rank, mid in enumerate(ids, start=1):
        if mid == original_id:
            return 1.0 / rank
    return 0.0

def ndcg_score(recommendations, original_id):
    ids = [str(m.get('id', '')).strip() for m in recommendations]
    for rank, mid in enumerate(ids, start=1):
        if mid == original_id:
            return 1 / math.log2(rank + 1)
    return 0.0

# === Main evaluation ===
def process_all_inputs():
    df_input = pd.read_csv(CSV_INPUT, sep=",", quotechar='"', encoding="utf-8")
    genre_map = load_movie_genres()

    total = 0
    precision_sum = 0.0
    recall_sum = 0.0
    mrr_sum = 0.0
    ndcg_sum = 0.0
    binary_sum = 0.0
    prop_sum = 0.0
    genre_count = 0

    for _, row in df_input.iterrows():
        original_id = str(row[ORIGINAL_ID_COL]).strip()
        user_input = str(row[USER_INPUT_COL]).strip()

        if not user_input or not original_id or user_input.lower() == 'nan':
            continue

        recommendations = get_recommendations(user_input)
        if not recommendations:
            continue

        input_genres = genre_map.get(original_id, [])

        total += 1
        precision_sum += precision_at_k(recommendations, original_id)
        recall_sum += recall_at_k(recommendations, original_id)
        mrr_sum += mrr_score(recommendations, original_id)
        ndcg_sum += ndcg_score(recommendations, original_id)

        if input_genres:
            bin_score = genre_binary_score(input_genres, recommendations[:TOP_K])
            prop_score = genre_proportional_score(input_genres, recommendations[:TOP_K])
            if bin_score is not None:
                binary_sum += bin_score
                prop_sum += prop_score
                genre_count += 1

    if total == 0:
        print("No valid inputs processed.")
        return

    metrics_summary = {
        'precision_at_k': precision_sum / total,
        'recall_at_k': recall_sum / total,
        'mrr': mrr_sum / total,
        'ndcg': ndcg_sum / total,
        'binary_genre_similarity': (binary_sum / genre_count) if genre_count > 0 else None,
        'proportional_genre_similarity': (prop_sum / genre_count) if genre_count > 0 else None,
        'total_evaluated_inputs': total,
        'total_inputs_with_genres': genre_count
    }

    # Save summary CSV
    df_summary = pd.DataFrame([metrics_summary])
    df_summary.to_csv(OUTPUT_CSV, index=False, float_format='%.6f', encoding='utf-8-sig')
    print(f"Summary metrics saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_all_inputs()
