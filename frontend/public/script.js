document.getElementById('searchButton').addEventListener('click', async () => {
  const query = document.getElementById('description').value.trim();
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (query.length < 60) {
    resultsDiv.innerHTML = `
      <div style="
        background-color: #ffa44e;
        color: #000000ff;
        padding: 10px;
        border-radius: 12px;
        margin-top: 10px;
        font-family: Arial, sans-serif;
        text-align: center;
        box-shadow: 0 4px 8px hsla(27, 100%, 49%, 0.10);
      ">
        <strong>Atenção:</strong> Por favor, insira uma descrição com no mínimo 60 caracteres.
      </div>
    `;
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

    const LIMIAR_SIMILARIDADE = 0.4;


    const filmesFiltrados = Array.isArray(filmes)
      ? filmes.filter(f => f.similarity >= LIMIAR_SIMILARIDADE)
      : [];

    if (filmesFiltrados.length === 0) {
      resultsDiv.innerHTML = `
        <div style="
          background-color: #ffa44e;
          color: #000000ff;
          padding: 10px;
          border-radius: 12px;
          margin-top: 10px;
          font-family: Arial, sans-serif;
          text-align: center;
          box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        ">
          Nenhum filme relevante encontrado. Por favor, reformule sua descrição.
        </div>
      `;
      return;
    }

    

    function renderStars(rating) {
      const maxStars = 5;
      const filledStars = Math.round(rating / 2); // converte 0-10 para 0-5
      let stars = '';

      for (let i = 0; i < maxStars; i++) {
        stars += i < filledStars ? '⭐' : '☆';
      }

      return stars;
    }

    const grid = document.createElement('div');
    grid.className = 'result-grid';

    filmesFiltrados.forEach(filme => {
      const ratingNum = parseFloat(filme.rating) || 0;
      const item = document.createElement('div');
      item.className = 'result-item';
      item.innerHTML = `
        <img src="${filme.poster || 'placeholder.jpg'}" alt="Poster de ${filme.title}" class="result-poster" />
        <div class="result-title"><strong>${filme.title}</strong></div>
        <div class="result-overview">${filme.overview}</div>
        <div><strong>Gêneros:</strong> ${Array.isArray(filme.genres) ? filme.genres.join(', ') : 'Não informado'}</div>
        <div><strong>Popularidade:</strong> ${filme.popularity}</div>
        <div><strong>Avaliação TMDB:</strong> ${renderStars(ratingNum)} (${ratingNum.toFixed(1)}/10)</div>
      `;
      grid.appendChild(item);
    });
    //<div><strong>Similaridade:</strong> ${(filme.similarity * 100).toFixed(2)}%</div>
    resultsDiv.appendChild(grid);

  } catch (error) {
    resultsDiv.innerHTML = '<p>Erro ao conectar com o servidor.</p>';
    console.error(error);
  }
});

// 🔹 Efeito do header ao rolar
window.addEventListener('scroll', () => {
  const header = document.getElementById('header');
  if (window.scrollY > 30) {
    header.classList.add('scrolled');
  } else {
    header.classList.remove('scrolled');
  }
});

// 🔹 Expansão da descrição
document.addEventListener('DOMContentLoaded', () => {
  const results = document.getElementById('results');

  results.addEventListener('click', (event) => {
    if (event.target.classList.contains('result-overview')) {
      event.target.classList.toggle('expanded');
    }
  });
});
