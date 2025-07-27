const fs = require('fs');
const path = require('path');
const cosineSimilarity = require('./cosineSimilarity.js');

const TFIDF_VECTORS_PATH = path.join(__dirname, '../../../data/model/tfidf_vectors.json');
const tfidfData = JSON.parse(fs.readFileSync(TFIDF_VECTORS_PATH, 'utf-8'));

const { vocabArray, idf, tfidfVectors } = tfidfData;

function tokenize(text) {
  return text
    .toLowerCase()
    .match(/\b\w+\b/g) || [];
}

// Calcula TF vetor da query
function computeTF(tokens) {
  const tfMap = new Map();
  tokens.forEach(t => tfMap.set(t, (tfMap.get(t) || 0) + 1));
  return tfMap;
}

// Calcula TF-IDF da query usando o IDF do corpus
function vectorizeQuery(query) {
  const tokens = tokenize(query);
  const tfMap = computeTF(tokens);
  const vec = vocabArray.map((term, i) => {
    const tf = tfMap.get(term) || 0;
    return tf * idf[i];
  });
  return vec;
}

function getTfidfSimilarities(query) {
  const queryVec = vectorizeQuery(query);

  // Normalizar queryVec (opcional, recomendado)
  const mag = Math.sqrt(queryVec.reduce((acc, v) => acc + v * v, 0));
  const normalizedQueryVec = mag > 0 ? queryVec.map(v => v / mag) : queryVec;

  // Normalizar documentos? Supondo que tfidfVectors já estão normalizados (se não, normalizar aqui também)

  return tfidfVectors.map(docVec => cosineSimilarity(normalizedQueryVec, docVec));
}

module.exports = {
  getTfidfSimilarities
};
