import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const viteCli = resolve(root, 'node_modules/vite/bin/vite.js');
const uvicorn = process.platform === 'win32'
  ? resolve(root, 'services/.venv/Scripts/uvicorn.exe')
  : resolve(root, 'services/.venv/bin/uvicorn');

if (!existsSync(uvicorn)) {
  console.error('HELIOS backend environment not found. Run `uv sync` from the services directory first.');
  process.exit(1);
}

const children = [];
let shuttingDown = false;

function findFreePort() {
  return new Promise((resolvePort, reject) => {
    const probe = createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => {
      const address = probe.address();
      if (!address || typeof address === 'string') {
        probe.close();
        reject(new Error('Could not determine a free local port for the backend.'));
        return;
      }
      probe.close((error) => error ? reject(error) : resolvePort(address.port));
    });
  });
}

function stopChildren(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (child.exitCode === null && !child.killed) child.kill();
  }
  process.exitCode = exitCode;
}

function start(label, command, args, options) {
  const child = spawn(command, args, { stdio: 'inherit', ...options });
  children.push(child);
  child.on('error', (error) => {
    console.error(`[HELIOS] Could not start ${label}: ${error.message}`);
    stopChildren(1);
  });
  child.on('exit', (code) => {
    if (!shuttingDown) {
      console.error(`[HELIOS] ${label} exited${code === null ? '' : ` with code ${code}`}.`);
      stopChildren(code ?? 1);
    }
  });
}

process.on('SIGINT', () => stopChildren(0));
process.on('SIGTERM', () => stopChildren(0));

const backendPort = await findFreePort();
const apiBaseUrl = `http://127.0.0.1:${backendPort}/api/v1`;
const webEnv = { ...process.env, VITE_API_BASE_URL: apiBaseUrl };

start('backend', uvicorn, ['--app-dir', 'services', 'helios.main:app', '--host', '127.0.0.1', '--port', String(backendPort)], { cwd: root });
start('web frontend', process.execPath, [viteCli], { cwd: resolve(root, 'apps/web'), env: webEnv });

console.log(`[HELIOS] Starting API at ${apiBaseUrl} and web UI at http://localhost:3000.`);
