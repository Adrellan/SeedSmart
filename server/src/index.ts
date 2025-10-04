import express from 'express';
import bodyParser from 'body-parser';
import http from 'http';

import cors from 'cors';
import apiRouter from './api.router';
import { db } from './config/db.config';

const app = express();

app.use((req, res, next) => {
  res.setHeader("Content-Security-Policy", "frame-ancestors http://localhost:3000");
  res.removeHeader("X-Frame-Options");
  next();
});

app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

const port = process.env.PORT || 3000;

// --- Adatbázis inicializálása --- //
db.init().catch(e => {
  console.error(`Nem sikerült csatlakozni az adatbázishoz: ${e}`);
});

// JSON formátumú kérések feldolgozása
app.use(express.json());

// CORS szabályok
app.use(cors({
  origin: '*',
  credentials: true,
}));

// Fő router az /api előtaghoz
app.use('/api', apiRouter);

app.listen(port, () => {
  console.log(`A szerver elindult a ${port} porton`);
});