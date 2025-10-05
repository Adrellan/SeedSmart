import { Router, Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { promisify } from 'util';
import { execFile } from 'child_process';
import { logger } from '../config/logger.config';
import { Countires } from '../models/Countires'; // (ha elgépelés, írd át Countries-re + importot is)
import { Regions } from '../models/Regions';
import { transformFeatureCollectionTo4326 } from '../helpers/geom_transfer';

const router = Router();
const execFileAsync = promisify(execFile);

const SCRIPT_CANDIDATES = [
  path.resolve(process.cwd(), 'src/python_scripts/find_top_crop.py'),
  path.resolve(process.cwd(), 'server/src/python_scripts/find_top_crop.py'),
  path.resolve(__dirname, '../python_scripts/find_top_crop.py'),
  path.resolve(__dirname, '../../python_scripts/find_top_crop.py'),
];

const SOWINGMAP_SCRIPT_CANDIDATES = [
  path.resolve(process.cwd(), 'src/python_scripts/extract_sowingmap_features.py'),
  path.resolve(process.cwd(), 'server/src/python_scripts/extract_sowingmap_features.py'),
  path.resolve(__dirname, '../python_scripts/extract_sowingmap_features.py'),
  path.resolve(__dirname, '../../python_scripts/extract_sowingmap_features.py'),
];

const PYTHON_MAX_BUFFER = 1024 * 1024 * 64;

const resolveFindTopCropScript = (): string => {
  for (const candidate of SCRIPT_CANDIDATES) {
    if (fs.existsSync(candidate)) return candidate;
  }
  const searched = SCRIPT_CANDIDATES.join(', ');
  logger.error('find_top_crop.py script not found. Checked paths: %s', searched);
  throw new Error(`find_top_crop.py script not found. Checked paths: ${searched}`);
};

const resolveSowingMapScript = (): string => {
  for (const candidate of SOWINGMAP_SCRIPT_CANDIDATES) {
    if (fs.existsSync(candidate)) return candidate;
  }
  const searched = SOWINGMAP_SCRIPT_CANDIDATES.join(', ');
  logger.error('extract_sowingmap_features.py script not found. Checked paths: %s', searched);
  throw new Error(`extract_sowingmap_features.py script not found. Checked paths: ${searched}`);
};

const collectCategoryLabels = (input: unknown): string[] => {
  const labels: string[] = [];
  const seen = new Set<string>();

  const addLabel = (value: string) => {
    value
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean)
      .forEach((entry) => {
        const normalized = entry.toLowerCase();
        if (seen.has(normalized)) return;
        seen.add(normalized);
        labels.push(entry);
      });
  };

  const processVal = (value: unknown): void => {
    if (value == null) return;
    if (Array.isArray(value)) {
      value.forEach(processVal);
      return;
    }
    addLabel(String(value));
  };

  processVal(input);
  return labels;
};

// ---------------------- ROUTES ----------------------

router.get('/countries', async (_req: Request, res: Response) => {
  logger.info('GET /countries endpoint called');
  try {
    const countries = await Countires.findAll();
    return res.status(200).json(countries);
  } catch (err) {
    logger.error('Error fetching countries: %o', err);
    return res.status(500).json({ error: 'Internal Server Error' });
  }
});

router.get('/regions', async (req: Request, res: Response) => {
  logger.info('GET /regions endpoint called');

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
      order: [['name_latn', 'ASC']],
    });
    return res.status(200).json(regions);
  } catch (err) {
    logger.error('Error fetching regions: %o', err);
    return res.status(500).json({ error: 'Internal Server Error' });
  }
});

router.get('/sowingmap', async (req: Request, res: Response) => {
  logger.info('GET /sowingmap endpoint called');

  const { coordinates } = req.query;
  if (typeof coordinates !== 'string' || !coordinates.trim()) {
    logger.warn('Missing coordinates query parameter');
    return res.status(400).json({ error: 'coordinates query parameter is required' });
  }

  let scriptPath: string;
  try {
    scriptPath = resolveSowingMapScript();
  } catch (err) {
    logger.error('SowingMap script missing: %o', err);
    return res.status(500).json({ error: 'Server misconfiguration: helper script not found' });
  }

  const args = ['--coordinates', coordinates.trim()];

  try {
    const { stdout } = await execFileAsync('python', [scriptPath, ...args], { maxBuffer: PYTHON_MAX_BUFFER });
    const rawPayload = stdout.trim() ? JSON.parse(stdout.trim()) : { count: 0, features: [] };

    // 🔁 PROJ: EPSG:3857 -> EPSG:4326 MIELŐTT válaszolunk
    const payload4326 = transformFeatureCollectionTo4326(rawPayload);

    res.set('Cache-Control', 'max-age=3600');
    return res.status(200).json(payload4326);
  } catch (err) {
    logger.error('Error extracting sowing map data: %o', err);
    return res.status(500).json({ error: 'Failed to retrieve sowing map data' });
  }
});

router.get('/topic', async (req: Request, res: Response) => {
  logger.info('GET /topic endpoint called');

  const { country, year } = req.query;
  const rawCategoryInput = req.query.category_label;

  if (typeof country !== 'string' || !country.trim()) {
    return res.status(400).json({ error: 'country query parameter is required' });
  }

  const yearNumber = typeof year === 'string' ? Number.parseInt(year, 10) : Number.NaN;
  if (!Number.isInteger(yearNumber)) {
    return res.status(400).json({ error: 'year query parameter must be a number' });
  }

  let scriptPath: string;
  try {
    scriptPath = resolveFindTopCropScript();
  } catch (err) {
    logger.error('FindTopCrop script missing: %o', err);
    return res.status(500).json({ error: 'Server misconfiguration: helper script not found' });
  }

  const categoryLabels = collectCategoryLabels(rawCategoryInput);

  const args = ['--country', country.trim(), '--year', yearNumber.toString()];
  categoryLabels.forEach((label) => {
    args.push('--category_label', label);
  });

  try {
    const { stdout } = await execFileAsync('python', [scriptPath, ...args], { maxBuffer: PYTHON_MAX_BUFFER });
    const payload = stdout.trim() ? JSON.parse(stdout.trim()) : {};
    return res.status(200).json(payload);
  } catch (err) {
    logger.error('Error fetching topic data: %o', err);
    return res.status(500).json({ error: 'Failed to retrieve topic data' });
  }
});

export const DashboardController = router;
