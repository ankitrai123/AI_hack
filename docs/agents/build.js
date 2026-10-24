// Renders docs/agents/opslab-agents.html to docs/OpsLab_AI_Agents.pdf (needs Playwright + Chromium).
const {chromium} = require('playwright'), path = require('path');
(async () => {
  const b = await chromium.launch(), pg = await b.newPage();
  await pg.goto('file://' + path.join(__dirname, 'opslab-agents.html'));
  await pg.waitForTimeout(500);
  await pg.pdf({path: path.join(__dirname, '..', 'OpsLab_AI_Agents.pdf'), format: 'A4', printBackground: true, margin: {top: 0, right: 0, bottom: 0, left: 0}});
  await b.close(); console.log('ok');
})();
