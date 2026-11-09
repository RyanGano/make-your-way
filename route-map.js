// The route map, drawn as a storybook trail. Each place you've been is a round vignette cut from
// its illustration, joined to the next by an inked trail. Places one step beyond where you've been
// are hidden under clouds, each a different piece of one cloud drawing (art/clouds.webp). The rest
// of the story stays off the map until you get near it.
(function (root) {

const ROW = 180;   // vertical distance between rows of places
const SX = 1.7;     // horizontal stretch of the layout
const GAP = 140;    // closest two places in a row may sit, so their labels don't collide
const R = 36;       // vignette radius (endings are a little bigger)
const BELOW = 40;   // a trail leaves from below its place's label
const MARGIN = 74;
const MIN_W = 560;

// Rows by longest distance from the start, so every choice leads downward.
function layout(story) {
  const ids = story.order;
  const depth = { [story.start]: 0 };
  const indeg = Object.fromEntries(ids.map((id) => [id, 0]));
  ids.forEach((id) => story.passages[id].choices.forEach((c) => indeg[c.to]++));
  const queue = ids.filter((id) => indeg[id] === 0);
  while (queue.length) {
    const id = queue.shift();
    for (const c of story.passages[id].choices) {
      depth[c.to] = Math.max(depth[c.to] ?? 0, (depth[id] ?? 0) + 1);
      if (--indeg[c.to] === 0) queue.push(c.to);
    }
  }

  const rows = [];
  ids.forEach((id) => (rows[depth[id]] ||= []).push(id));
  const parents = {};
  ids.forEach((id) => story.passages[id].choices.forEach((c) => (parents[c.to] ||= []).push(id)));

  // A couple of sweeps placing each node under the average of its parents keeps crossings down.
  const pos = {};
  const place = () => rows.forEach((row) => row.forEach((id, i) => (pos[id] = (i + 1) / (row.length + 1))));
  place();
  for (let sweep = 0; sweep < 3; sweep++) {
    rows.forEach((row, d) => {
      if (!d) return;
      const key = (id) => {
        const ps = parents[id] || [];
        return ps.length ? ps.reduce((n, p) => n + pos[p], 0) / ps.length : pos[id];
      };
      row.sort((a, b) => key(a) - key(b));
    });
    place();
  }

  const at = {};
  rows.forEach((row, d) => row.forEach((id) => (at[id] = { x: 20 + pos[id] * 320, y: 26 + d * 54, row: d })));
  return { at };
}

// ---------- hand-drawn line helpers ----------

// Seeded noise, so the wobble and the clouds are the same on every visit.
function rng(seed) {
  return () => {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const hash = (s) => [...s].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 16777619), 2166136261);
const f1 = (n) => n.toFixed(1);

// A smooth path through the points (Catmull-Rom).
function smooth(pts) {
  const P = (i) => pts[Math.max(0, Math.min(pts.length - 1, i))];
  let d = `M${f1(pts[0][0])} ${f1(pts[0][1])}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    d += ` C${f1(p1[0] + (p2[0] - p0[0]) / 6)} ${f1(p1[1] + (p2[1] - p0[1]) / 6)} ${f1(p2[0] - (p3[0] - p1[0]) / 6)} ${f1(p2[1] - (p3[1] - p1[1]) / 6)} ${f1(p2[0])} ${f1(p2[1])}`;
  }
  return d;
}

// The trail from one place to the next, from under the first one's label to the top of the next
// one's ring (or into the middle of its cloud). It bows aside when it skips rows, and is sampled and
// nudged a little so it looks drawn by hand.
function trailPath(p, q, w, seed, into) {
  const span = Math.round((q.y - p.y) / ROW);
  const y0 = p.y + R + BELOW, y1 = q.y - into, m = (y0 + y1) / 2;
  let c = [[p.x, y0], [p.x, m], [q.x, m], [q.x, y1]];
  if (span > 1) {
    const side = q.x > p.x ? 1 : q.x < p.x ? -1 : (p.x > w / 2 ? -1 : 1);
    const off = side * Math.min(160, 55 * span);
    c = [[p.x, y0], [p.x + off, y0 + ROW * 0.6], [q.x + off, y1 - ROW * 0.6], [q.x, y1]];
  }
  // Short trails get fewer, gentler wobbles than long ones, or they look scribbled.
  const len = Math.hypot(q.x - p.x, y1 - y0) + (span > 1 ? 200 : 0);
  const r = rng(seed), n = Math.max(4, Math.min(16, Math.round(len / 30))), amp = Math.min(4, len / 40), pts = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t;
    const pt = [0, 1].map((k) => u * u * u * c[0][k] + 3 * u * u * t * c[1][k] + 3 * u * t * t * c[2][k] + t * t * t * c[3][k]);
    if (i && i < n) { pt[0] += (r() - 0.5) * amp; pt[1] += (r() - 0.5) * amp; }
    pts.push(pt);
  }
  return smooth(pts);
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);

// A short name for a place: the caption's first sentence, in at most two lines.
function labelLines(text, width = 21) {
  const words = text.split(/\.\s/)[0].replace(/\.$/, "").split(/\s+/);
  const lines = [""];
  for (const word of words) {
    const line = lines.at(-1);
    if (!line || (line + " " + word).length <= width) lines[lines.length - 1] = line ? `${line} ${word}` : word;
    else if (lines.length < 2) lines.push(word);
    else { lines[1] = (lines[1] + " " + word).slice(0, width - 1).replace(/\s*\S*$/, "") + "…"; break; }
  }
  return lines;
}

// ---------- the map ----------

// trail: "from>to" steps taken on any reading; path: the current reading; art: the scene names
// that have a drawing.
function render(story, { trail, path, art = new Set() }) {
  const { at } = layout(story);
  const walked = new Set(trail);
  const seen = new Set([story.start, ...trail.flatMap((t) => t.split(">"))]);
  const visible = new Set(seen);
  seen.forEach((id) => story.passages[id]?.choices.forEach((c) => visible.add(c.to)));
  const now = new Set(path.slice(1).map((id, i) => `${path[i]}>${id}`));
  const current = path.at(-1);

  // Only the rows that have something on them, closed up so the map doesn't have empty bands.
  const usedRows = [...new Set([...visible].map((id) => at[id].row))].sort((a, b) => a - b);
  const rowOf = Object.fromEntries(usedRows.map((r, i) => [r, i]));
  const pos = {};
  visible.forEach((id) => (pos[id] = { x: (at[id].x - 20) * SX, y: 46 + rowOf[at[id].row] * ROW }));

  // Push apart places that would crowd each other in a row, keeping the row where it was.
  usedRows.forEach((r) => {
    const row = [...visible].filter((id) => at[id].row === r).sort((a, b) => pos[a].x - pos[b].x);
    const mean = row.reduce((n, id) => n + pos[id].x, 0) / row.length;
    for (let i = 1; i < row.length; i++) pos[row[i]].x = Math.max(pos[row[i]].x, pos[row[i - 1]].x + GAP);
    const shift = mean - row.reduce((n, id) => n + pos[id].x, 0) / row.length;
    row.forEach((id) => (pos[id].x += shift));
  });
  const xs = [...visible].map((id) => pos[id].x);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const W = Math.max(MIN_W, maxX - minX + MARGIN * 2);
  const dx = (W - (maxX - minX)) / 2 - minX;
  visible.forEach((id) => (pos[id].x += dx));
  const H = 46 + (usedRows.length - 1) * ROW + 86;

  let defs = "";
  const into = (id) => (seen.has(id) ? (story.passages[id].end ? R + 4 : R) + 6 : 0);

  // Trails: ones you haven't walked are dotted, ones you have are inked, the current reading is red
  // and drawn last, in order, so it inks itself in from the start.
  const lines = [];
  seen.forEach((from) => story.passages[from]?.choices.forEach((c) => {
    const key = `${from}>${c.to}`;
    if (!visible.has(c.to) || now.has(key)) return;
    lines.push(`<path class="trail ${walked.has(key) ? "walked" : "unwalked"}" d="${trailPath(pos[from], pos[c.to], W, hash(key), into(c.to))}"/>`);
  }));
  const stagger = Math.min(0.12, 1.5 / path.length);
  path.slice(1).forEach((id, i) => {
    const key = `${path[i]}>${id}`;
    if (pos[id] && pos[path[i]]) lines.push(`<path class="trail now" pathLength="1" style="animation-delay:${(i * stagger).toFixed(2)}s" d="${trailPath(pos[path[i]], pos[id], W, hash(key), into(id))}"/>`);
  });

  const clouds = art.has("clouds");
  const nodes = [...visible].map((id) => {
    const p = story.passages[id], { x, y } = pos[id];
    const key = id.replace(/[^\w-]/g, "_");

    if (!seen.has(id)) {
      // A cloud: a soft-edged puff cut from a different part of the cloud drawing each time.
      const r = rng(hash(story.id + id));
      const size = 24 + r() * 16;
      const count = 4 + Math.floor(r() * 3);
      const puffs = Array.from({ length: count }, (_, i) => {
        const a = (i / count) * Math.PI * 2 + r();
        const d = size * (0.35 + r() * 0.3);
        return `<ellipse cx="${f1(x + Math.cos(a) * d * 1.3)}" cy="${f1(y + Math.sin(a) * d * 0.7)}" rx="${f1(size * (0.55 + r() * 0.3))}" ry="${f1(size * (0.45 + r() * 0.25))}"/>`;
      }).join("");
      if (!clouds) return `<g class="node fog"><title>Not explored yet</title><g class="cloud-plain">${puffs}</g></g>`;
      const soft = 1 + Math.floor(r() * 3);
      const box = `x="${f1(x - size * 3)}" y="${f1(y - size * 3)}" width="${f1(size * 6)}" height="${f1(size * 6)}"`;
      defs += `<mask id="rm-c-${key}" maskUnits="userSpaceOnUse" ${box}><g fill="#fff" filter="url(#rm-soft${soft})">${puffs}</g></mask>`;
      const iw = size * (11 + r() * 7), ih = (iw * 2) / 3;
      const ix = x - iw * (0.15 + r() * 0.7), iy = y - ih * (0.15 + r() * 0.7);
      return `<g class="node fog"><title>Not explored yet</title><g mask="url(#rm-c-${key})">` +
        `<rect class="cloud-bg" ${box}/><image class="art-img cloud-img" href="art/clouds.webp" x="${f1(ix)}" y="${f1(iy)}" width="${f1(iw)}" height="${f1(ih)}" preserveAspectRatio="none"/></g></g>`;
    }

    const rad = p.end ? R + 4 : R;
    const cls = ["node", "seen", p.end ? "end" : "", id === current ? "current" : ""].join(" ").trim();
    const name = p.end ? `Ending: ${p.end}` : (p.caption || "A place you've been");
    defs += `<clipPath id="rm-v-${key}"><circle cx="${f1(x)}" cy="${y}" r="${rad}"/></clipPath>`;
    const img = p.art && art.has(p.art)
      ? `<image class="art-img" href="art/thumbs/${esc(p.art)}.webp" clip-path="url(#rm-v-${key})" x="${f1(x - rad * 1.6)}" y="${f1(y - rad * 1.07)}" width="${f1(rad * 3.2)}" height="${f1(rad * 2.13)}" preserveAspectRatio="xMidYMid slice"/>`
      : "";
    const vignette = `<circle class="vig-bg" cx="${f1(x)}" cy="${y}" r="${rad}"/>${img}` +
      `<circle class="ring" cx="${f1(x)}" cy="${y}" r="${rad}"/><circle class="ring-outer" cx="${f1(x)}" cy="${y}" r="${rad + 3.5}"/>`;
    let label;
    if (p.end) {
      const t = p.end.length > 26 ? p.end.slice(0, 25) + "…" : p.end;
      const bw = Math.max(80, t.length * 6.4 + 22);
      const by = y + rad + 4;
      label = `<path class="banner" d="M${f1(x - bw / 2)} ${f1(by)} h${f1(bw)} l-6 9 6 9 h${f1(-bw)} l6 -9z"/>` +
        `<text class="place-label end" x="${f1(x)}" y="${f1(by + 13)}" text-anchor="middle">${esc(t)}</text>`;
    } else {
      label = labelLines(p.caption || "").map((line, i) =>
        `<text class="place-label" x="${f1(x)}" y="${f1(y + rad + 17 + i * 14)}" text-anchor="middle">${esc(line)}</text>`).join("");
    }
    const attrs = p.end ? "" : ` tabindex="0" role="button" aria-label="${esc(`Go back to: ${name}`)}"`;
    return `<g class="${cls}" data-id="${esc(id)}"${attrs}><title>${esc(name)}</title>${vignette}${label}</g>`;
  });

  const filters = [1.5, 3, 4.5].map((s, i) =>
    `<filter id="rm-soft${i + 1}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${s}"/></filter>`).join("");
  return `<div class="route-map-wrap"><svg class="route-map" viewBox="0 0 ${f1(W)} ${H}" style="min-width:${Math.round(W * 0.62)}px" aria-label="Map of the story so far">` +
    `<defs>${filters}${defs}</defs>${lines.join("")}${nodes.join("")}</svg></div>`;
}

// Shortest way from the start to `target` using only steps the reader has taken.
function routeTo(story, trail, target) {
  const next = {};
  trail.forEach((t) => { const [a, b] = t.split(">"); (next[a] ||= []).push(b); });
  const prev = { [story.start]: null };
  const queue = [story.start];
  while (queue.length) {
    const id = queue.shift();
    if (id === target) break;
    for (const n of next[id] || []) if (!(n in prev)) { prev[n] = id; queue.push(n); }
  }
  if (!(target in prev)) return null;
  const path = [];
  for (let id = target; id; id = prev[id]) path.unshift(id);
  return path;
}

const api = { render, routeTo, layout };
if (typeof module !== "undefined") module.exports = api;
else root.RouteMap = api;
})(this);
