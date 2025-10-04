import express from 'express';
import bodyParser from 'body-parser';
import http from 'http';

import cors from 'cors';
import compression from 'compression';
import apiRouter from './api.router';
import snakeCaseMiddleware from './middlewares/snakeCaseMiddleware';
import { Server } from 'socket.io';
import { db } from './config/db.config';
import { logger } from './config/logger.config';
import redis from './config/redis.config';
import { io as Client } from 'socket.io-client';

const app = express();

app.use((req, res, next) => {
  res.setHeader("Content-Security-Policy", "frame-ancestors http://localhost:3000");
  res.removeHeader("X-Frame-Options");
  next();
});

app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST'],
    credentials: true,
  },
  pingTimeout: 60000, 
  pingInterval: 25000, 
});
const port = process.env.PORT || 3000;
const directoryPath = process.env.DIRECTORY_PATH || '';

// --- Adatbázis inicializálása --- //
db.init().catch(e => {
  console.error(`Nem sikerült csatlakozni az adatbázishoz: ${e}`);
});

// --- Köztes rétegek (middlewares) --- //

// JSON formátumú kérések feldolgozása
app.use(express.json());

// CORS szabályok
app.use(cors({
  origin: '*',
  credentials: true,
}));

// Válaszok tömörítése az optimális teljesítmény érdekében
app.use(compression());

// Snake case köztes réteg
// app.use(snakeCaseMiddleware);

// Teljesítmény köztes réteg
// app.use(performanceMiddleware);

// Statikus fájlok kiszolgálása képekhez
app.use('/images', express.static(directoryPath, {
  setHeaders: (res, path) => {
    res.setHeader('Content-Encoding', 'gzip');
  }
}));

// Fő router az /api előtaghoz
app.use('/api', apiRouter);

// Folyamat állapotának lekérdezése
app.get('/api/process-status', async (req, res) => {
  try {
    const status = await redis.get('processStatus');
    res.json({ status: status || 'idle' });
  } catch (error) {
    console.error('Error fetching process status:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Folyamat állapotának beállítása
const setProcessStatus = async (status: string) => {
  try {
    await redis.set('processStatus', status);
  } catch (error) {
    logger.error('Error setting process status in Redis:', error);
  }
};

// Socket.IO kapcsolat kezelése
io.on('connection', (socket) => {
  logger.info(`Egy felhasználó csatlakozott: ${socket.id}`);
  socket.on('disconnect', () => {
    logger.info(`Egy felhasználó lecsatlakozott: ${socket.id}`);
  });
});

// Kapcsolódás a távoli szerverhez
// const remoteSocket = Client('http://10.50.20.8:3000', {
//   reconnection: true,
//   reconnectionAttempts: Infinity,
//   reconnectionDelay: 1000,
//   reconnectionDelayMax: 5000,
//   timeout: 60000,
// });

// remoteSocket.on('connect', () => {
//   console.log('Kapcsolódás a távoli szerverhez sikeres', remoteSocket.id);
// });

// remoteSocket.on('status', async (data) => {
//   await setProcessStatus(data.status); 
//   io.emit('processingStatus', data);
// });

// remoteSocket.on('connect_error', (error) => {
//   console.error('Kapcsolódási hiba a távoli szerverhez:', error);
// });

// remoteSocket.on('error', async (error) => {
//   await setProcessStatus('idle');
//   console.error('Hiba történt a feldolgozás során:', error);
// });

// remoteSocket.on('disconnect', (reason) => {
//   console.log('Kapcsolat megszakadt a távoli szerverrel:', reason);
// });

setProcessStatus('idle').then(() => {
  server.listen(port, () => {
    logger.info(`A szerver elindult a ${port} porton`);
  });
});
export { io, setProcessStatus };