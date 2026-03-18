const { execSync } = require('child_process');
const fs = require('fs');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe', timeout: 60000 });
  } catch (e) {
    return (e.stdout || '') + '\nERR: ' + (e.stderr || '') + '\n' + (e.message || '');
  }
}

const out = [];

out.push('=== STATUS ===');
out.push(run('git status --short'));

out.push('=== ADD ===');
out.push(run('git add -A'));

out.push('=== COMMIT ===');
out.push(run('git commit -m "fix: remove hashpack wallet-connect from CarrierPortalPage and CarrierPortal, fix encoding junk, unblock Vercel build"'));

out.push('=== PUSH ===');
out.push(run('git push origin main'));

out.push('=== LOG ===');
out.push(run('git log --oneline -5'));

const result = out.join('\n');
fs.writeFileSync('_push_out.txt', result);
console.log(result);
