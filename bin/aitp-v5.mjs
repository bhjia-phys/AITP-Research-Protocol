#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const uvCommand = process.env.AITP_UV_COMMAND ?? 'uv';
const pythonCommand = process.env.AITP_PYTHON_COMMAND ?? 'python';

const child = spawn(
  uvCommand,
  ['run', '--with', 'pyyaml', pythonCommand, '-m', 'brain.v5.cli', ...process.argv.slice(2)],
  {
    cwd: repoRoot,
    stdio: 'inherit',
    windowsHide: true,
  },
);

child.on('error', (error) => {
  console.error(`aitp-v5 failed to start ${uvCommand}: ${error.message}`);
  process.exit(1);
});

child.on('exit', (code, signal) => {
  if (signal !== null) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
