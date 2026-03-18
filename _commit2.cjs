const { execSync } = require('child_process');
const fs = require('fs');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe' });
  } catch (e) {
    return (e.stdout || '') + (e.stderr || '');
  }
}

const out = [];
out.push('=== STATUS ===');
out.push(run('git status --short'));
out.push('=== ADD ===');
out.push(run('git add -A'));
out.push('=== STATUS AFTER ADD ===');
out.push(run('git status --short'));
out.push('=== COMMIT ===');
out.push(run('git commit -m "fix: strip wallet from CarrierPortalPage, remove junk temp files"'));
out.push('=== PUSH ===');
out.push(run('git push origin main'));
out.push('=== LOG ===');
out.push(run('git log --oneline -4'));

const result = out.join('\n');
fs.writeFileSync('_commit2_out.txt', result);
console.log(result);
