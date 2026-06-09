// scripts/render.ts
// Dynamic effect renderer — programmatic API using @remotion/renderer
//
// Usage:
//   npx tsx scripts/render.ts --effect blur-reveal --props '{"text":"Hello"}'
//   npx tsx scripts/render.ts --effect blur-reveal --props '{"text":"Hello"}' --out out/my-video.mp4
//   npx tsx scripts/render.ts --effect blur-reveal --props '{"text":"Hello"}' --duration 60 --fps 30 --width 1920 --height 1080

import { parseArgs } from "node:util";
import path from "node:path";
import fs from "node:fs";
import { pathToFileURL } from "node:url";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

function printUsage() {
	console.log(`
Usage: npx tsx scripts/render.ts --effect <id> [options]

Required:
  --effect, -e     Effect ID from the registry (e.g. blur-reveal, typewriter)

Options:
  --props          JSON string of effect props (default: "{}")
  --out, -o        Output MP4 path (default: out/<effect>.mp4)
  --duration       Duration in frames (default: effect default)
  --fps            Frames per second (default: effect default)
  --width          Width in pixels (default: effect default)
  --height         Height in pixels (default: effect default)
  --list           List all available effects

Examples:
  npx tsx scripts/render.ts --effect blur-reveal --props '{"text":"Hello World"}'
  npx tsx scripts/render.ts -e typewriter --props '{"text":"Hello"}' -o out/typewriter.mp4
  npx tsx scripts/render.ts --list
`);
}

async function listEffects() {
	// Load the registry to list effects
	const EFFECT_REGISTRY = await import(
		pathToFileURL(path.resolve(process.cwd(), "src/effects/index.ts")).href
	).then((m) => m.EFFECT_REGISTRY);

	console.log("\nAvailable effects:");
	for (const [id, meta] of Object.entries(EFFECT_REGISTRY) as [string, any][]) {
		console.log(`  ${id.padEnd(30)} ${meta.defaultDurationInFrames}f @ ${meta.defaultFps}fps | ${meta.defaultWidth}x${meta.defaultHeight}`);
	}
}

async function main() {
	const { values } = parseArgs({
		options: {
			effect: { type: "string", short: "e" },
			props: { type: "string", default: "{}" },
			out: { type: "string", short: "o" },
			duration: { type: "string" },
			fps: { type: "string" },
			width: { type: "string" },
			height: { type: "string" },
			list: { type: "boolean" },
			help: { type: "boolean", short: "h" },
		},
		allowPositionals: false,
	});

	if (values.help) {
		printUsage();
		process.exit(0);
	}

	const entryPoint = path.resolve(process.cwd(), "src/index.ts");

	if (values.list) {
		await listEffects();
		process.exit(0);
	}

	const effectId = values.effect;
	if (!effectId) {
		console.error("Error: --effect is required\n");
		printUsage();
		process.exit(1);
	}

	let effectProps: Record<string, unknown>;
	try {
		effectProps = JSON.parse(values.props!);
	} catch {
		console.error("Error: --props must be valid JSON");
		process.exit(1);
	}

	const inputProps = { effectId, effectProps };

	const outputPath = values.out
		? path.resolve(values.out)
		: path.resolve(process.cwd(), "out", `${effectId}.mp4`);

	// Ensure output directory exists
	const outDir = path.dirname(outputPath);
	fs.mkdirSync(outDir, { recursive: true });

	console.log(`Effect: ${effectId}`);
	console.log(`Props: ${JSON.stringify(effectProps)}`);
	console.log(`Output: ${outputPath}`);
	console.log(`Bundling project...`);

	const bundleLocation = await bundle({ entryPoint });

	console.log(`Selecting composition: effect-${effectId}`);
	const composition = await selectComposition({
		serveUrl: bundleLocation,
		id: `effect-${effectId}`,
		inputProps,
	});

	const overrides = {
		durationInFrames: values.duration
			? parseInt(values.duration)
			: composition.durationInFrames,
		fps: values.fps ? parseInt(values.fps) : composition.fps,
		width: values.width ? parseInt(values.width) : composition.width,
		height: values.height ? parseInt(values.height) : composition.height,
	};

	console.log(
		`Config: ${overrides.durationInFrames}f @ ${overrides.fps}fps | ${overrides.width}x${overrides.height}`,
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
