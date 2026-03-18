const { execSync } = require('child_process');
const fs = require('fs');

const cwd = 'truthforge_frontend/truthforge-logistics-verified-main';

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe', ...opts });
  } catch (e) {
    return e.stdout + '\n' + e.stderr;
  }
}

const out = [];

out.push(run('git add -A', { cwd: process.cwd() }));
out.push(run('git status --short', { cwd: process.cwd() }));
out.push(run('git commit -m "fix: remove hedera-wallet-connect entirely — unblock Vercel build"', { cwd: process.cwd() }));
out.push(run('git push origin main', { cwd: process.cwd() }));

fs.writeFileSync('_git_out.txt', out.join('\n'));
console.log(out.join('\n'));
