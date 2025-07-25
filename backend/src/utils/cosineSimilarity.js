module.exports = function cosineSimilarity(vecA, vecB, { normalized = true } = {}) {
  if (vecA.length !== vecB.length) {
    throw new Error("Vetores devem ter o mesmo comprimento");
  }

  const EPSILON = 1e-10;
  let dot = 0;
  
  for (let i = 0; i < vecA.length; i++) {
    dot += vecA[i] * vecB[i];
  }

  if (normalized) return dot;

  const magA = Math.hypot(...vecA);
  const magB = Math.hypot(...vecB);
  const magnitude = magA * magB;

  return magnitude < EPSILON ? 0 : dot / magnitude;
};