import { Router } from 'express';
import { HomeController } from './controllers/UserController';

const router = Router();

router.use('/home', HomeController);

export default router;