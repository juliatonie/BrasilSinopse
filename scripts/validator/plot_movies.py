import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

sns.set_theme(style="whitegrid")

# Carregar CSV
df = pd.read_csv("../../data/processed/movies.csv")

# Corrigir vírgulas para ponto
df['popularity'] = df['popularity'].astype(str).str.replace(',', '.').astype(float)
df['rating'] = df['rating'].astype(str).str.replace(',', '.').astype(float)
df['title'] = df['title'].str.replace(r'\$', 'S', regex=True)


# --- Função para definir número de bins automaticamente ---
def optimal_bins(data):
    q25, q75 = np.percentile(data, [25, 75])
    iqr = q75 - q25
    bin_width = 2 * iqr * len(data)**(-1/3)
    bins = int(np.ceil((data.max() - data.min()) / bin_width)) if bin_width > 0 else 10
    return max(5, bins)

# ===== 1. Popularidade =====

df['popularity_round'] = df['popularity'].round(1)

# Conta quantos filmes têm cada valor arredondado
pop_counts = df['popularity_round'].value_counts().reset_index()
pop_counts.columns = ['popularity', 'qtd']

# Ordena para manter a sequência correta
pop_counts = pop_counts.sort_values('popularity')

plt.figure(figsize=(8,6))
sns.scatterplot(x='popularity', y='qtd', data=pop_counts,
                s=35, color="#FF004C", alpha=0.6)

plt.title('Escala de Popularidade no TMDB')
plt.xlabel('Popularidade (TMDB)')
plt.ylabel('Quantidade de Filmes')
plt.grid(True, alpha=0.3)

plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(300))

plt.tight_layout()
#plt.show()

# ===== 2. Rating =====
bins_rating = optimal_bins(df['rating'])
mean_rate = df['rating'].mean()
median_rate = df['rating'].median()

plt.figure(figsize=(9,5))
sns.histplot(df['rating'], bins=bins_rating, kde=True, color="#FFEE00")
#plt.axvline(mean_rate, color='red', linestyle='--', label=f'Média: {mean_rate:.2f}')
#plt.axvline(median_rate, color='green', linestyle=':', label=f'Mediana: {median_rate:.2f}')
plt.title(f'Distribuição de Avaliações')
plt.xlabel('Nota (Rating)')
plt.ylabel('Quantidade de Filmes')
plt.legend()
plt.tight_layout()
#plt.show()

# ===== 3. Gêneros =====
df_genres = df['genres'].dropna().str.split(',').explode().str.strip()
genre_counts = df_genres.value_counts()
genre_percent = (genre_counts / len(df) * 100).round(1)

plt.figure(figsize=(10,6))
sns.barplot(x=genre_counts.values, y=genre_counts.index, palette='Pastel2')
for i, (count, perc) in enumerate(zip(genre_counts.values, genre_percent.values)):
    plt.text(count + 0.1, i, f"{count} ({perc}%)", va='center')
plt.title('Distribuição de Gêneros', fontsize=14)
plt.xlabel('Quantidade de Filmes')
plt.ylabel('Gênero')
plt.tight_layout()
#plt.show()

# ===== 3. Palavras-chave =====

df_keywords = (
    df['keywords']
    .dropna()
    .str.lower()               # transforma em minúsculas
    .str.split(',')
    .explode()
    .str.strip()               # remove espaços antes/depois
)
keywords_counts = df_keywords.value_counts()

# Filtra palavras-chave com mais de 100 ocorrências
keywords_counts_filtered = keywords_counts[keywords_counts > 30]

keywords_percent = (keywords_counts_filtered / len(df) * 100).round(1)

plt.figure(figsize=(10,6))
sns.barplot(x=keywords_counts_filtered.values, y=keywords_counts_filtered.index, palette='Pastel1')

for i, (count, perc) in enumerate(zip(keywords_counts_filtered.values, keywords_percent.values)):
    plt.text(count + 0.1, i, f"({perc}%)", va='center')
    #{count}

plt.title('Distribuição de Palavras-chave (mais de 30 ocorrências)', fontsize=14)
plt.xlabel('Quantidade de Filmes')
plt.ylabel('Palavras-chave')
plt.tight_layout()
plt.show()


