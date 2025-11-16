from pathlib import Path
import textwrap

path = Path("server/src/controllers/DashboardController.ts")
text = path.read_text()

import_block = "import { execFile } from 'child_process';\n"
if "spawn" not in text:
    text = text.replace(import_block, "import { execFile, spawn } from 'child_process';\n")
    if "spawn" not in text:
        text = text.replace("from 'child_process'", "from 'child_process';\nimport type { ChildProcessWithoutNullStreams } from 'child_process'", 1)

pd_import = "import { logger } from '../config/logger.config';\n"
if "path" in text and "predic" not in text:
    text = text.replace(
        pd_import,
        pd_import + "import pathToFileURL from 'url';\n",
        1
    )

predicate_handler = textwrap.dedent('''
router.get('/predicate', async (req: Request, res: Response) => {
  logger.info('GET predicate endpoint called');

  const { country, target_year, categories } = req.query;
  if (typeof country !== 'string' || !country.trim()) {
    return res.status(400).json({ error: 'country query parameter is required' });
  }
  const year = typeof target_year === 'string' ? Number.parseInt(target_year, 10) : Number.NaN;
  if (!Number.isInteger(year)) {
    return res.status(400).json({ error: 'target_year query parameter must be a number' });
  }

  const categoriesArray: string[] = [];
  if (Array.isArray(categories)) {
    categories.forEach((entry) => {
      if (typeof entry === 'string' && entry.trim()) {
        categoriesArray.push(...entry.split(',').map((v) => v.trim()).filter(Boolean));
      }
    });
  } else if (typeof categories === 'string') {
    categoriesArray.push(...categories.split(',').map((v) => v.trim()).filter(Boolean));
  }

  const scriptPath = path.resolve(__dirname, '../python_scripts/train_profit_model.py');
  if (!fs.existsSync(scriptPath)) {
    return res.status(500).json({ error: 'train_profit_model.py script not found on server' });
  }

  const args = [
    '--suggest',
    '--country', country.trim(),
    '--year', year.toString(),
    '--top', '3',
  ];
  if (categoriesArray.length > 0) {
    args.push('--categories', ...categoriesArray);
  }

  try {
    const child = spawn('python', [scriptPath, ...args]);
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('close', (code) => {
      if (code !== 0) {
        logger.error('Predicate script failed', { code, stderr });
        return res.status(500).json({ error: 'Failed to compute prediction results' });
      }
      try {
        const payload = JSON.parse(stdout.trim());
        return res.status(200).json({ results: payload });
      } catch (parseError) {
        logger.error('Failed to parse predicate output', { stdout });
        return res.status(500).json({ error: 'Invalid prediction payload from script' });
      }
    });
  } catch (error) {
    logger.error('Error spawning predicate script', error);
    return res.status(500).json({ error: 'Failed to run prediction script' });
  }
});
''')

insert_marker = "router.get('/sowingmap', async (req: Request, res: Response) => {"
if predicate_handler not in text and insert_marker in text:
    text = text.replace(
        "router.get('/sowingmap", predicate_handler + "\nrouter.get('/sowingmap"
    )

path.write_text(text)
