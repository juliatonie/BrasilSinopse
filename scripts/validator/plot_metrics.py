import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações gerais de estilo
sns.set(style='whitegrid')
plt.rcParams.update({'font.size': 14, 'axes.titlesize': 18, 'axes.labelsize': 16})

# Carrega dados
df = pd.read_csv('evaluation_results.csv')

# Cria bins de 0.1
bins = np.arange(0, 1.1, 0.1)
labels = [f'{round(b,1)}–{round(b+0.1,1)}' for b in bins[:-1]]
df['binary_genre_bin'] = pd.cut(df['binary_genre_similarity'], bins=bins, labels=labels, include_lowest=True)

# Agrupa
grouped = df.groupby('binary_genre_bin').agg(
    count_inputs=('binary_genre_similarity', 'size'),
    mean_precision=('precision_at_k', 'mean')
).reset_index()

# Plot
fig, ax1 = plt.subplots(figsize=(14,7))

# Barras laranja para quantidade de inputs
bars = ax1.bar(grouped['binary_genre_bin'], grouped['count_inputs'], color="#97e0dd", alpha=0.9, label='Quantidade de Inputs', edgecolor='black')

ax1.set_xlabel('Similaridade Binária de Gênero', fontsize=16)
ax1.set_ylabel('Quantidade de Inputs', fontsize=16, color="#a8a8a8")
ax1.tick_params(axis='y', labelcolor="#AAAAAA")
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Anotações nas barras
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f'{int(height)}', 
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 5), textcoords='offset points', 
                 ha='center', va='bottom', fontsize=12, fontweight='bold', color='#333333')

# Eixo secundário para Precision@K
ax2 = ax1.twinx()
sns.lineplot(x='binary_genre_bin', y='mean_precision', data=grouped, marker='o', color="#660202", linewidth=3, label='Precision@K', ax=ax2)

ax2.set_ylabel('Precision@K', fontsize=16, color="#000000")
ax2.tick_params(axis='y', labelcolor="#410000")
ax2.set_ylim(0, 1)
ax2.grid(False)

# Legenda combinada
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=14)

plt.title('Quantidade por Similaridade de Gênero e Precision@K ', fontsize=20, fontweight='bold')
plt.tight_layout()
plt.show()
