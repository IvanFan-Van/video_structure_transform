import fs from "fs";
import path from "path";
import os from "os";
import { spawnSync } from "child_process";

const rootDir = path.resolve(__dirname, "..");
const jsonlPath = path.join(rootDir, "render_commands.jsonl");
const lines = fs.readFileSync(jsonlPath, "utf-8").trim().split("\n");

const isWin = process.platform === "win32";
const remotionBin = isWin
  ? path.join(rootDir, "node_modules", ".bin", "remotion.cmd")
  : path.join(rootDir, "node_modules", ".bin", "remotion");

const failed: string[] = [];

for (let i = 0; i < lines.length; i++) {
  const entry = JSON.parse(lines[i]);
  const propsJson = entry.props;
  const outMatch = entry.command.match(/out\/([^\s"']+)/);
  const outFile = outMatch ? outMatch[1] : `effect-${i}.mp4`;

  console.log(`[${i + 1}/${lines.length}] ${outFile}`);

  const tmpFile = path.join(os.tmpdir(), `rem-props-${i}.json`);
  fs.writeFileSync(tmpFile, propsJson);

  const args = ["render", "src/index.ts", "render", `out/${outFile}`, `--props=${tmpFile}`];
  const result = spawnSync(remotionBin, args, {
    stdio: "inherit",
    cwd: rootDir,
    shell: false,
  });

  try {
    fs.unlinkSync(tmpFile);
  } catch {}

  if (result.status !== 0) {
    failed.push(outFile);
  }
}

if (failed.length > 0) {
  console.error(`\n${failed.length}/${lines.length} failed:\n  ${failed.join("\n  ")}`);
  process.exit(1);
}
console.log(`\nAll ${lines.length} rendered successfully.`);
