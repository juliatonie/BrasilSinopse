from flask import Flask, request, jsonify
import unicodedata
import re
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# === Função de limpeza leve (sem remover acentos ou pontuação) ===
def clean_text(text):
    if not text or not isinstance(text, str):
        return ''
    # Substitui quebras de linha internas por espaço e depois remove espaços extras nas bordas
    text = str(text).strip()
    text = unicodedata.normalize('NFKC', text)  # Normaliza unicode
    text = re.sub(r'[^\w\sáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ-]', '', text)  # Remove caracteres especiais
    return ' '.join(text.split())  # Normaliza espaços


@app.route('/embed', methods=['POST'])
def embed():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'Texto ausente'}), 400

    cleaned_text = clean_text(text)
    vector = model.encode(cleaned_text).tolist()
    return jsonify({'vector': vector})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
