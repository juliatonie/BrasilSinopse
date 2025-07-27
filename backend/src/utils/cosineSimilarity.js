module.exports = function cosineSimilarity(vecA, vecB) {
  if (vecA.length !== vecB.length) {
    throw new Error("Vetores devem ter o mesmo comprimento");
  }

  let dot = 0;
  let normA = 0;
  let normB = 0;

  // Usa acesso direto para performance, funciona com Array e Float32Array
  for (let i = 0; i < vecA.length; i++) {
    const a = vecA[i];
    const b = vecB[i];
    dot += a * b;
    normA += a * a;
    normB += b * b;
  }

  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  if (denom === 0) return 0;

  return dot / denom;
};
