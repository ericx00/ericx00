// Zero-dependency static server (ES modules don't load from file://).
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { join, extname, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const port = Number(process.argv[2] ?? 5173);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml' };

createServer(async (req, res) => {
  let p = join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(root)) return res.writeHead(403).end();
  try {
    if ((await stat(p)).isDirectory()) p = join(p, 'index.html');
    res.writeHead(200, { 'content-type': types[extname(p)] ?? 'application/octet-stream' }).end(await readFile(p));
  } catch {
    res.writeHead(404).end('Not found');
  }
}).listen(port, () => console.log(`SensForge at http://localhost:${port}`));
