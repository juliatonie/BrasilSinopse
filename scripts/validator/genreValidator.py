import os
import subprocess
import json
import pandas as pd

# === CONFIGURAÇÕES ===
CSV_INPUT = '../../data/results/inputs.csv'        # arquivo com input_user e id_original (troque title por id)
GENRES_FILE = '../../data/processed/movies.csv'      # arquivo auxiliar com id, title e genres
COLUNA_INPUT = 'input_user'
COLUNA_ID_ORIGINAL = 'id'  # coluna com ID do filme original no CSV de input
NOME_FILME = 'title'
RECOMMENDER = './run_recommender.js'
TOP_K = 5

def carregar_generos_dos_filmes():
    df = pd.read_csv(GENRES_FILE)
    # Garantir tipos string e limpeza básica
    df['id'] = df['id'].astype(str).str.strip()
    df['genres'] = df['genres'].astype(str).apply(lambda x: [g.strip().lower() for g in x.split(',')] if x.strip() else [])
    # Criar dicionário id -> lista de gêneros (não inclui gêneros vazios)
    return dict((film_id, genres) for film_id, genres in zip(df['id'], df['genres']) if genres)

def buscar_similares_com_node(input_usuario):
    try:
        result = subprocess.run(
            ['node', RECOMMENDER, input_usuario],
            capture_output=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout
        if not output:
            print("Atenção: saída do subprocess está vazia (stdout=None).")
            return []
        output = output.strip()
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar run_recommender.js: {e.stderr}")
        return []
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON retornado.")
        print("Saída recebida:", output)
        return []

def limpar_generos(valor):
    if isinstance(valor, list):
        # Remove strings vazias e formata
        return [g.strip().lower() for g in valor if g.strip()]
    elif isinstance(valor, str):
        # Garante que não é vazio antes de dividir
        return [g.strip().lower() for g in valor.split(',') if g.strip()]
    return []

def avaliar_binaria_por_generos(generos_entrada, recomendacoes):
    """Métrica 1: 1 se há pelo menos um gênero em comum, 0 caso contrário (por filme). Ignora recomendados sem gênero."""
    generos_entrada_set = set(generos_entrada)
    if not generos_entrada_set:
        return 0.0

    acertos = 0
    count_validos = 0
    for filme in recomendacoes:
        generos_recomendado = set(limpar_generos(filme.get('genres', [])))
        if not generos_recomendado:
            continue  # ignora filmes sem gênero
        count_validos += 1
        if generos_entrada_set & generos_recomendado:
            acertos += 1

    if count_validos == 0:
        return 0.0
    return acertos / count_validos

def avaliar_proporcional_por_generos(generos_entrada, recomendacoes):
    """Métrica 2: proporção de gêneros do original presentes em cada recomendado (média). Ignora recomendados sem gênero."""
    generos_entrada_set = set(generos_entrada)
    if not generos_entrada_set:
        return 0.0

    proporcoes = []
    for filme in recomendacoes:
        generos_recomendado = set(limpar_generos(filme.get('genres', [])))
        if not generos_recomendado:
            continue
        intersecao = generos_entrada_set.intersection(generos_recomendado)
        proporcao = len(intersecao) / len(generos_entrada_set)
        proporcoes.append(proporcao)

    if not proporcoes:
        return 0.0
    return sum(proporcoes) / len(proporcoes)

def processar_todos_os_inputs():
    df_input = pd.read_csv(CSV_INPUT, sep=",", quotechar='"', encoding="utf-8")
    mapa_generos = carregar_generos_dos_filmes()

    # Validar colunas
    if COLUNA_INPUT not in df_input.columns or COLUNA_ID_ORIGINAL not in df_input.columns:
        print(f"Colunas '{COLUNA_INPUT}' e/ou '{COLUNA_ID_ORIGINAL}' não encontradas no CSV de entrada.")
        return

    total = 0
    acertos = 0
    soma_binaria = 0.0
    soma_proporcional = 0.0
    total_genero = 0

    for idx, row in df_input.iterrows():
        id_original = str(row[COLUNA_ID_ORIGINAL]).strip()
        input_usuario = str(row[COLUNA_INPUT]).strip()
        nome_filme = str(row[NOME_FILME]).strip()

        if not input_usuario or input_usuario.lower() == 'nan' or not id_original:
            continue

        print("="*80)
        print(f"filme original: {nome_filme}{id_original}")
        print(f"Input do usuário: {input_usuario}\n")

        resultados = buscar_similares_com_node(input_usuario)
        if not resultados:
            print("Nenhum resultado encontrado.\n")
            continue

        generos_original = mapa_generos.get(id_original, [])
        if generos_original:
            generos_str = ', '.join(generos_original)
            print(f"Gêneros do filme original (arquivo auxiliar): {generos_str}\n")
        else:
            print("Filme original sem gêneros definidos no arquivo auxiliar. Ignorando avaliação de gêneros.\n")


        # IDs recomendados para checagem de acerto por ID
        ids_recomendados = [str(filme.get('id', '')).strip() for filme in resultados[:TOP_K]]

        for i, filme in enumerate(resultados[:TOP_K], start=1):
            print(f"[{i}] {filme.get('title', 'Título desconhecido')}")
            print(f"   Descrição: {filme.get('overview', 'Sem descrição.')}")
            print(f"   Gêneros: {filme.get('genres', [])}")
            print(f"   ID: {filme.get('id', 'N/A')}\n")

        total += 1
        if id_original in ids_recomendados:
            print("Resultado: ACERTO (por ID)\n")
            acertos += 1
        else:
            print("Resultado: ERRO! Filme original não está entre os top recomendados.\n")

        if generos_original:
            score_binaria = avaliar_binaria_por_generos(generos_original, resultados[:TOP_K])
            soma_binaria += score_binaria

            score_proporcional = avaliar_proporcional_por_generos(generos_original, resultados[:TOP_K])
            soma_proporcional += score_proporcional
            total_genero += 1

            print(f"→ Similaridade binária por gênero: {score_binaria * 100:.1f}%")
            print(f"→ Similaridade proporcional por gênero: {score_proporcional * 100:.1f}%\n")

    # Resultados finais
    if total > 0:
        print(f"\n📊 Acurácia Top-{TOP_K} por ID: {(acertos / total) * 100:.2f}% ({acertos}/{total})")
    if total_genero > 0:
        print(f"📊 Similaridade binária por gêneros (média): {(soma_binaria / total_genero) * 100:.2f}%")
        print(f"📊 Similaridade proporcional por gêneros (média): {(soma_proporcional / total_genero) * 100:.2f}%")

if __name__ == "__main__":
    processar_todos_os_inputs()
