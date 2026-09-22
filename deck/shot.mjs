import { chromium } from 'playwright';
const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg = await b.newPage({ viewport: { width: 1400, height: 860 } });
await pg.goto('file://' + process.cwd() + '/deck.html');
await pg.waitForTimeout(3500);
for (const i of [13,15]) {
  await pg.evaluate(n => document.querySelectorAll('.s').forEach((s,k)=>s.classList.toggle('on', k===n)), i);
  await pg.waitForTimeout(300);
  await pg.screenshot({ path: 'p' + (i+1) + '.png' });
}
await b.close(); console.log('ok');
