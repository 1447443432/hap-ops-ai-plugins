#!/usr/bin/env python3
"""Fast preflight checks for generated HAP upgrade Markdown documents."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


COMMON_HEADINGS = [
    "## 升级前准备",
    "## 升级步骤",
    "### 第二阶段：升级微服务",
    "## 升级后验证",
]
SINGLE_HEADINGS = [
    "# HAP 升级指南（单机模式）",
    "### 提前准备",
    "### 1. 授权有效期检查",
    "### 2. 前端二次开发注意事项",
    "### 3. 数据备份",
    "### 4. 确认当前版本",
    "### 5. 检查资源",
]
CLUSTER_HEADINGS = [
    "# HAP 升级指南（集群模式）",
    "## 提前准备",
    "### 1. 授权有效期检查",
    "### 2. 前端二次开发注意事项",
    "### 3. 数据备份",
    "### 4. 确认当前版本",
    "### 5. 检查资源",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--mode", choices=("single", "cluster"), required=True)
    parser.add_argument("--html", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = args.markdown.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    if "\\`" in text:
        errors.append("Markdown 包含被反斜杠转义的反引号 \\`；必须写入真实 ASCII 反引号")

    fence_lines = [line for line in lines if re.match(r"^```(?:[A-Za-z0-9_+.-]+)?\s*$", line)]
    if len(fence_lines) % 2:
        errors.append(f"代码围栏数量不成对：检测到 {len(fence_lines)} 行围栏")

    in_prepare = False
    prepare_level = 0
    in_download_table = False
    for line in lines:
        heading = re.match(r"^(#{1,6}) ", line)
        if heading:
            level = len(heading.group(1))
            if line.strip() == "### 提前准备" or line.strip() == "## 提前准备":
                in_prepare = True
                prepare_level = level
            elif in_prepare and (level < prepare_level or (level == prepare_level and "若服务器" not in line)):
                in_prepare = False
                in_download_table = False
        if in_prepare and "| 文件 | 下载链接 |" in line:
            in_download_table = True
            continue
        if in_download_table and not line.strip().startswith("|"):
            in_download_table = False
        if in_download_table and line.strip().startswith("|") and "|------" not in line:
            if "](" in line or "<https://" in line or "`https://" in line:
                errors.append("下载资源区域禁止使用 Markdown 超链接或代码格式，必须直接写完整 https:// 地址")
            if "https://" not in line:
                errors.append(f"下载资源行缺少完整 https:// 地址：{line.strip()}")

    expected = SINGLE_HEADINGS if args.mode == "single" else CLUSTER_HEADINGS
    for heading in [*expected, *COMMON_HEADINGS]:
        if heading not in lines:
            errors.append(f"缺少规定标题：{heading}")

    in_code = False
    seen: dict[str, int] = {}
    for index, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if index > 1 and re.match(r"^# ", line):
            errors.append(f"第 {index} 行出现额外一级标题：{line}")
        candidate = line.strip()
        if len(candidate) < 12 or candidate.startswith(("#", "|", ">", "- ", "* ")):
            continue
        seen[candidate] = seen.get(candidate, 0) + 1
    for line, count in seen.items():
        if count > 1:
            errors.append(f"正文完全重复 {count} 次：{line}")

    if args.mode == "single":
        forbidden = ("kubectl", "crictl", "ctr -n")
    else:
        forbidden = ("docker exec", "service.sh restartall", "docker-compose")
    for token in forbidden:
        if token in text:
            errors.append(f"{args.mode} 模式包含禁止命令：{token}")

    if args.html is not None and (not args.html.exists() or args.html.stat().st_size == 0):
        errors.append(f"HTML 产物不存在或为空：{args.html}")

    if errors:
        print("升级文档校验失败：")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"升级文档校验通过：{args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
