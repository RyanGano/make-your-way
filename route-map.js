// The route map: the story's passages laid out as a map that inks itself in as you read.
// Places you've been are drawn in ink, places one step beyond them are faint outlines,
// and the rest of the map stays blank until you get near it.
(function (root) {

const W = 360;
const ROW = 54;
const TOP = 26;

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
  rows.forEach((row, d) => row.forEach((id) => (at[id] = { x: 20 + pos[id] * (W - 40), y: TOP + d * ROW })));
  return { at, height: TOP * 2 + (rows.length - 1) * ROW };
}

// trail: "from>to" steps taken on any reading; path: the current reading.
function render(story, { trail, path }) {
  const { at, height } = layout(story);
  const walked = new Set(trail);
  const seen = new Set([story.start, ...trail.flatMap((t) => t.split(">"))]);
  const visible = new Set(seen);
  seen.forEach((id) => story.passages[id]?.choices.forEach((c) => visible.add(c.to)));
  const now = new Set(path.slice(1).map((id, i) => `${path[i]}>${id}`));
  const current = path.at(-1);

  const curve = (a, b) => {
    const p = at[a], q = at[b], m = (p.y + q.y) / 2;
    const span = Math.round((q.y - p.y) / ROW);
    if (span <= 1) return `M${p.x.toFixed(1)} ${p.y} C${p.x.toFixed(1)} ${m} ${q.x.toFixed(1)} ${m} ${q.x.toFixed(1)} ${q.y}`;
    // Steps that skip rows bow out to the side, so they don't run through the places between.
    const side = q.x > p.x ? 1 : q.x < p.x ? -1 : (p.x > W / 2 ? -1 : 1);
    const off = side * Math.min(70, 22 * span);
    return `M${p.x.toFixed(1)} ${p.y} C${(p.x + off).toFixed(1)} ${p.y + ROW} ${(q.x + off).toFixed(1)} ${q.y - ROW} ${q.x.toFixed(1)} ${q.y}`;
  };

  const edges = [];
  const nowEdges = [];
  seen.forEach((from) => story.passages[from]?.choices.forEach((c) => {
    if (!visible.has(c.to)) return;
    const key = `${from}>${c.to}`;
    if (now.has(key)) nowEdges.push(key);
    else edges.push(`<path class="${walked.has(key) ? "walked" : "unwalked"}" d="${curve(from, c.to)}"/>`);
  }));
  // The current reading is drawn last, in order, so it inks in from the start.
  const stagger = Math.min(0.12, 1.5 / path.length);
  path.slice(1).forEach((id, i) => {
    const key = `${path[i]}>${id}`;
    if (nowEdges.includes(key)) edges.push(`<path class="now" pathLength="1" style="animation-delay:${(i * stagger).toFixed(2)}s" d="${curve(path[i], id)}"/>`);
  });

  const label = (p) => p.end ? `Ending: ${p.end}` : (p.caption || "A place you've been");
  const nodes = [...visible].map((id) => {
    const p = story.passages[id], { x, y } = at[id];
    const been = seen.has(id);
    const cls = [been ? "seen" : "fog", p.end ? "end" : "", id === current ? "current" : ""].join(" ").trim();
    const shape = p.end
      ? `<rect x="${(x - 6).toFixed(1)}" y="${y - 6}" width="12" height="12" transform="rotate(45 ${x.toFixed(1)} ${y})"/>`
      : `<circle cx="${x.toFixed(1)}" cy="${y}" r="${id === current ? 7 : been ? 5 : 4}"/>`;
    const title = been ? label(p) : "Not explored yet";
    return `<g class="node ${cls}" data-id="${id}" ${been && !p.end ? 'tabindex="0" role="button"' : ""}><title>${title.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`)}</title>${shape}</g>`;
  });

  return `<svg class="route-map" viewBox="0 0 ${W} ${height}" role="img" aria-label="Map of the story so far">${edges.join("")}${nodes.join("")}</svg>`;
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
