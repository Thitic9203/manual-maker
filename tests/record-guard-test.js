#!/usr/bin/env node
/* Known-answer tests for the one-way-step guard in skills/screen-record/scripts/record.js.
 *
 * The incident these pin: a play typed into a search box, then clicked a POSITIONAL selector
 * (`tbody tr:nth-child(1) button`) that already matched the UNFILTERED first row, picked a reason
 * and clicked confirm — a one-way write landed on the wrong item. Every case below runs the real
 * record.js against a local fixture server (127.0.0.1, random port) and counts the write requests
 * that actually reached that server. No stubs, no real site.
 *
 * Must FAIL (non-zero exit, zero writes reach the server):
 *   F1 positional click before an irreversible step, no expectTarget between -> rejected at load
 *      (before any browser action: the server sees no request at all)
 *   F2 irreversible step with no expectTarget anywhere before it -> rejected at load
 *   F3 expectTarget mismatch -> aborted before the irreversible click
 *   F4 a write request fired outside an irreversible step -> aborted, run fails
 * Must PASS:
 *   P1 expectTarget matches -> runs, exactly one write, on the expected item
 *   P2 a play with no irreversible step -> unchanged behaviour (its write goes through)
 *
 *   NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node --test tests/record-guard-test.js
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const RECORD = path.join(__dirname, '..', 'skills', 'screen-record', 'scripts', 'record.js');

// A list of two items. The search box filters client-side, so after typing "Beta" the first row
// is Beta — but a selector evaluated against the unfiltered table finds Alpha first. "Review"
// opens a dialog naming the item; "Confirm" POSTs the vote. "Save draft" POSTs outside any
// one-way step (used by F4/P2).
const PAGE = `<!doctype html><html><head><meta charset="utf-8"><title>fixture</title></head><body>
<input id="q" placeholder="search">
<button id="draft" onclick="fetch('/draft',{method:'POST',body:'x'}).then(()=>{document.getElementById('saved').hidden=false})">Save draft</button>
<span id="saved" hidden>draft saved</span>
<table><tbody id="rows"></tbody></table>
<div id="dlg" hidden><h2 id="dlg-title"></h2>
  <select id="reason"><option value="">-</option><option value="spam">spam</option></select>
  <button id="confirm">Confirm</button></div>
<span id="done" hidden>vote sent</span>
<script>
const items=[{id:'a1',title:'Alpha'},{id:'b2',title:'Beta'}];
let current=null;
function render(f){const tb=document.getElementById('rows');tb.innerHTML='';
  items.filter(i=>i.title.includes(f||'')).forEach(i=>{const tr=document.createElement('tr');
    tr.innerHTML='<td>'+i.title+'</td><td><button class="review">Review</button></td>';
    tr.querySelector('button').onclick=()=>{current=i;const t=document.getElementById('dlg-title');
      t.textContent=i.title;t.dataset.id=i.id;document.getElementById('dlg').hidden=false;};
    tb.appendChild(tr);});}
render('');
// Filtering lags like a real search request does, which is what made the incident possible.
document.getElementById('q').addEventListener('input',e=>{const v=e.target.value;setTimeout(()=>render(v),1500);});
document.getElementById('confirm').onclick=()=>fetch('/vote',{method:'POST',body:current.id})
  .then(()=>{document.getElementById('done').hidden=false;});
</script></body></html>`;

function startServer() {
  const log = { all: 0, writes: [] };
  const srv = http.createServer((req, res) => {
    log.all++;
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      if (req.method !== 'GET' && req.method !== 'HEAD') log.writes.push({ method: req.method, url: req.url, body });
      res.writeHead(200, { 'content-type': req.url === '/' ? 'text/html; charset=utf-8' : 'text/plain' });
      res.end(req.url === '/' ? PAGE : 'ok');
    });
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r({ srv, log, port: srv.address().port })));
}

function run(play) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sr-guard-test-'));
  const file = path.join(dir, 'play.json');
  // Capture rate is not under test here, and a static fixture page legitimately emits few
  // screencast frames — the floor is lowered for THIS fixture only so the guard is what decides.
  fs.writeFileSync(file, JSON.stringify(Object.assign({
    name: 'guard', out: path.join(dir, 'out'), viewport: { width: 800, height: 600 },
    deviceScaleFactor: 1, minUniqueFps: 0, settle: 200, tail: 200, glideSteps: 4, typeDelay: 0,
    preset: 'ultrafast',
  }, play)));
  return new Promise((resolve) => {
    const p = spawn(process.execPath, [RECORD, file], { env: process.env });
    let out = '';
    p.stdout.on('data', (d) => { out += d; });
    p.stderr.on('data', (d) => { out += d; });
    p.on('close', (code) => { fs.rmSync(dir, { recursive: true, force: true }); resolve({ code, out }); });
  });
}

const search = { do: 'fill', selector: '#q', value: 'Beta' };
const openFirst = { do: 'click', selector: 'tbody tr:nth-child(1) button.review', waitFor: '#dlg-title' };
const reason = { do: 'select', selector: '#reason', value: 'spam' };
const confirm = { do: 'click', selector: '#confirm', irreversible: true, waitFor: 'text=vote sent' };

let S;
test.before(async () => { S = await startServer(); });
test.after(() => S.srv.close());
test.beforeEach(() => { S.log.all = 0; S.log.writes = []; });
const base = () => `http://127.0.0.1:${S.port}`;

test('F1 positional click before an irreversible step without expectTarget is rejected at load', async () => {
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' }, search, openFirst, reason, confirm] });
  assert.notStrictEqual(r.code, 0, r.out);
  assert.match(r.out, /positional/i);
  assert.strictEqual(S.log.all, 0, 'no browser action may happen before the play is rejected');
});

test('F2 irreversible step with no expectTarget at all is rejected at load', async () => {
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' }, reason, confirm] });
  assert.notStrictEqual(r.code, 0, r.out);
  assert.match(r.out, /expectTarget/);
  assert.strictEqual(S.log.all, 0);
});

test('F3 expectTarget mismatch aborts before the irreversible click', async () => {
  // No wait for the filter: the positional click lands on the unfiltered first row (Alpha) —
  // the incident exactly. The assertion must catch it before Confirm is pressed.
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' }, search, openFirst, reason,
    Object.assign({}, confirm, { expectTarget: { selector: '#dlg-title', text: 'Beta' } })] });
  assert.notStrictEqual(r.code, 0, r.out);
  assert.match(r.out, /expectTarget mismatch .* text is "Alpha", expected "Beta"/);
  assert.deepStrictEqual(S.log.writes, [], 'the one-way write must never reach the server');
});

test('F4 a write request outside an irreversible step is aborted and fails the run', async () => {
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' },
    { do: 'click', selector: '#draft' },
    Object.assign({}, confirm, { expectTarget: { selector: '#dlg-title', text: 'Beta' } })] });
  assert.notStrictEqual(r.code, 0, r.out);
  assert.match(r.out, /outside an irreversible step/);
  assert.deepStrictEqual(S.log.writes, []);
});

test('P1 matching expectTarget runs, and the one write lands on the expected item', async () => {
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' }, search,
    { do: 'waitFor', selector: 'tbody tr:nth-child(1) >> text=Beta' }, openFirst, reason,
    Object.assign({}, confirm, { expectTarget: { selector: '#dlg-title', id: 'b2' } })] });
  assert.strictEqual(r.code, 0, r.out);
  assert.deepStrictEqual(S.log.writes.map((w) => [w.method, w.url, w.body]), [['POST', '/vote', 'b2']]);
});

test('P2 a play with no irreversible step behaves as before', async () => {
  const r = await run({ baseUrl: base(), steps: [{ do: 'goto', url: '/' },
    { do: 'click', selector: '#draft', waitFor: 'text=draft saved' }] });
  assert.strictEqual(r.code, 0, r.out);
  assert.deepStrictEqual(S.log.writes.map((w) => [w.method, w.url]), [['POST', '/draft']]);
});
