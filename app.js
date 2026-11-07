// Make Your Way: a small branching-story reader.
// Stories live in stories/<id>.txt (format described in README.md); art lives in art/<name>.svg.

const WORDS_PER_MINUTE = 230;
const app = document.getElementById("app");
const headerActions = document.getElementById("header-actions");

const storyCache = new Map();
const artCache = new Map();

// ---------- storage (best effort: the site works without it) ----------

function loadState(storyId) {
  try {
    const raw = localStorage.getItem("myw:" + storyId);
    if (raw) return JSON.parse(raw);
  } catch (_) { /* private mode or blocked storage */ }
  return { path: [], endings: [] };
}

function saveState(storyId, state) {
  try { localStorage.setItem("myw:" + storyId, JSON.stringify(state)); } catch (_) { /* ignore */ }
}

// ---------- loading ----------

async function fetchText(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  return res.text();
}

async function loadLibrary() {
  return JSON.parse(await fetchText("stories/index.json"));
}

async function loadStory(id) {
  if (!storyCache.has(id)) {
    storyCache.set(id, fetchText(`stories/${id}.txt`).then((t) => StoryParser.parseStory(id, t)));
  }
  return storyCache.get(id);
}

async function loadArt(name) {
  if (!artCache.has(name)) {
    artCache.set(name, fetchText(`art/${name}.svg`).catch(() => ""));
  }
  return artCache.get(name);
}

const minutes = (words) => Math.max(1, Math.round(words / WORDS_PER_MINUTE));

// ---------- rendering helpers ----------

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Allows *italic* in story text.
const inline = (s) => esc(s).replace(/\*(.+?)\*/g, "<em>$1</em>");

function setHeader(html) { headerActions.innerHTML = html; }

function focusMain() {
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  app.focus({ preventScroll: true });
}

// ---------- views ----------

async function renderHome() {
  setHeader("");
  document.title = "Make Your Way";
  const library = await loadLibrary();
  const stories = await Promise.all(library.map((s) => loadStory(s.id)));
  const covers = await Promise.all(stories.map((s) => loadArt(s.meta.cover)));

  app.innerHTML = `
    <section class="hero">
      <h1>Make Your Way</h1>
      <p>Pick a story. Read a while. When the road forks, you decide which way it goes, and the story follows you there.</p>
    </section>
    <section class="shelf" aria-label="Stories">
      ${stories.map((s, i) => {
        const state = loadState(s.id);
        const lo = minutes(s.range.minWords), hi = minutes(s.range.maxWords);
        const inProgress = state.path.length > 1 && !s.passages[state.path.at(-1)]?.end;
        return `
          <a class="story-card" href="#/read/${s.id}">
            <div class="cover">${covers[i]}</div>
            <div class="body">
              <p class="genre">${esc(s.meta.genre || "")}</p>
              <h2>${esc(s.meta.title)}</h2>
              <p class="blurb">${esc(s.meta.blurb || "")}</p>
              <div class="meta">
                <span>${lo}–${hi} min</span>
                <span>${s.endings.length} endings</span>
                ${state.endings.length ? `<span>${state.endings.length} found</span>` : ""}
                ${inProgress ? `<span class="resume">Continue reading →</span>` : ""}
              </div>
            </div>
          </a>`;
      }).join("")}
    </section>`;
  focusMain();
}

async function renderPassage(storyId, action) {
  const story = await loadStory(storyId);
  const state = loadState(storyId);

  if (action === "restart" || !state.path.length || !story.passages[state.path.at(-1)]) {
    state.path = [story.start];
  }
  saveState(storyId, state);

  const passage = story.passages[state.path.at(-1)];
  const wordsSoFar = state.path.reduce((n, id) => n + (story.passages[id]?.words || 0), 0);
  const art = passage.art ? await loadArt(passage.art) : "";
  document.title = `${story.meta.title} · Make Your Way`;

  if (passage.end && !state.endings.includes(passage.id)) {
    state.endings.push(passage.id);
    saveState(storyId, state);
  }

  setHeader(`
    <button class="btn" id="back" ${state.path.length < 2 ? "disabled" : ""}>← Back a step</button>
    <button class="btn" id="restart">Start over</button>
    <a class="btn" href="#/">All stories</a>`);

  const choicesHtml = passage.choices.length
    ? `<section class="choices" aria-labelledby="choose">
         <h2 id="choose">What do you do?</h2>
         ${passage.choices.map((c, i) => `
           <button class="choice" data-i="${i}"><span class="arrow" aria-hidden="true">→</span><span>${inline(c.text)}</span></button>`).join("")}
       </section>`
    : "";

  const endingHtml = passage.end
    ? `<section class="ending">
         <p class="label">The End</p>
         <h2>${esc(passage.end)}</h2>
         <p>You've found ${state.endings.length} of ${story.endings.length} endings. Other choices lead to other places.</p>
         <div class="actions">
           <button class="btn primary" id="again">Read it again</button>
           <a class="btn" href="#/">Pick another story</a>
         </div>
         <ul class="endings-list" aria-label="Endings">
           ${story.endings.map((e) => `<li class="${state.endings.includes(e.id) ? "found" : ""}">${state.endings.includes(e.id) ? esc(e.end) : "???"}</li>`).join("")}
         </ul>
       </section>`
    : "";

  app.innerHTML = `
    <article class="reader">
      <p class="story-title">${esc(story.meta.title)}</p>
      <p class="progress-line">Part ${state.path.length} · about ${minutes(wordsSoFar)} min read so far</p>
      ${art ? `<figure class="art">${art}${passage.caption ? `<figcaption>${esc(passage.caption)}</figcaption>` : ""}</figure>` : ""}
      <div class="passage">${passage.paragraphs.map((p) => `<p>${inline(p)}</p>`).join("")}</div>
      ${choicesHtml}
      ${endingHtml}
    </article>`;

  app.querySelectorAll(".choice").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.path.push(passage.choices[+btn.dataset.i].to);
      saveState(storyId, state);
      renderPassage(storyId);
    });
  });
  document.getElementById("back").onclick = () => {
    if (state.path.length > 1) { state.path.pop(); saveState(storyId, state); renderPassage(storyId); }
  };
  const restart = () => renderPassage(storyId, "restart");
  document.getElementById("restart").onclick = restart;
  const again = document.getElementById("again");
  if (again) again.onclick = restart;
  focusMain();
}

// ---------- routing ----------

async function route() {
  const [, view, id] = location.hash.split("/");
  try {
    if (view === "read" && id) await renderPassage(decodeURIComponent(id));
    else await renderHome();
  } catch (err) {
    console.error(err);
    app.innerHTML = `<div class="error"><p>Something went wrong loading this page.</p><p><a href="#/">Back to all stories</a></p></div>`;
  }
}

window.addEventListener("hashchange", route);
route();
