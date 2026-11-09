# Make Your Way

A small branching-story website. Pick a story, read a passage, choose what happens next, and keep going until you reach one of the endings.

**Live site:** https://ryangano.github.io/make-your-way/

## The stories

| Story | Genre | Reading time | Endings |
| --- | --- | --- | --- |
| The Keeper of Gull Rock | Coastal mystery | 15–30 min | 25 |
| The Map That Drew Itself | Fantasy journey | 15–42 min | 22 |
| The Long Quiet | Deep-sea science fiction | 15–43 min | 21 |

Reading times assume 230 words per minute and depend on which path you take.

## How it works

It's a static site with no build step: `index.html`, `style.css`, `app.js` and `story-parser.js`. GitHub Pages serves it as is.

- Progress and the endings you've found are saved in your browser's local storage, so you can close the tab and pick up where you left off.
- **Back a step** undoes your last choice, and **Start over** goes back to the beginning.
- **Map** draws your readings as a storybook trail. Each place you've been is a round picture cut from its illustration, joined by inked trails, with the current reading in red. Places one step beyond where you've been are hidden under clouds, each a different piece of one cloud drawing (`art/clouds.webp`). Tap a picture to go back there and choose differently. The map is drawn by `route-map.js`.

## The storyteller

An optional helper in `worker/` adds two things to the reader:

- **Write what you do.** Under the choices, the reader can type an action in their own words. The helper matches it to the closest choice and writes a sentence or two that leads into the next passage. If nothing fits, it answers in the story's voice and the reader stays where they are. It never invents new branches, so every route still comes from the written story. A line under the box tells readers that what they type is sent to an AI service; the helper doesn't store it.
- **Talk to people.** When someone is in the scene with you, a "Talk to …" box lets you ask them things. They answer in character and know only what you've read so far. Talking never changes what happens. Who can be talked to, and where, is set in `stories/characters.json`.

It's a Cloudflare Worker running Llama 3.1 8B on Workers AI, about 15 to 30 neurons a call, from the same daily quota as the drawings. The helper reads the stories from the site itself, so changing a story doesn't need a redeploy. When it can't be reached (not deployed, or out of quota), the boxes don't appear, or say so, and the site works with its buttons alone.

To try it locally alongside the site:

```bash
MYW_ENV_FILE=path/to/.env node tools/dev-worker.mjs   # http://localhost:8787 (add MYW_DEBUG=1 to log the model's raw replies)
```

The site uses the local helper automatically when it's opened from localhost. To deploy it (it needs a Cloudflare login that can edit Workers):

```bash
cd worker
npx wrangler deploy
```

It's deployed at https://make-your-way.make-your-way.workers.dev, which is the `AI_URL` in `app.js`. It runs on its own Cloudflare account, so it has its own 10,000 neurons a day, separate from the drawings.

## Writing a story

Each story is a plain text file in `stories/`, listed in `stories/index.json`.

```
title: The Keeper of Gull Rock
genre: Mystery · Coast
blurb: One or two sentences for the story card.
cover: dawn-tower
start: arrival

## arrival
[art: mailboat | Optional caption under the drawing.]
Paragraphs are separated by blank lines. *Asterisks* make italics.

> Text of the first choice -> cottage
> Text of the second choice -> tower

## ending-light
[art: dawn-tower]
[end: The Light Holds]
An ending has an [end: ...] line and no choices.
```

Passages can merge back together, but loops aren't allowed. Every story should have at least 20 endings, spread along the whole journey, so a short read can end early and a long one can go deep.

## Checking stories

```bash
node tools/check-stories.js
```

The script reports broken links, unreachable passages, loops, dead ends, and illustrations with no prompt in `art/prompts.json`. It also prints the shortest and longest reading time for each story, and fails if either falls outside 15–60 minutes.

## Drawings

The illustrations are black-ink line art, generated with Cloudflare Workers AI (FLUX schnell). Each scene has a prompt in `art/prompts.json`, which also holds the shared line-art style and the order to draw scenes in. Generated images go in `art/<name>.webp`, with a small copy in `art/thumbs/` for the map, and `art/index.json` lists the scenes that have one. A scene with no image yet is simply shown without a picture.

The free daily quota is 10,000 neurons, which works out to roughly 80 images a day (about 120 neurons each). The quota is shared with anything else on the same Cloudflare account. So the art is filled in over a few days:

```bash
npm install
MYW_ENV_FILE=path/to/.env node tools/gen-art.cjs --next 3   # draw the next 3 scenes in priority order
node tools/gen-art.cjs --list                                        # see which scenes are still missing
node tools/gen-art.cjs --force crow                                  # redraw one scene
node tools/gen-art.cjs --thumbs                                      # rebuild the map's small copies
```

The script needs `CF_ACCOUNT_ID` and `CF_API_TOKEN`. It reads them from the environment, a gitignored `.env` in this repo, or the file named by `MYW_ENV_FILE`. When the quota runs out it stops and says so; run it again after the reset. Look over new images before committing them: the model sometimes adds made-up lettering, stray colour, or the wrong subject. Rewrite the scene description and redraw it. Rejected drafts can be parked in the gitignored `art/rejects/` folder; the site only shows images listed in `art/index.json`, which the script rebuilds from the files in `art/`.

The images are drawn black on white. The site multiplies them onto the paper colour in light mode and inverts them in dark mode, so they sit on the page in both themes.

## Running locally

The site loads stories with `fetch`, so you need a local server rather than opening the file directly:

```bash
python -m http.server 8123
```

Then open http://localhost:8123.
