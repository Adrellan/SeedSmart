import { Router, Request, Response } from 'express';
import { logger } from '../config/logger.config';
import { Countires } from '../models/Countires';
import { Regions } from '../models/Regions';

const router = Router();

router.get('/countries', async (req: Request, res: Response) => {
    logger.info('GET countries endpoint called');

    try {
        const countries = await Countires.findAll();

        return res.status(200).json(countries);
    } catch (error) {
        logger.error('Error fetching countries:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
});

router.get('/regions', async (req: Request, res: Response) => {
    logger.info('GET regions endpoint called');

    const { cntr_code } = req.query;
    if (typeof cntr_code !== 'string' || !cntr_code.trim()) {
        logger.warn('Missing cntr_code query parameter');
        return res.status(400).json({ error: 'cntr_code query parameter is required' });
    }

    const normalizedCode = cntr_code.trim().toUpperCase();

    try {
        const regions = await Regions.findAll({
            attributes: ['name_latn', 'geom'],
            where: { cntr_code: normalizedCode },
            order: [['name_latn', 'ASC']]
        });

        return res.status(200).json(regions);
    } catch (error) {
        logger.error('Error fetching regions:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
});

export const DashboardController = router;
