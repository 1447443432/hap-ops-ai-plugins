#!/usr/bin/env python3
"""Validate an upgrade Markdown document, then convert it to HTML."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("html", type=Path)
    parser.add_argument("--mode", choices=("single", "cluster"), required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    validator = root / "validate_upgrade_doc.py"
    check = subprocess.run(
        [sys.executable, str(validator), str(args.markdown), "--mode", args.mode],
        check=False,
    )
    if check.returncode != 0:
        print("Markdown 校验未通过，已停止 HTML 转换。", file=sys.stderr)
        return check.returncode

    go_tool = root / "md2html" / ("md2html.exe" if sys.platform == "win32" else "md2html")
    if go_tool.exists():
        command = [str(go_tool), "-input", str(args.markdown), "-output", str(args.html)]
    else:
        python_tool = root / "md2html-py" / "md2html.py"
        if not python_tool.exists():
            print("未找到可用的 md2html 转换工具。", file=sys.stderr)
            return 2
        command = [sys.executable, str(python_tool), "-input", str(args.markdown), "-output", str(args.html)]

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        return result.returncode
    if not args.html.exists() or args.html.stat().st_size == 0:
        print("HTML 转换完成但产物为空。", file=sys.stderr)
        return 3
    print(f"HTML 已生成：{args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
