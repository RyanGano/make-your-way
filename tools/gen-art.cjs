// Generate the story illustrations via Cloudflare Workers AI (free daily quota), the same
// service ai-mysteries uses for its covers (see its scripts/gen-cover.cjs).
//
//   node tools/gen-art.cjs <name> [<name> ...]     # generate these scenes
//   node tools/gen-art.cjs --next 3                 # the next 3 scenes without an image, in priority order
//   node tools/gen-art.cjs --list                   # show which scenes have images
//   options: --model flux|sdxl   --force (regenerate even if the image exists)
//
// Scene prompts live in art/prompts.json: a shared "style" block plus one description per
// scene name (the names used by [art: ...] lines in the stories). "priority" lists the scenes
// to draw first: covers, then one key scene per story, round-robin.
//
// Each image is cropped to 3:2 and written as art/<name>.webp; art/index.json lists every
// scene that has an image, and the site only shows images that are listed there.
//
// Credentials: CF_ACCOUNT_ID and CF_API_TOKEN from the environment, a gitignored .env in this
// repo, or the .env file named by MYW_ENV_FILE (e.g. MYW_ENV_FILE=../ai-mysteries/.env).
//
// When the daily quota runs out the script stops and says so; run it again after the reset.

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const ART = path.join(ROOT, "art");
const W = 1200;
const H = 800;

const MODELS = {
  flux: "@cf/black-forest-labs/flux-1-schnell",
  sdxl: "@cf/stabilityai/stable-diffusion-xl-base-1.0",
};

function loadDotEnv(file) {
  if (!file || !fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

function parseArgs(argv) {
  const a = { model: "flux", names: [], next: 0, list: false, force: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--model") a.model = argv[++i];
    else if (argv[i] === "--next") a.next = Number(argv[++i]);
    else if (argv[i] === "--list") a.list = true;
    else if (argv[i] === "--force") a.force = true;
    else a.names.push(argv[i]);
  }
  return a;
}

const readJson = (p, fallback) => (fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : fallback);
const hasImage = (name) => fs.existsSync(path.join(ART, name + ".webp"));

function writeIndex() {
  const names = fs.readdirSync(ART).filter((f) => f.endsWith(".webp")).map((f) => f.slice(0, -5)).sort();
  fs.writeFileSync(path.join(ART, "index.json"), JSON.stringify(names, null, 2) + "\n");
  return names;
}

class QuotaError extends Error {}

async function callWorkersAi(model, prompt) {
  const acct = process.env.CF_ACCOUNT_ID;
  const token = process.env.CF_API_TOKEN;
  if (!acct || !token) throw new Error("Set CF_ACCOUNT_ID and CF_API_TOKEN (env, .env, or MYW_ENV_FILE).");
  const url = `https://api.cloudflare.com/client/v4/accounts/${acct}/ai/run/${model}`;
  // FLUX schnell rejects width/height/seed and always returns a square; SDXL takes a size.
  const body = model === MODELS.flux ? { prompt, steps: 8 } : { prompt, width: 1024, height: 680, num_steps: 20 };
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const ct = res.headers.get("content-type") || "";
  if (!res.ok) {
    const text = (await res.text()).slice(0, 400);
    if (res.status === 429 || /quota|limit|neurons|4006/i.test(text)) throw new QuotaError(text);
    throw new Error(`Workers AI ${res.status}: ${text}`);
  }
  if (ct.includes("application/json")) {
    const j = await res.json();
    if (!j.success) throw new Error(`Workers AI error: ${JSON.stringify(j.errors || j)}`);
    return Buffer.from(j.result.image, "base64");
  }
  return Buffer.from(await res.arrayBuffer());
}

async function generate(name, prompts, model) {
  const scene = prompts.scenes[name];
  if (!scene) throw new Error(`No prompt for "${name}" in art/prompts.json`);
  const prompt = `${prompts.style} Scene: ${scene}`;
  const raw = await callWorkersAi(MODELS[model], prompt);
  const sharp = require("sharp");
  const out = path.join(ART, name + ".webp");
  await sharp(raw).resize(W, H, { fit: "cover", position: "centre" }).webp({ quality: 82 }).toFile(out);
  console.log(`  ✓ ${name}  (${(fs.statSync(out).size / 1024).toFixed(0)} KB)`);
}

async function main() {
  loadDotEnv(path.join(ROOT, ".env"));
  loadDotEnv(process.env.MYW_ENV_FILE && path.resolve(ROOT, process.env.MYW_ENV_FILE));
  const args = parseArgs(process.argv.slice(2));
  if (!MODELS[args.model]) throw new Error(`Unknown model "${args.model}" (use flux or sdxl)`);
  const prompts = readJson(path.join(ART, "prompts.json"));

  if (args.list) {
    const all = Object.keys(prompts.scenes);
    const done = all.filter(hasImage);
    console.log(`${done.length} of ${all.length} scenes have images.`);
    console.log("Missing:", all.filter((n) => !hasImage(n)).join(", ") || "none");
    return;
  }

  let queue = args.names;
  if (args.next) {
    const order = [...prompts.priority, ...Object.keys(prompts.scenes)];
    queue = [...new Set(order)].filter((n) => !hasImage(n)).slice(0, args.next);
  }
  if (!queue.length) {
    console.log("Nothing to generate. Usage: node tools/gen-art.cjs <name...> | --next N | --list");
    return;
  }

  console.log(`Model: ${args.model}. Generating ${queue.length}: ${queue.join(", ")}`);
  let made = 0;
  for (const name of queue) {
    if (hasImage(name) && !args.force) { console.log(`  - ${name} already exists (use --force to redo)`); continue; }
    try {
      await generate(name, prompts, args.model);
      made++;
    } catch (e) {
      if (e instanceof QuotaError) {
        console.log(`\nStopped: the Workers AI daily quota looks used up (${e.message.slice(0, 160)}).`);
        console.log("Run again after the quota resets.");
        break;
      }
      throw e;
    }
  }
  const all = writeIndex();
  console.log(`\nMade ${made}. ${all.length} images in art/index.json.`);
}

main().catch((e) => {
  console.error(String(e.message || e));
  process.exit(1);
});
