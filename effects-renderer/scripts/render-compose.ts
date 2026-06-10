// scripts/render-compose.ts
// Render a full video from a VideoProject JSON file.
//
// Usage:
//   npx tsx scripts/render-compose.ts --project <json-file-path>
//   npx tsx scripts/render-compose.ts --project compose-example.json --out out/my-video.mp4
//   npx tsx scripts/render-compose.ts --project compose-example.json --bgcolor "#ffffff"

import { parseArgs } from "node:util";
import path from "node:path";
import fs from "node:fs";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

async function main() {
  const { values } = parseArgs({
    options: {
      project: { type: "string", short: "p" },
      out: { type: "string", short: "o" },
      bgcolor: { type: "string" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: false,
  });

  if (values.help || !values.project) {
    console.log(`
Usage: npx tsx scripts/render-compose.ts --project <json-file> [options]

Required:
  --project, -p   Path to VideoProject JSON file

Options:
  --out, -o       Output MP4 path (default: out/<project-name>.mp4)
  --bgcolor       Override global background color (e.g. "#000000")

Examples:
  npx tsx scripts/render-compose.ts -p compose-example.json
  npx tsx scripts/render-compose.ts -p compose-example.json -o out/my-video.mp4
`);
    process.exit(values.help ? 0 : 1);
  }

  // Read and parse project JSON
  const projectPath = path.resolve(values.project);
  if (!fs.existsSync(projectPath)) {
    console.error(`Error: Project file not found: ${projectPath}`);
    process.exit(1);
  }

  const projectRaw = fs.readFileSync(projectPath, "utf-8");
  let project: any;
  try {
    project = JSON.parse(projectRaw);
  } catch {
    console.error("Error: Project file is not valid JSON");
    process.exit(1);
  }

  // Validate version
  if (!project.version || !project.scenes) {
    console.error(
      "Error: Invalid project JSON — must contain 'version' and 'scenes'",
    );
    process.exit(1);
  }

  const comp = project.composition ?? {
    width: 1920,
    height: 1080,
    fps: 30,
  };

  // Compute total duration by accumulating scenes + transitions
  let totalDuration = 0;
  for (let i = 0; i < project.scenes.length; i++) {
    const scene = project.scenes[i];
    totalDuration += scene.durationInFrames ?? 90;

    if (i < project.scenes.length - 1) {
      const trans = scene.transitionOut ?? { type: "cut" };
      if (trans.type === "effect") {
        totalDuration += trans.durationInFrames ?? 30;
      }
    }
  }

  // Apply bgcolor override
  if (values.bgcolor) {
    project.composition = project.composition ?? {};
    project.composition.backgroundColor = values.bgcolor;
  }

  const inputProps = { project };

  const projectName = path.basename(projectPath, path.extname(projectPath));
  const outputPath = values.out
    ? path.resolve(values.out)
    : path.resolve(process.cwd(), "out", `${projectName}.mp4`);

  const outDir = path.dirname(outputPath);
  fs.mkdirSync(outDir, { recursive: true });

  console.log(`Project: ${projectPath}`);
  console.log(`Scenes: ${project.scenes.length}`);
  console.log(`Total duration: ${totalDuration}f @ ${comp.fps}fps`);
  console.log(`Resolution: ${comp.width}x${comp.height}`);
  console.log(`Output: ${outputPath}`);
  console.log(`Bundling...`);

  const entryPoint = path.resolve(process.cwd(), "src/index.ts");
  const bundleLocation = await bundle({ entryPoint });

  console.log(`Selecting composition: compose`);
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: "compose",
    inputProps,
  });

  const overrides = {
    durationInFrames: totalDuration,
    fps: comp.fps ?? composition.fps,
    width: comp.width ?? composition.width,
    height: comp.height ?? composition.height,
  };

  console.log(
    `Render config: ${overrides.durationInFrames}f @ ${overrides.fps}fps | ${overrides.width}x${overrides.height}`,
  );
  console.log(`Rendering...`);

  const startTime = Date.now();

  await renderMedia({
    composition: { ...composition, ...overrides },
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: outputPath,
    inputProps,
    chromiumOptions: {
      gl: "angle",
    },
    onProgress: ({ progress }) => {
      process.stdout.write(`\r  Progress: ${Math.round(progress * 100)}%`);
    },
  });

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\nDone in ${elapsed}s`);
  console.log(`Output: ${outputPath}`);
}

main().catch((err) => {
  console.error("\nRender failed:", err);
  process.exit(1);
});
