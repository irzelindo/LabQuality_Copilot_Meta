const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const standalone = path.join(root, '.next', 'standalone');
if (!fs.existsSync(path.join(standalone, 'server.js'))) throw new Error('Run npm run build first.');
for (const [source, target] of [['public','public'],['.next/static','.next/static']]) {
  const input = path.join(root, source);
  if (fs.existsSync(input)) fs.cpSync(input, path.join(standalone, target), { recursive: true });
}
process.env.HOSTNAME = process.env.LQ_WEB_HOST || '127.0.0.1';
require(path.join(standalone, 'server.js'));
