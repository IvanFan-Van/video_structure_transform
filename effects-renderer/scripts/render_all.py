import json
import subprocess
import traceback

with open("render_commands.jsonl", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        try:
            data = json.loads(line)
            props = json.loads(data['props'])
            effect_id = props.get("effectId", "?")
            out_file = f"out/{effect_id}.mp4"
            print(f"[{idx}]: {effect_id}")

            cmd = [
                "pnpm", "exec", "remotion", "render",
                "src/index.ts", "render", out_file,
                f"--props={data['props']}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

            if result.returncode != 0:
                print(f"  FAILED (exit code {result.returncode})")
                print(f"  CMD: {' '.join(cmd)}")
                if result.stderr:
                    print(f"  STDERR:\n{result.stderr}")
                if result.stdout:
                    print(f"  STDOUT:\n{result.stdout}")
            else:
                print("  OK")
        except Exception:
            effect_id_fallback = "?"
            print(f"[{idx}]: {effect_id_fallback} EXCEPTION:")
            traceback.print_exc()