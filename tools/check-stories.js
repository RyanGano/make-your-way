// Checks every story for broken links, unreachable passages, loops, dead ends,
// missing art, and reports the shortest and longest reading time.
// Usage: node tools/check-stories.js
const fs = require("fs");
const path = require("path");
const { parseStory } = require("../story-parser.js");

const root = path.join(__dirname, "..");
const WPM = 230;
const MIN_MINUTES = 15;
const MAX_MINUTES = 60;
const library = JSON.parse(fs.readFileSync(path.join(root, "stories/index.json"), "utf8"));
let problems = 0;

const fail = (story, msg) => { problems++; console.log(`  ✗ ${story}: ${msg}`); };
const artExists = (name) => fs.existsSync(path.join(root, "art", name + ".svg"));

for (const { id } of library) {
  const story = parseStory(id, fs.readFileSync(path.join(root, "stories", id + ".txt"), "utf8"));
  const passages = story.passages;
  console.log(`\n${story.meta.title} (${id})`);

  if (!passages[story.start]) fail(id, `start passage "${story.start}" missing`);
  if (!artExists(story.meta.cover)) fail(id, `cover art "${story.meta.cover}" missing`);

  for (const p of Object.values(passages)) {
    if (!p.end && !p.choices.length) fail(id, `"${p.id}" has no choices and is not an ending`);
    if (p.end && p.choices.length) fail(id, `"${p.id}" is an ending but has choices`);
    if (p.art && !artExists(p.art)) fail(id, `"${p.id}" uses missing art "${p.art}"`);
    for (const c of p.choices) if (!passages[c.to]) fail(id, `"${p.id}" links to missing "${c.to}"`);
  }

  // reachability + cycle detection
  const seen = new Set(), stack = new Set();
  const visit = (pid, trail) => {
    if (stack.has(pid)) { fail(id, `loop: ${[...trail, pid].join(" → ")}`); return; }
    if (seen.has(pid) || !passages[pid]) return;
    seen.add(pid); stack.add(pid);
    for (const c of passages[pid].choices) visit(c.to, [...trail, pid]);
    stack.delete(pid);
  };
  visit(story.start, []);
  for (const pid of story.order) if (!seen.has(pid)) fail(id, `"${pid}" is unreachable`);

  const lo = story.range.minWords / WPM, hi = story.range.maxWords / WPM;
  const total = Object.values(passages).reduce((n, p) => n + p.words, 0);
  const arts = new Set(Object.values(passages).map((p) => p.art).filter(Boolean));
  console.log(`  ${story.order.length} passages, ${story.endings.length} endings, ${arts.size} illustrations, ${total} words total`);
  console.log(`  shortest path ${story.range.minWords} words (${lo.toFixed(1)} min), longest ${story.range.maxWords} words (${hi.toFixed(1)} min)`);
  if (lo < MIN_MINUTES) fail(id, `shortest path is under ${MIN_MINUTES} minutes`);
  if (hi > MAX_MINUTES) fail(id, `longest path is over ${MAX_MINUTES} minutes`);

  // shortest path to each ending, so thin branches are easy to spot
  const toEnding = {};
  const walk = (pid, words, seenHere) => {
    const p = passages[pid];
    if (!p || seenHere.has(pid)) return;
    const w = words + p.words;
    if (p.end) { toEnding[pid] = Math.min(toEnding[pid] ?? Infinity, w); return; }
    for (const c of p.choices) walk(c.to, w, new Set([...seenHere, pid]));
  };
  walk(story.start, 0, new Set());
  for (const e of story.endings) {
    const w = toEnding[e.id];
    console.log(`    ending "${e.end}": shortest route ${w ?? "-"} words (${w ? (w / WPM).toFixed(1) : "-"} min)`);
  }
}

console.log(problems ? `\n${problems} problem(s) found.` : "\nAll stories check out.");
process.exit(problems ? 1 : 0);
