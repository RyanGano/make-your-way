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

The illustrations are black-ink line art, generated with Cloudflare Workers AI (FLUX schnell), the same service the ai-mysteries project uses for its covers. Each scene has a prompt in `art/prompts.json`, which also holds the shared line-art style and the order to draw scenes in. Generated images go in `art/<name>.webp`, and `art/index.json` lists the scenes that have one. A scene with no image yet is simply shown without a picture.

The free daily quota covers only a few images, so the art is filled in a few at a time:

```bash
npm install
MYW_ENV_FILE=../ai-mysteries/.env node tools/gen-art.cjs --next 3   # draw the next 3 scenes in priority order
node tools/gen-art.cjs --list                                        # see which scenes are still missing
node tools/gen-art.cjs --force crow                                  # redraw one scene
```

The script needs `CF_ACCOUNT_ID` and `CF_API_TOKEN`. It reads them from the environment, a gitignored `.env` in this repo, or the file named by `MYW_ENV_FILE`. When the quota runs out it stops and says so; run it again after the reset. Look over new images before committing them: the model sometimes adds made-up lettering, and a scene description that avoids signs and labels usually fixes it.

The images are drawn black on white. The site multiplies them onto the paper colour in light mode and inverts them in dark mode, so they sit on the page in both themes.

## Running locally

The site loads stories with `fetch`, so you need a local server rather than opening the file directly:

```bash
python -m http.server 8123
```

Then open http://localhost:8123.
