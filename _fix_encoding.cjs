const fs = require('fs');
const path = 'truthforge_frontend/truthforge-logistics-verified-main/src/components/CarrierPortal.tsx';
let content = fs.readFileSync(path, 'utf8');

// Replace the garbled UTF-8 em-dash sequences with proper em-dash
// The garbled sequence is the UTF-8 bytes for em-dash (0xE2 0x80 0x94) misread as latin1
content = content.split('\u00e2\u0080\u0094').join('\u2014');

fs.writeFileSync(path, content, 'utf8');
console.log('Fixed. Lines with em-dash:');
content.split('\n').forEach((line, i) => {
  if (line.includes('\u2014')) console.log(`  L${i+1}: ${line.trim()}`);
});
