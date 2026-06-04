"""
一次性将所有 58 个 remocn 组件安装到 _templates/src/components/remocn/

    运行一次（需要网络）后，所有后续 scaffold 的项目都自带完整的 remocn 组件库。
    无需联网下载，无需用户手动安装。

运行:
    python install_remocn_cache.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════

PROJECT_DIR = Path(__file__).resolve().parent  # videos/
TEMPLATES_DIR = PROJECT_DIR / "_templates"
TARGET_DIR = TEMPLATES_DIR / "src" / "components" / "remocn"
COMPONENTS_JSON = PROJECT_DIR / "remocn_components.json"
TEMP_DIR = PROJECT_DIR / ".remocn_install_tmp"

SHADCN_COMPONENTS_JSON = """\
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib"
  },
  "registries": {
    "@remocn": "https://www.remocn.dev/r/{name}.json"
  }
}
"""

PACKAGE_JSON = '{"name":"remocn-cache-install","private":true}'

# ═══════════════════════════════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════════════════════════════

_PNPM = shutil.which("pnpm")
if _PNPM is None:
    raise RuntimeError("未找到 pnpm，请先安装: npm install -g pnpm")


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """执行命令，pnpm 用完整路径避免 PATH 问题。"""
    if cmd[0] in ("pnpm", "pnpx"):
        cmd = [_PNPM] + cmd[1:]
    elif cmd[0] == "npx":
        cmd = [_PNPM, "exec"] + cmd[1:]
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)

# 组件名 → 文件名的覆盖（少数不遵循 pascal→kebab 规则的情况）
_COMPONENT_SLUG_OVERRIDES: dict[str, str] = {
    "ChatToPreviewLayout": "dynamic-split-screen",
}


def _pascal_to_kebab(name: str) -> str:
    """PascalCase → kebab-case"""
    result = []
    for i, ch in enumerate(name):
        if ch.isupper():
            if i > 0 and (
                name[i - 1].islower()
                or (i + 1 < len(name) and name[i + 1].islower())
            ):
                result.append("-")
            result.append(ch.lower())
        else:
            result.append(ch)
    return "".join(result)


def component_slug(name: str) -> str:
    if name in _COMPONENT_SLUG_OVERRIDES:
        return _COMPONENT_SLUG_OVERRIDES[name]
    return _pascal_to_kebab(name)


def load_component_names() -> list[str]:
    with open(COMPONENTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [c["name"] for c in data]


# ═══════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════

def main():
    names = load_component_names()
    print(f"\n📋 共 {len(names)} 个 remocn 组件待安装\n")

    # ── 创建临时项目 ────────────────────────────────────────────
    print("🏗️  创建临时安装项目...")
    if TEMP_DIR.exists():
        print(f"  清空旧缓存: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 写入 package.json (无 BOM)
    with open(TEMP_DIR / "package.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(PACKAGE_JSON)

    # 写入 components.json
    with open(TEMP_DIR / "components.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(SHADCN_COMPONENTS_JSON)

    # 初始化 pnpm + 安装 shadcn CLI（本地安装，避免每次 dlx 重复下载）
    print("安装 shadcn CLI...")
    _run(["pnpm", "install"], TEMP_DIR, timeout=120)
    # 用 pnpm dlx 已缓存版本，后续调用很快
    print("测试安装一个组件确认 shadcn 可用...")
    _run(["pnpm", "dlx", "shadcn@latest", "add", "@remocn/blur-reveal"], TEMP_DIR, timeout=120)

    # ── 批量安装组件 ────────────────────────────────────────────
    # 分批: 每批 10 个，避免命令行过长
    batch_size = 10
    failed: list[str] = []
    installed = 0

    for i in range(0, len(names), batch_size):
        batch = names[i : i + batch_size]
        packages = [f"@remocn/{component_slug(n)}" for n in batch]
        batch_num = i // batch_size + 1
        total_batches = (len(names) + batch_size - 1) // batch_size

        print(
            f"📥 [{batch_num}/{total_batches}] 安装: "
            + ", ".join(batch)
            + " ..."
        )

        try:
            result = _run(
                ["pnpm", "dlx", "shadcn@latest", "add"] + packages,
                TEMP_DIR,
                timeout=300,
            )
            if result.returncode == 0:
                installed += len(batch)
                print(f"  OK {len(batch)} 个")
            else:
                print(f"  此批失败:")
                for line in result.stderr.split("\n")[-5:]:
                    if line.strip():
                        print(f"     {line.strip()}")
                # 逐个重试失败的
                for n in batch:
                    pkg = f"@remocn/{component_slug(n)}"
                    retry = _run(
                        ["pnpm", "dlx", "shadcn@latest", "add", pkg],
                        TEMP_DIR,
                        timeout=120,
                    )
                    if retry.returncode == 0:
                        installed += 1
                    else:
                        failed.append(n)
                        print(f"  失败: {n}")
        except subprocess.TimeoutExpired:
            failed.extend(batch)
            print(f"  超时: {len(batch)} 个")

    # ── 复制到 _templates ───────────────────────────────────────
    source = TEMP_DIR / "src" / "components" / "remocn"
    if not source.exists():
        print("\n❌ 源目录不存在，安装可能是完全失败的")
        sys.exit(1)

    file_count = len(list(source.glob("*.tsx")))
    print(f"\n📂 安装目录包含 {file_count} 个 .tsx 文件")

    if TARGET_DIR.exists():
        print("  清空旧缓存...")
        shutil.rmtree(TARGET_DIR, ignore_errors=True)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 复制文件
    for f in source.glob("*.tsx"):
        shutil.copy2(f, TARGET_DIR / f.name)
    final_count = len(list(TARGET_DIR.glob("*.tsx")))
    print(f"📋 已缓存 {final_count} 个组件到: {TARGET_DIR}")

    # ── 清理临时目录 ────────────────────────────────────────────
    print(f"🧹 清理临时目录: {TEMP_DIR}")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # ── 输出结果 ─────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print(f"  ✅ 安装完成")
    print(f"  成功: {installed} 个")
    if failed:
        print(f"  失败: {len(failed)} 个: {', '.join(failed)}")
    print(f"  缓存位置: {TARGET_DIR}")
    print(f"{'=' * 62}\n")


if __name__ == "__main__":
    main()
