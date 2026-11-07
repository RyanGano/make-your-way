// Parses the plain-text story format (see README.md). Shared by the site and tools/check-stories.js.
(function (root) {

function parseStory(id, text) {
  const story = { id, meta: {}, passages: {}, order: [] };
  let current = null;
  let para = [];

  const flush = () => {
    if (current && para.length) current.paragraphs.push(para.join(" "));
    para = [];
  };

  for (const rawLine of text.replace(/\r/g, "").split("\n")) {
    const line = rawLine.trim();
    const header = line.match(/^##\s+(\S+)/);
    if (header) {
      flush();
      current = { id: header[1], paragraphs: [], choices: [], art: null, caption: "", end: null };
      story.passages[current.id] = current;
      story.order.push(current.id);
      continue;
    }
    if (!current) {
      const m = line.match(/^(\w+):\s*(.*)$/);
      if (m) story.meta[m[1]] = m[2];
      continue;
    }
    if (line === "") { flush(); continue; }
    let m;
    if ((m = line.match(/^\[art:\s*([\w-]+)\s*(?:\|\s*(.*))?\]$/))) {
      current.art = m[1];
      current.caption = m[2] || "";
    } else if ((m = line.match(/^\[end:\s*(.*)\]$/))) {
      current.end = m[1];
    } else if ((m = line.match(/^>\s*(.*?)\s*->\s*(\S+)$/))) {
      flush();
      current.choices.push({ text: m[1], to: m[2] });
    } else {
      para.push(line);
    }
  }
  flush();

  for (const p of Object.values(story.passages)) {
    p.words = p.paragraphs.join(" ").split(/\s+/).filter(Boolean).length;
  }
  story.start = story.meta.start || story.order[0];
  story.endings = Object.values(story.passages).filter((p) => p.end);
  story.range = readingRange(story);
  return story;
}

// Shortest and longest number of words from the start to any ending.
function readingRange(story) {
  const memo = new Map();
  const visiting = new Set();
  const walk = (id) => {
    if (memo.has(id)) return memo.get(id);
    const p = story.passages[id];
    if (!p || visiting.has(id)) return null;
    visiting.add(id);
    let min = Infinity, max = 0;
    for (const c of p.choices) {
      const r = walk(c.to);
      if (!r) continue;
      min = Math.min(min, r.min);
      max = Math.max(max, r.max);
    }
    visiting.delete(id);
    const result = p.choices.length ? { min: p.words + min, max: p.words + max } : { min: p.words, max: p.words };
    memo.set(id, result);
    return result;
  };
  const r = walk(story.start) || { min: 0, max: 0 };
  return { minWords: r.min, maxWords: r.max };
}

  const api = { parseStory, readingRange };
  if (typeof module !== "undefined") module.exports = api;
  else root.StoryParser = api;
})(this);
