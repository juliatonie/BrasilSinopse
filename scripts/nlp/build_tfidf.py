import pandas as pd
import json
from    .feature_extraction.text import TfidfVectorizer
import stopwordsiso as stopwords

WEIGHTS = {
    'title': 1.0,
    'overview': 3.0,
    'keywords': 1.5,
    'genres': 2.0
}

CSV_PATH = 'data/processed/movies.csv'

df = pd.read_csv(CSV_PATH)
for col in ['title', 'overview', 'keywords', 'genres']:
    if col not in df.columns:
        df[col] = ''
    else:
        df[col] = df[col].fillna('')

def weighted_text(row):
    parts = []
    if row['title']:
        parts.append(row['title'] + ' ')
    if row['overview']:
        parts.append(row['overview'] + ' ')
    if row['keywords']:
        parts.append(row['keywords'] + ' ')
    if row['genres']:
        parts.append(row['genres'] + ' ')
    return ''.join(parts).lower()

corpus = df.apply(weighted_text, axis=1).tolist()

ptbr_stopwords = list(stopwords.stopwords("pt"))

vectorizer = TfidfVectorizer(max_features=3000, stop_words=ptbr_stopwords)
X = vectorizer.fit_transform(corpus)

vocab = vectorizer.get_feature_names_out()
idf = vectorizer.idf_  # array de idf para cada termo

tfidf_vectors = X.toarray()

output = {
    'vocabArray': vocab.tolist(),
    'idf': idf.tolist(),
    'tfidfVectors': tfidf_vectors.tolist()
}

with open('data/model/tfidf_vectors.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print('Vetores TF-IDF com IDF salvos em data/model/tfidf_vectors.json')
