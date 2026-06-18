import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const configPaths = [
  path.join(root, "capacitor.config.json"),
  path.join(root, "ios", "App", "App", "capacitor.config.json"),
];

const forbiddenText = [
  "run.myrunningmate.com/dashboard",
  "localhost",
  "127.0.0.1",
  "http://",
];

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return { raw, data: JSON.parse(raw) };
}

let failed = false;

for (const filePath of configPaths) {
  const label = path.relative(root, filePath);

  if (!fs.existsSync(filePath)) {
    console.error(`[ios-config] missing ${label}`);
    failed = true;
    continue;
  }

  const { raw, data } = readJson(filePath);

  if (data.server?.url) {
    console.error(`[ios-config] ${label} must not define server.url: ${data.server.url}`);
    failed = true;
  }

  for (const token of forbiddenText) {
    if (raw.includes(token)) {
      console.error(`[ios-config] ${label} contains forbidden value: ${token}`);
      failed = true;
    }
  }

  if (data.webDir !== "bundle/www") {
    console.error(`[ios-config] ${label} must use webDir "bundle/www"`);
    failed = true;
  }
}

if (failed) {
  process.exit(1);
}

console.log("[ios-config] OK: iOS app will load the bundled webDir, not a remote server.url.");
