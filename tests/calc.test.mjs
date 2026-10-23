// node --test tests/calc.test.mjs — cálculos da página (js/calc.js)
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const C = createRequire(import.meta.url)('../js/calc.js');
const U = s => Date.parse(s + 'T00:00:00Z');
const bdays = (from, to) => { const o = []; for (let t = U(from); t <= U(to); t += C.DAY) { const w = new Date(t).getUTCDay(); if (w && w < 6) o.push(t) } return o };
const iso = ms => new Date(ms).toISOString().slice(0, 10);

test('minus respeita o fim do mês', () => {
  assert.equal(iso(C.minus(U('2026-03-31'), 1)), '2026-02-28');
  assert.equal(iso(C.minus(U('2026-10-21'), 12)), '2025-10-21');
});

test('windowStart: base é o último fechamento antes da janela', () => {
  const t = bdays('2025-11-03', '2026-10-21'), at = p => iso(t[C.windowStart(t, p)]);
  assert.equal(at('YTD'), '2025-12-31');
  assert.equal(at('MTD'), '2026-09-30');
  assert.equal(at('QTD'), '2026-09-30');
  assert.equal(at('1D'), '2026-10-20');
  assert.equal(at('5D'), '2026-10-14');
  assert.equal(at('1M'), '2026-09-21');
});

test('compute: acumulado, relativo e móvel', () => {
  const src = { t: [0, 1, 2, 3].map(i => U('2026-01-05') + i * C.DAY), s: { A: [100, 110, 121, 133.1], B: [null, 50, 55, 60], BM: [10, 10, 11, 11] } };
  const acc = C.compute(src, { keys: ['A', 'B', 'BM'], bm: 'BM', i0: 0, mode: 'acc', rel: false, k: 0 });
  assert.ok(Math.abs(acc.s.A[3] - 0.331) < 1e-12);
  assert.equal(acc.s.B[0], null); assert.ok(Math.abs(acc.s.B[3] - 0.2) < 1e-12);
  assert.equal(iso(acc.late.B), '2026-01-06');
  const rel = C.compute(src, { keys: ['A'], bm: 'BM', i0: 0, mode: 'acc', rel: true, k: 0 });
  assert.ok(Math.abs(rel.s.A[3] - (1.331 / 1.1 - 1)) < 1e-12); // razão setor/benchmark rebaseada
  const rot = C.compute(src, { keys: ['A'], bm: 'BM', i0: 1, mode: 'rot', rel: false, k: 1 });
  assert.deepEqual(rot.s.A.map(v => +v.toFixed(10)), [0.1, 0.1, 0.1]);
});

test('timeTicks: rótulos de ano/mês nunca se repetem (bug do 2025 duplicado)', () => {
  const lab = (t, x) => x.u === 'y' ? new Date(t[x.j]).getUTCFullYear() : x.u === 'm' ? new Date(t[x.j]).toISOString().slice(0, 7) : t[x.j];
  for (const [from, to] of [['2021-10-22', '2026-10-21'], ['2023-10-20', '2026-10-21'], ['2016-10-21', '2026-10-21'], ['2025-10-21', '2026-10-21'], ['2026-07-21', '2026-10-21']]) {
    const weekly = bdays(from, to).filter(t => new Date(t).getUTCDay() === 5);
    for (const t of [weekly, bdays(from, to)]) for (const n of [4, 7]) {
      const ticks = C.timeTicks(t, n), labs = ticks.map(x => lab(t, x));
      assert.equal(new Set(labs).size, labs.length, `${from}..${to} n=${n}: ${labs}`);
      assert.ok(ticks.length <= n && ticks.length >= 2, `${from}..${to} n=${n}: ${ticks.length}`);
    }
  }
});
