import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Estilo do gráfico
sns.set(style='whitegrid')
plt.rcParams.update({'font.size': 14, 'axes.titlesize': 18, 'axes.labelsize': 16})

# Carrega os dados
df_hybrid = pd.read_csv('../../data/results/hybrid_evaluation_results.csv')
df_minilm = pd.read_csv('../../data/results/miniLM_evaluation_results.csv')

# Define bins
bins = np.arange(0, 1.1, 0.1)
labels = [f'{round(b,1)}–{round(b+0.1,1)}' for b in bins[:-1]]

# Cria colunas de bin
df_hybrid['binary_genre_bin'] = pd.cut(df_hybrid['binary_genre_similarity'], bins=bins, labels=labels, include_lowest=True)
df_minilm['binary_genre_bin'] = pd.cut(df_minilm['binary_genre_similarity'], bins=bins, labels=labels, include_lowest=True)

# Agrupa para cada sistema
grouped_hybrid = df_hybrid.groupby('binary_genre_bin').agg(
    count_inputs=('binary_genre_similarity', 'size'),
    mean_precision=('precision_at_k', 'mean')
).reset_index()

grouped_minilm = df_minilm.groupby('binary_genre_bin').agg(
    count_inputs=('binary_genre_similarity', 'size'),
    mean_precision=('precision_at_k', 'mean')
).reset_index()

# Cria figura
fig, ax1 = plt.subplots(figsize=(14,7))

# Posição das barras lado a lado
x = np.arange(len(labels))
width = 0.4

# Barras para Hybrid (azul)
bars1 = ax1.bar(x - width/2, grouped_hybrid['count_inputs'], width, 
                color="#1f77b4", alpha=0.8, label='Qtd Entradas (Hybrid)', edgecolor='black')

# Barras para MiniLM (vermelho)
bars2 = ax1.bar(x + width/2, grouped_minilm['count_inputs'], width, 
                color="#d62728", alpha=0.8, label='Qtd Entradas (MiniLM)', edgecolor='black')

ax1.set_xlabel('Similaridade Binária de Gênero', fontsize=16)
ax1.set_ylabel('Quantidade de Entradas', fontsize=16, color="#444444")
ax1.tick_params(axis='y', labelcolor="#444444")
ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=45)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Adiciona anotações de valor nas barras
for bar in bars1 + bars2:
    height = bar.get_height()
    ax1.annotate(f'{int(height)}', 
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords='offset points',
                 ha='center', va='bottom', fontsize=10, color='#222222')

# Eixo secundário para Precision@K
ax2 = ax1.twinx()

# Linha do sistema híbrido
sns.lineplot(x=x, y=grouped_hybrid['mean_precision'], marker='o',
             color="#003366", linewidth=3, label='Precision@K (Hybrid)', ax=ax2)

# Linha do MiniLM
sns.lineplot(x=x, y=grouped_minilm['mean_precision'], marker='s',
             color="#8B0000", linewidth=3, label='Precision@K (MiniLM)', ax=ax2)

ax2.set_ylabel('Precision@K', fontsize=16, color="#000000")
ax2.tick_params(axis='y', labelcolor="#000000")
ax2.set_ylim(0, 1)
ax2.grid(False)

# Combina legendas dos dois eixos
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

plt.title('Comparação: Quantidade e Precision@K por Similaridade de Gênero', fontsize=20, fontweight='bold')
plt.tight_layout()
plt.savefig('comparacao_hybrid_minilm.png', dpi=300)
plt.show()
