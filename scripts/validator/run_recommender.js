const recommender = require('../../backend/src/recommender.js');

const input = process.argv[2];

recommender(input).then(result => {
  console.log(JSON.stringify(result));
}).catch(err => {
  console.error('Erro:', err.message);
  process.exit(1);
});
