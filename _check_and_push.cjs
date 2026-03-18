const { execSync } = require('child_process');
const fs = require('fs');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe', timeout: 30000 });
  } catch (e) {
    return (e.stdout || '') + '\nERR:' + (e.stderr || '') + '\n' + (e.message || '');
  }
}

const out = [];

// Check what's in HEAD for CarrierPortalPage
const carrier = run('git show HEAD:truthforge_frontend/truthforge-logistics-verified-main/src/pages/CarrierPortalPage.tsx');
out.push('CARRIER_HAS_WALLET: ' + (carrier.includes('handleConnectWallet') || carrier.includes('walletModalOpen')));
out.push('CARRIER_FIRST_IMPORT: ' + carrier.split('\n').slice(0, 5).join(' | '));

// Check package.json
const pkg = run('git show HEAD:truthforge_frontend/truthforge-logistics-verified-main/package.json');
out.push('PKG_HAS_HASHGRAPH: ' + pkg.includes('@hashgraph'));
out.push('PKG_HAS_WALLETCONNECT: ' + pkg.includes('@walletconnect'));

// Push
out.push('=== PUSH ===');
out.push(run('git push origin main'));

fs.writeFileSync('_check_out.txt', out.join('\n'));
console.log(out.join('\n'));
