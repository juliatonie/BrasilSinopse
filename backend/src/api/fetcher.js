// Carrega as variáveis de ambiente do arquivo .env
require('dotenv').config();

const axios = require('axios');       // Cliente HTTP para fazer requisições à API da TMDB
const fs = require('fs');             // Módulo do sistema de arquivos para salvar dados localmente
const path = require('path');         // Módulo de caminho para lidar com caminhos de arquivos

// Configuração base da API
const API_KEY = "9e442d7d9aaa8672cd8fc6d1e798a77f"//process.env.TMDB_API_KEY;
const BASE_URL = 'https://api.themoviedb.org/3';
const TOTAL_PAGES = 500
; 

// Define o caminho do arquivo de saída para salvar os dados finais dos filmes
const OUTPUT_PATH = path.join(__dirname, '../../data/movies.json');


function getSavedMovieIds() {
  if (!fs.existsSync(OUTPUT_PATH)) return new Set();

  const content = fs.readFileSync(OUTPUT_PATH, 'utf-8').trim();
  if (!content.startsWith('[') || !content.endsWith(']')) return new Set();

  const jsonText = `[${content.slice(1, -1)}]`; // remove [ e ] e reencaixa como JSON válido

  try {
    const movies = JSON.parse(jsonText ? jsonText : '[]');
    return new Set(movies.map(movie => movie.id));
  } catch (err) {
    console.error('Erro ao ler IDs já salvos:', err.message);
    return new Set();
  }
}

async function fetchPopularMovies(page) {
  const url = `${BASE_URL}/discover/movie`;
  const response = await axios.get(url, {
    params: {
      api_key: API_KEY,
      sort_by: "popularity.desc",
      with_origin_country: "BR",
      with_original_language: "pt",
      language: 'pt-BR',
      page: page
    }
  });
  return response.data.results;
}

async function fetchMovieDetails(movieId) {
  const url = `${BASE_URL}/movie/${movieId}`;
  const response = await axios.get(url, {
    params: {
      api_key: API_KEY,
      language: 'pt-BR',
      append_to_response: 'keywords'
    }
  });
  const data = response.data;

  return {
    id: data.id,
    title: data.title,
    overview: data.overview,
    genres: data.genres.map(g => g.name),
    keywords: (data.keywords?.keywords || []).map(k => k.name),
    popularity: data.popularity,
    rating: data.vote_average,
    original_language: data.original_language,
    poster: data.poster_path
  };
}

async function collectMovies() {
  const savedIds = getSavedMovieIds();
  let isFirst = savedIds.size === 0;

  if (isFirst) {
    fs.writeFileSync(OUTPUT_PATH, '[\n', 'utf-8');
  } else {
    // Remove o `]` do final para continuar o array
    const original = fs.readFileSync(OUTPUT_PATH, 'utf-8').trim();
    fs.writeFileSync(OUTPUT_PATH, original.slice(0, -1), 'utf-8');
  }

  for (let page = 1; page <= TOTAL_PAGES; page++) {
    console.log(`🔎 Buscando página ${page} de ${TOTAL_PAGES}...`);
    const movies = await fetchPopularMovies(page);

    for (const movie of movies) {
      if (savedIds.has(movie.id)) {
        console.log(`Filme ${movie.id} já foi salvo. Pulando...`);
        continue;
      }

      try {
        const details = await fetchMovieDetails(movie.id);

        const json = JSON.stringify(details, null, 2);
        if (!isFirst) fs.appendFileSync(OUTPUT_PATH, ',\n', 'utf-8');
        fs.appendFileSync(OUTPUT_PATH, json, 'utf-8');
        savedIds.add(details.id);
        isFirst = false;

        await new Promise(r => setTimeout(r, 250));
      } catch (err) {
        console.error(`Erro ao buscar o filme ${movie.id}:`, err.message);
      }
    }
  }

  // Finaliza o JSON
  fs.appendFileSync(OUTPUT_PATH, '\n]', 'utf-8');
  console.log(`Filmes salvos em ${OUTPUT_PATH}`);
}

collectMovies();