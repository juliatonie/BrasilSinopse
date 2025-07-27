const fs = require('fs');
const path = require('path');
const axios = require('axios');
const cosineSimilarity = require('./utils/cosineSimilarity.js');
const { getTfidfSimilarities } = require('./utils/tfidf.js');

const DEBUG = false;
const TMDB_BASE_URL = 'https://image.tmdb.org/t/p/w154';
const EMBEDDING_API_URL = 'http://127.0.0.1:5000/embed';
const EMBEDDING_TIMEOUT_MS = 5000;
const MODEL_PATH = path.join(__dirname, '../../data/model/model.json');

const WEIGHT_MINILM = 0.7;
const WEIGHT_TFIDF = 0.3;

let model;
try {
  model = JSON.parse(fs.readFileSync(MODEL_PATH, 'utf-8'));
} catch (err) {
  console.error('Erro ao carregar o modelo:', err.message);
  throw err;
}

const { movies } = model;
// Converter embeddings para Float32Array para performance
const embeddings = model.embeddings.map(e => Float32Array.from(e));

function validateQuery(query) {
  if (!query || typeof query !== 'string' || query.trim().length < 2) {
    throw new Error('Consulta inválida: deve ser uma string válida com pelo menos 2 caracteres');
  }
}

function validateEmbedding(vector) {
  if (!Array.isArray(vector) && !(vector instanceof Float32Array)) {
    throw new Error(`Formato de embedding inválido. Tipo: ${typeof vector}`);
  }
  if (vector.length === 0) {
    throw new Error('Embedding vazio');
  }
}

async function getEmbedding(query) {
  const response = await axios.post(
    EMBEDDING_API_URL,
    { text: query },
    {
      timeout: EMBEDDING_TIMEOUT_MS,
      headers: { 'Content-Type': 'application/json' }
    }
  );

  if (!response?.data?.vector) {
    throw new Error('Resposta do serviço de embedding está vazia');
  }

  // Converte vetor recebido para Float32Array para melhor performance
  return Float32Array.from(response.data.vector);
}

function processResults(queryVec, queryText, queryKeywords = '', queryGenres = '', n) {
  const results = [];
  const tfidfScores = getTfidfSimilarities(queryText, queryKeywords, queryGenres);

  for (let i = 0; i < embeddings.length; i++) {
    const simMiniLM = cosineSimilarity(queryVec, embeddings[i]);
    const simTfidf = tfidfScores[i];

    const similarity = (WEIGHT_MINILM * simMiniLM) + (WEIGHT_TFIDF * simTfidf);
    results.push({ index: i, similarity });
  }

  return results
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, n);
}

function formatMovie(movie, similarity) {
  const splitAndTrim = (str) =>
    typeof str === 'string'
      ? str.split(',').map(s => s.trim()).filter(Boolean)
      : [];

  return {
    id: movie.id,
    title: movie.title,
    overview: movie.overview || 'Sem descrição.',
    genres: splitAndTrim(movie.genres),
    keywords: splitAndTrim(movie.keywords),
    similarity: Number(similarity.toFixed(4)),
    poster: movie.poster ? `${TMDB_BASE_URL}${movie.poster}` : null,
    popularity: movie.popularity,
    rating: movie.rating,
  };
}

async function recommender(query, n = 5, keywords = '', genres = '') {
  try {
    validateQuery(query);

    const queryVec = await getEmbedding(query);
    validateEmbedding(queryVec);

    const topResults = processResults(queryVec, query, keywords, genres, n);

    return topResults.map(result =>
      formatMovie(movies[result.index], result.similarity)
    );
  } catch (err) {
    console.error('\nErro no sistema de recomendação:');
    console.error(`Name: ${err.name}`);
    console.error(`Message: ${err.message}`);

    if (err.code === 'ECONNREFUSED') {
      console.error('Verifique se o serviço de embedding está rodando em', EMBEDDING_API_URL);
    }

    if (DEBUG) console.error('\n🔍 Stack Trace:', err.stack);

    return [];
  }
}

module.exports = recommender;
