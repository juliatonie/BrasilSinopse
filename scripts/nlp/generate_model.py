import pandas as pd
import numpy as np
import json
import logging
import re
import unicodedata
from pathlib import Path
from sentence_transformers import SentenceTransformer
from hashlib import md5

# === CONFIGURAÇÕES ===
CSV_FILE = 'bref/data/movies.csv'
OUTPUT_FILE = './model.json'
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

WEIGHTS = {
    'title': 1.0,
    'overview': 3.0,
    'keywords': 1.5,
    'genres': 2.0
}

REQUIRED_COLS = [
    'id', 'title', 'overview', 'genres', 
    'keywords', 'popularity', 'rating', 'poster'
]

# === SETUP LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === FUNÇÕES DE PRÉ-PROCESSAMENTO ===
def clean_text(text):
    """Limpeza avançada preservando semântica"""
    if pd.isna(text) or not str(text).strip():
        return ''
    
    text = str(text).strip()
    text = unicodedata.normalize('NFKC', text)  # Normaliza unicode
    text = re.sub(r'[^\w\sáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ-]', '', text)  # Remove caracteres especiais
    return ' '.join(text.split())  # Normaliza espaços

def validate_dataframe(df):
    if df.empty:
        raise ValueError("DataFrame vazio")
    
    missing_cols = set(REQUIRED_COLS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Colunas faltantes: {missing_cols}")
    
    # Verifica campos essenciais
    if df['title'].isna().any():
        raise ValueError("Títulos faltantes encontrados")

def combine_text_fields(row):
    """Combinação inteligente com pesos dinâmicos"""
    combined = []
    total_weight = 0
    
    for field, weight in WEIGHTS.items():
        text = clean_text(row[field])
        if text:
            combined.append((text, weight))
            total_weight += weight
    
    if not combined:
        return ''
    
    # Ponderação proporcional
    return ' '.join(
        text for text, weight in combined 
        for _ in range(int(weight * len(combined)))
    )

# === GERADOR DE EMBEDDINGS ===
def generate_embeddings(texts, model):
    """Gera embeddings com verificações de qualidade"""
    logger.info("Gerando embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Verificação de qualidade
    norms = np.linalg.norm(embeddings, axis=1)
    if np.any(norms < 1e-6):
        bad_indices = np.where(norms < 1e-6)[0]
        logger.error(f"Embeddings inválidos nos índices: {bad_indices}")
        raise ValueError("Embeddings com norma zero detectados")
    
    return embeddings

# === PÓS-PROCESSAMENTO ===
def normalize_embeddings(embeddings):
    """Normalização L2 para similaridade de cosseno"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

def calculate_similarity_stats(embeddings):
    """Calcula estatísticas de similaridade para monitoramento"""
    sample_size = min(100, len(embeddings))
    sample = embeddings[np.random.choice(len(embeddings), sample_size, replace=False)]
    similarities = np.dot(sample, sample.T)
    np.fill_diagonal(similarities, 0)
    
    return {
        'min': float(np.min(similarities)),
        'max': float(np.max(similarities)),
        'median': float(np.median(similarities)),
        'mean': float(np.mean(similarities))
    }

# === UTILITÁRIOS ===
def save_model_with_checksum(data, output_path):
    """Salva o modelo com checksum para verificação"""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    checksum = md5(json_str.encode('utf-8')).hexdigest()
    
    data['metadata']['checksum'] = checksum
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Modelo salvo com checksum: {checksum}")

# === FLUXO PRINCIPAL ===
def generate_model():
    try:
        logger.info("Iniciando geração do modelo...")
        
        # 1. Carregar e validar dados
        logger.info(f"Carregando dados de {CSV_FILE}")
        df = pd.read_csv(CSV_FILE, low_memory=False)
        validate_dataframe(df)
        
        # Pré-processamento
        df = df[REQUIRED_COLS].copy()
        df.fillna('', inplace=True)
        
        # 2. Processamento de texto
        logger.info("Processando campos de texto...")
        df['combined'] = df.apply(combine_text_fields, axis=1)
        
        # Fallback para overviews faltantes
        if df['overview'].str.len().median() < 10:
            df['overview'] = df.apply(
                lambda x: x['overview'] if x['overview'].strip() else x['title'],
                axis=1
            )
        
        # 3. Carregar modelo de embeddings
        logger.info(f"Carregando modelo {MODEL_NAME}...")
        model = SentenceTransformer(MODEL_NAME)
        
        # 4. Gerar embeddings
        embeddings = generate_embeddings(df['combined'].tolist(), model)
        embeddings = normalize_embeddings(embeddings)
        
        # 5. Construir estrutura de saída
        logger.info("Montando modelo final...")
        model_data = {
            "movies": df[REQUIRED_COLS].to_dict(orient='records'),
            "embeddings": embeddings.tolist(),
            "metadata": {
                "model": MODEL_NAME,
                "generation_date": pd.Timestamp.now().isoformat(),
                "stats": {
                    "num_movies": len(df),
                    "avg_text_length": int(df['combined'].str.len().mean()),
                    "embedding_dim": embeddings.shape[1],
                    "similarity": calculate_similarity_stats(embeddings)
                }
            }
        }
        
        # 6. Salvar modelo
        save_model_with_checksum(model_data, OUTPUT_FILE)
        logger.info("Modelo gerado com sucesso!")
        return True
        
    except Exception as e:
        logger.critical(f"Falha na geração do modelo: {str(e)}", exc_info=True)
        return False

if __name__ == '__main__':
    success = generate_model()
    exit(0 if success else 1)