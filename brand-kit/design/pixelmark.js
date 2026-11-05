/* After Tokens wordmark, drawn the way the website hero draws it: "After" as white Soehne Buch text,
   "Tokens" as a grid of sharp green squares sampled from the same text (site: sample every step px,
   alpha > 100, square = step - gap), plus the cover's explosion: the "ns" breaks apart and its pixels
   blow out to the right, up and down. Everything is drawn in whole device pixels, so it stays sharp.

   PixelMark.draw(canvas, opts) -> metrics (CSS px)
     cap       target cap height of the letters, CSS px
     layout    'inline' | 'stacked'
     dpr       device pixel ratio to draw at (default window.devicePixelRatio)
     rows      pixel rows across the cap height (default 24; site hero ~60, Luma cover ~25)
     explode   0..1 strength (default 1), seed, reachX / reachUp / reachDown in cap heights
*/
(function () {
  const GREEN = '#92e759', WHITE = '#ffffff', TRACK = -0.073, CAP = 0.7; // Soehne cap height ~0.7 em
  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  async function ready() { await document.fonts.load('400 100px "Soehne Buch"'); }
  function font(px) { return `400 ${px}px "Soehne Buch"`; }
  function setup(ctx, px) { ctx.font = font(px); ctx.letterSpacing = (TRACK * px) + 'px'; ctx.textBaseline = 'alphabetic'; }

  function draw(cv, o) {
    const dpr = o.dpr || window.devicePixelRatio || 1;
    const rows = o.rows || 24, seed = o.seed || 7, ex = o.explode == null ? 1 : o.explode;
    const capDev = o.cap * dpr;
    // grid: whole device pixels; visible gap like the site (square = 85% of the pitch) once the pitch allows it
    const step = Math.max(o.minStep || 4, Math.round(capDev / rows)); // >= 4 device px: square 3 + 1px gap, sharp and bright
    const gap = step >= 3 ? Math.max(1, Math.round(step * 0.15)) : 0;
    const sq = step - gap;
    const fpx = Math.round(capDev / CAP);
    const m = document.createElement('canvas').getContext('2d'); setup(m, fpx);
    const wA = m.measureText('After'), wT = m.measureText('Tokens');
    const ascA = Math.ceil(wA.actualBoundingBoxAscent), ascT = Math.ceil(wT.actualBoundingBoxAscent);
    const wordGap = Math.round(fpx * 0.24), lead = Math.round(fpx * 0.81);
    const reachX = (o.reachX == null ? 0.75 : o.reachX) * capDev * ex;
    const reachUp = (o.reachUp == null ? 0.45 : o.reachUp) * capDev * ex;
    const reachDown = (o.reachDown == null ? 0.55 : o.reachDown) * capDev * ex;
    const padL = Math.ceil(Math.max(0, -wA.actualBoundingBoxLeft) + 2);
    // positions (device px) of the two baselines
    let ax = padL, tx, bA, bT, W, H, top;
    if (o.layout === 'stacked') {
      top = Math.ceil(Math.max(ascA, 0));
      bA = top; bT = top + lead; tx = padL;
      W = Math.ceil(Math.max(wA.width, wT.width) + padL + reachX + step * 2);
      H = Math.ceil(bT + reachDown + step);
    } else {
      top = Math.ceil(Math.max(ascA, ascT) + reachUp);
      bA = bT = top; tx = Math.round(ax + wA.width + wordGap);
      W = Math.ceil(tx + wT.width + reachX + step * 2);
      H = Math.ceil(bT + reachDown + step);
    }
    cv.width = W; cv.height = H;
    cv.style.width = W / dpr + 'px'; cv.style.height = H / dpr + 'px';
    const ctx = cv.getContext('2d'); ctx.clearRect(0, 0, W, H);
    setup(ctx, fpx); ctx.fillStyle = WHITE; ctx.fillText('After', ax, bA);
    // sample "Tokens" on the site grid
    const off = document.createElement('canvas'); off.width = W; off.height = H;
    const oc = off.getContext('2d'); setup(oc, fpx); oc.fillStyle = '#fff'; oc.fillText('Tokens', tx, bT);
    const data = oc.getImageData(0, 0, W, H).data;
    const x0 = tx - ((tx) % step), y0 = (bT - ascT) - ((bT - ascT) % step) - step;
    const cells = [];
    for (let y = y0; y < bT + step; y += step)
      for (let x = x0; x < tx + wT.width + step; x += step) {
        const cx = Math.min(W - 1, x + (step >> 1)), cy = Math.min(H - 1, y + (step >> 1));
        if (cx >= 0 && cy >= 0 && data[(cy * W + cx) * 4 + 3] > 100) cells.push({ x, y });
      }
    // the "ns": where the explosion starts
    const right = Math.max(...cells.map((c) => c.x + step));
    const nStart = tx + m.measureText('Toke').width + fpx * TRACK * 0;
    const span = right - nStart;
    const R = rng(seed), flying = [];
    ctx.fillStyle = GREEN;
    for (const c of cells) {
      const u = (c.x - nStart) / span;                    // 0 at the n, 1 at the s's right edge
      const p = u <= 0.5 ? 0 : Math.pow((u - 0.5) / 0.5, 1.8) * (o.erode == null ? 0.55 : o.erode) * ex; // the s frays at its right edge, the word still reads
      if (R() < p) flying.push({ c, u }); else ctx.fillRect(c.x + (gap >> 1), c.y + (gap >> 1), sq, sq);
    }
    // blown-out pixels: the ones that broke off plus a spray beyond the s, thinning with distance
    const cy0 = bT - ascT * 0.5;
    // o.snap: blown-out pixels land on the letters' own grid, one square per cell, so none overlap
    const taken = new Set(o.snap ? cells.map((c) => c.x + ',' + c.y) : []);
    const put = (x, y, s) => {
      if (o.snap) {
        const gx = x0 + Math.round((x - x0) / step) * step, gy = y0 + Math.round((y - y0) / step) * step, k = gx + ',' + gy;
        if (taken.has(k)) return; taken.add(k);
        x = gx + (gap >> 1); y = gy + (gap >> 1); s = sq;
      }
      x = Math.round(x); y = Math.round(y); s = Math.max(1, Math.round(s)); if (x >= 0 && y >= 0 && x + s <= W && y + s <= H) ctx.fillRect(x, y, s, s);
    };
    for (const f of flying) {
      const t = Math.pow(R(), 1.4);
      const dx = step * (0.5 + t * 4) + f.u * reachX * 0.25 * R();
      const dy = (f.c.y + step / 2 - cy0) * (0.15 + t * 0.6) + (R() - 0.5) * step * 3;
      put(f.c.x + dx, f.c.y + dy, sq);
    }
    const extra = Math.round((o.spray == null ? 1 : o.spray) * ex * 1.1 * Math.sqrt(cells.length));
    for (let i = 0; i < extra; i++) {
      const t = Math.pow(R(), 1.25);                       // most stay close to the s
      const x = right - step * 2 + t * reachX;
      const up = R() < 0.5;
      const spreadY = (up ? reachUp + ascT * 0.55 : reachDown + ascT * 0.45) * (0.25 + 0.75 * t);
      const y = cy0 + (up ? -1 : 1) * Math.pow(R(), 0.8) * spreadY;
      const s = sq * (R() < 0.18 ? 1.5 : 1) * (t > 0.75 && R() < 0.5 ? 0.75 : 1);
      put(x, y, s);
    }
    return { afterTop: (bA - ascA) / dpr, width: W / dpr, height: H / dpr, baselineA: bA / dpr, baselineT: bT / dpr, capTop: (bT - ascT) / dpr, step: step / dpr, square: sq / dpr, rows: Math.round(ascT / step), lettersRight: right / dpr, afterRight: (ax + wA.width) / dpr };
  }
  window.PixelMark = { ready, draw };
})();
