import os
import subprocess
import json
import pandas as pd

# === CONFIGURAÇÕES ===
CSV_INPUT = './inputs.csv'        # arquivo com input_user e title
GENRES_FILE = './movies.csv'      # arquivo auxiliar com title e genres
COLUNA_INPUT = 'input_user'
TOP_K = 5

def carregar_generos_dos_filmes():
    df = pd.read_csv(GENRES_FILE)
    df['title'] = df['title'].astype(str).str.strip()
    df['genres'] = df['genres'].astype(str).apply(lambda x: [g.strip().lower() for g in x.split(',')])
    return dict(zip(df['title'], df['genres']))

def buscar_similares_com_node(input_usuario):
    try:
        result = subprocess.run(
            ['node', './run_recommender.js', input_usuario],
            capture_output=True,
            encoding='utf-8',
            check=True
        )
        output = result.stdout
        if output is None:
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
        return [g.strip().lower() for g in valor]
    elif isinstance(valor, str):
        return [g.strip().lower() for g in valor.split(',')]
    return []

def avaliar_binaria_por_generos(generos_entrada, recomendacoes):
    """Métrica 1: 1 se há pelo menos um gênero em comum, 0 caso contrário (por filme)."""
    generos_entrada_set = set(limpar_generos(generos_entrada))
    if not generos_entrada_set:
        return 0.0

    acertos = 0
    for filme in recomendacoes:
        generos_recomendado = set(limpar_generos(filme.get('genres', [])))
        if generos_entrada_set & generos_recomendado:
            acertos += 1

    return acertos / len(recomendacoes) if recomendacoes else 0.0

def avaliar_proporcional_por_generos(generos_entrada, recomendacoes):
    """Métrica 2: proporção de gêneros do original presentes em cada recomendado (média)."""
    generos_entrada_set = set(limpar_generos(generos_entrada))
    if not generos_entrada_set:
        return 0.0

    proporcoes = []
    for filme in recomendacoes:
        generos_recomendado = set(limpar_generos(filme.get('genres', [])))
        intersecao = generos_entrada_set.intersection(generos_recomendado)
        proporcao = len(intersecao) / len(generos_entrada_set)
        proporcoes.append(proporcao)

    return sum(proporcoes) / len(proporcoes) if proporcoes else 0.0

def processar_todos_os_inputs():
    df_input = pd.read_csv(CSV_INPUT, sep=",", quotechar='"', encoding="utf-8")
    mapa_generos = carregar_generos_dos_filmes()

    if COLUNA_INPUT not in df_input.columns or 'title' not in df_input.columns:
        print(f"Colunas '{COLUNA_INPUT}' e/ou 'title' não encontradas no CSV de entrada.")
        return

    total = 0
    acertos = 0
    soma_binaria = 0.0
    soma_proporcional = 0.0
    total_genero = 0

    for idx, row in df_input.iterrows():
        titulo_original = str(row['title']).strip()
        input_usuario = str(row[COLUNA_INPUT]).strip()

        if not input_usuario or input_usuario.lower() == 'nan':
            continue

        print("="*80)
        print(f"Filme original: {titulo_original}")
        print(f"Input do usuário: {input_usuario}\n")

        resultados = buscar_similares_com_node(input_usuario)

        if not resultados:
            print("Nenhum resultado encontrado.\n")
            continue

        generos_original = mapa_generos.get(titulo_original, [])
        print(f"Gêneros do filme original (arquivo auxiliar): {generos_original}\n")

        titulos_recomendados = [filme['title'] for filme in resultados[:TOP_K]]

        for i, filme in enumerate(resultados[:TOP_K], start=1):
            print(f"[{i}] {filme['title']}")
            print(f"   Descrição: {filme.get('overview', 'Sem descrição.')}")
            print(f"   Gêneros: {filme.get('genres', [])}\n")

        total += 1
        if titulo_original in titulos_recomendados:
            print("Resultado: ACERTO (por título)\n")
            acertos += 1
        else:
            print("Resultado: ERRO! Filme original não está entre os top recomendados.\n")

        # Métrica binária
        score_binaria = avaliar_binaria_por_generos(generos_original, resultados[:TOP_K])
        soma_binaria += score_binaria

        # Métrica proporcional
        score_proporcional = avaliar_proporcional_por_generos(generos_original, resultados[:TOP_K])
        soma_proporcional += score_proporcional

        total_genero += 1

        print(f"→ Similaridade binária por gênero: {score_binaria * 100:.1f}%")
        print(f"→ Similaridade proporcional por gênero: {score_proporcional * 100:.1f}%\n")

    # Resultados finais
    if total > 0:
        print(f"\n📊 Acurácia Top-{TOP_K} por título: {(acertos / total) * 100:.2f}% ({acertos}/{total})")
    if total_genero > 0:
        print(f"📊 Similaridade binária por gêneros (média): {(soma_binaria / total_genero) * 100:.2f}%")
        print(f"📊 Similaridade proporcional por gêneros (média): {(soma_proporcional / total_genero) * 100:.2f}%")

if __name__ == "__main__":
    processar_todos_os_inputs()
