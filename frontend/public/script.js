document.getElementById('searchButton').addEventListener('click', async () => {
  const query = document.getElementById('description').value.trim();
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (query.length < 60) {
    resultsDiv.innerHTML = '<p>Por favor, digite uma descrição mais completa.</p>';
    return;
  }

  try {
    const response = await fetch('http://localhost:3000/api/recommender', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      resultsDiv.innerHTML = '<p>Erro na busca. Tente novamente.</p>';
      return;
    }

    const filmes = await response.json();

    if (!Array.isArray(filmes) || filmes.length === 0) {
      resultsDiv.innerHTML = '<p>Nenhum filme relevante encontrado.</p>';
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'result-grid';

    filmes.forEach(filme => {
      const item = document.createElement('div');
      item.className = 'result-item';
      item.innerHTML = `
        <img src="${filme.poster || 'placeholder.jpg'}" alt="Poster de ${filme.title}" class="result-poster" />
        <div class="result-title"><strong>${filme.title}</strong></div>
        <div class="result-overview">${filme.overview}</div>
        <div><strong>Gêneros:</strong> ${Array.isArray(filme.genres) ? filme.genres.join(', ') : 'Não informado'}</div>
        
      `;
      //<div><strong>Popularidade:</strong> ${filme.popularity || 'Não informado'}</div>
      grid.appendChild(item);
    });

    resultsDiv.appendChild(grid);

  } catch (error) {
    resultsDiv.innerHTML = '<p>Erro ao conectar com o servidor.</p>';
    console.error(error);
  }
});

 window.addEventListener('scroll', () => {
      const header = document.getElementById('header');
      if (window.scrollY > 30) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    });

document.addEventListener('DOMContentLoaded', () => {
  const results = document.getElementById('results');

  results.addEventListener('click', (event) => {
    // Se o alvo do clique tem a classe .result-overview
    if (event.target.classList.contains('result-overview')) {
      event.target.classList.toggle('expanded');
    }
  });
});