import os
import subprocess
import json
import pandas as pd

# === CONFIGURAÇÕES ===
RECOMMENDER = './run_recommender.js'
CSV_INPUT = './inputs.csv'        # Arquivo com colunas: input_user, id
COLUNA_INPUT = 'input_user'
TOP_K = 5

def buscar_similares_com_node(user_input):
    """Executa o script Node.js que retorna os filmes mais similares a partir do input do usuário."""
    try:
        result = subprocess.run(
            ['node', RECOMMENDER, user_input],
            capture_output=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout
        if output is None:
            print("Saída do subprocess está vazia.")
            return []
        output = output.strip()
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar run_recommender.js: {e.stderr}")
        return []
    except json.JSONDecodeError:
        print("rro ao decodificar JSON retornado.")
        print("Saída recebida:", output)
        return []

def calcular_hit_rate_por_id():
    """Calcula a proporção de vezes em que o filme original (por ID) aparece entre os top-K recomendados."""
    df_input = pd.read_csv(CSV_INPUT, sep=",", quotechar='"', encoding="utf-8")

    if COLUNA_INPUT not in df_input.columns or 'id' not in df_input.columns:
        print(f"Colunas '{COLUNA_INPUT}' e/ou 'id' não encontradas no CSV de entrada.")
        return

    total = 0
    acertos = 0

    for idx, row in df_input.iterrows():
        original_id = str(row['id']).strip()
        original_title = str(row['title']).strip()
        user_input = str(row[COLUNA_INPUT]).replace('\n', ' ').replace('\r', ' ').strip()


        if not user_input or user_input.lower() == 'nan':
            continue

        print("=" * 80)
        print(f"Filme original: {original_title} ID: {original_id}")
        print(f" Input do usuário: {user_input}\n")


        recomendados = buscar_similares_com_node(user_input)

        if not recomendados:
            print("Nenhum resultado retornado.\n")
            continue

        recommended_ids = [str(filme['id']).strip() for filme in recomendados[:TOP_K]]

        print(f"Top-{TOP_K} recomendados:")
        for i, rec in enumerate(recomendados[:TOP_K], start=1):
            titulo = rec.get('title', '(sem título)')
            rec_id = rec.get('id', '?')
            print(f"[{i}] ID: {rec_id} | Título: {titulo}")

        total += 1
        if original_id in recommended_ids:
            print("\nResultado: ACERTO (ID original entre os top recomendados)\n")
            acertos += 1
        else:
            print("\nResultado: ERRO! ID original não está entre os top recomendados.\n")

    if total > 0:
        acc = (acertos / total) * 100
        print(f"\nAcurácia Top-{TOP_K} por ID: {acc:.2f}% ({acertos}/{total})")
    else:
        print("Nenhum dado válido para avaliar.")

if __name__ == "__main__":
    calcular_hit_rate_por_id()
