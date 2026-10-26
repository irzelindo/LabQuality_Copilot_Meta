const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const project = path.resolve(__dirname, '../..');
const local = path.join(project, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const python = process.env.LQ_TEST_PYTHON || (fs.existsSync(local) ? local : 'python');
const directory = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'labquality-e2e-'));
const env = { ...process.env, LQ_DATABASE_URL: 'sqlite:///' + path.join(directory, 'test.db').replace(/\\/g, '/'),
  LQ_STORAGE_DIR: path.join(directory, 'storage'), LQ_MODEL_API_KEY: '', LQ_SMTP_HOST: '', LQ_ODK_URL: '',
  LQ_ALLOWED_ORIGINS: 'http://127.0.0.1:3100', LQ_DEMO_PASSWORD: 'Local-e2e-test-only-2026!', LQ_COOKIE_SECURE: 'false' };
const options = { cwd: path.join(project, 'backend'), env, stdio: 'inherit' };
const bootstrap = spawnSync(python, ['-m', 'app.bootstrap', '--demo'], options);
if (bootstrap.status !== 0) process.exit(bootstrap.status || 1);
const server = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '18000'], options);
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => { server.kill(signal); process.exit(0); });
server.on('exit', code => process.exit(code || 0));
