import { Router } from 'express';
import { DashboardController } from './controllers/DashboardController';

const router = Router();

router.use('/dashboard', DashboardController);

export default router;