import pandas as pd
import json
from sentence_transformers import SentenceTransformer

# === CONFIGURAÇÕES ===
CSV_FILE = 'bref/data/movies.csv'
OUTPUT_FILE = './model.json'
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
model = SentenceTransformer(MODEL_NAME)

# Pesos dos campos
weights = {
    'title': 1,
    'overview': 3,
    'keywords': 1,
    'genres': 2
}

# === FUNÇÃO DE LIMPEZA LEVE (sem remover acentos!) ===
def clean_text(text):
    if pd.isnull(text) or text == '':
        return ''
    return str(text).strip()

# === FUNÇÃO DE COMBINAÇÃO COM PESOS ===
def combine_text(row):
    def repeat_text(text, times):
        return (clean_text(text) + ' ') * times if text else ''
    
    return (
        repeat_text(row['title'], weights['title']) +
        repeat_text(row['overview'], weights['overview']) +
        repeat_text(row['keywords'], weights['keywords']) +
        repeat_text(row['genres'], weights['genres'])
    ).strip()

# === LEITURA DO CSV ===
print('Lendo CSV...')
df = pd.read_csv(CSV_FILE, low_memory=False)
print(f'Total de linhas no CSV: {len(df)}')

# Preenche campos vazios
df.fillna('', inplace=True)

# Colunas a manter na saída
required_cols = ['id', 'title', 'overview', 'genres', 'keywords', 'popularity', 'rating', 'poster']

# === COMBINANDO TEXTOS ===
print('Gerando textos combinados...')
df['combined'] = df.apply(combine_text, axis=1)

# === GERANDO EMBEDDINGS ===
print('Gerando embeddings...')
embeddings = model.encode(df['combined'].tolist(), show_progress_bar=True)

# === ESTRUTURA FINAL ===
print('Salvando modelo...')
model_data = {
    "movies": df[required_cols].to_dict(orient='records'),
    "embeddings": [vec.tolist() for vec in embeddings]
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(model_data, f, ensure_ascii=False, indent=2)

print(f'Salvo em {OUTPUT_FILE}')
