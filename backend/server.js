const express = require('express');
const cors = require('cors');
const recommend = require('./src/recommender'); 

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/recommender', async (req, res) => {
  const { query } = req.body;

  try {
    const results = await recommend(query, 5); 
    res.json(results);
   // console.log(results);
  } catch (error) {
    console.error('Erro ao recomendar:', error.message);
    res.status(500).json({ error: 'Erro ao processar recomendação.' });
  }
});

app.listen(3000, () => {
  console.log('🚀 Servidor rodando na porta 3000');
});
