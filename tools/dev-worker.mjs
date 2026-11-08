// Runs the Worker locally on http://localhost:8787 for testing, reading stories from the local
// site (http://localhost:8123) and calling Workers AI over REST with CF_ACCOUNT_ID and
// CF_API_TOKEN from the environment, a .env in this repo, or the file named by MYW_ENV_FILE.
//   MYW_ENV_FILE=../ai-mysteries/.env node tools/dev-worker.mjs
import http from "node:http";
import fs from "node:fs";
import worker from "../worker/src/index.mjs";

for (const file of [process.env.MYW_ENV_FILE, ".env"].filter(Boolean)) {
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const env = {
  SITE: process.env.SITE || "http://localhost:8123/",
  ALLOWED_ORIGINS: "http://localhost:8123,http://127.0.0.1:8123",
  CF_ACCOUNT_ID: process.env.CF_ACCOUNT_ID,
  CF_API_TOKEN: process.env.CF_API_TOKEN,
};
if (!env.CF_ACCOUNT_ID || !env.CF_API_TOKEN) console.warn("No Cloudflare credentials found; /act and /talk will fail.");

http.createServer(async (req, res) => {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const request = new Request(`http://localhost:8787${req.url}`, {
    method: req.method,
    headers: req.headers,
    body: ["GET", "HEAD", "OPTIONS"].includes(req.method) ? undefined : Buffer.concat(chunks),
  });
  const response = await worker.fetch(request, env);
  res.writeHead(response.status, Object.fromEntries(response.headers));
  res.end(Buffer.from(await response.arrayBuffer()));
  console.log(req.method, req.url, response.status);
}).listen(8787, () => console.log("Worker running on http://localhost:8787"));
