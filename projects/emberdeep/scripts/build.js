// Copies the game into dist/ and zips it for itch.io (upload the zip, tick "This file will be played in the browser").
import { cpSync, rmSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
rmSync('dist', { recursive: true, force: true });
mkdirSync('dist/emberdeep', { recursive: true });
for (const p of ['index.html', 'src', 'assets']) cpSync(p, `dist/emberdeep/${p}`, { recursive: true });
execFileSync('zip', ['-qr', '../emberdeep-html5.zip', '.'], { cwd: 'dist/emberdeep' });
console.log('dist/emberdeep-html5.zip');
