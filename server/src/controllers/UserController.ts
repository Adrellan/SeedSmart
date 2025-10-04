import { Router, Request, Response } from 'express';
import { logger } from '../config/logger.config';
import { Op } from 'sequelize';

const router = Router();

router.get('/countries', async (req: Request, res: Response) => {
    logger.info('GET countries endpoint called');

    try {

        return res.status(200).json([]);
    } catch (error) {
        logger.error('Error fetching countries:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.get('/regions', async (req: Request, res: Response) => {
    logger.info('GET regions endpoint called');

    try {

        return res.status(200).json([]);
    } catch (error) {
        logger.error('Error fetching regions:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
});

export const HomeController = router;