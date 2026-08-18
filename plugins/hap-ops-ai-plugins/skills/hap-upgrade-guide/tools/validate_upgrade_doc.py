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

# 集群前三项必须复用 WorkBuddy 集群成品的完整文案；目标发布日期所在行允许被生成器替换。
CLUSTER_PREP_EXACT_LINES = (
    '> ⚠️ **重要提示**：请确保您的授权密钥仍在"升级服务"有效期内。若目标版本（**',
    '请检查您的授权密钥是否仍在"升级服务"有效期内，并确认授权到期日晚于目标版本发布日期。若授权即将到期或已过期，请联系明道云商务团队续期后再执行升级。',
    '> ⚠️ **注意**：如有前端二次开发，请联系前端二开负责同事确认此操作已完成，否则可能导致升级后前端功能异常。',
    '若系统中存在前端二次开发（即有基于 HAP 前端源码进行过定制开发），升级后前端代码可能与新版本存在差异，需要**前端二开负责同事**执行以下操作：',
    '1. 拉取最新的前端二开基础代码（官方前端仓库对应目标版本的分支或 tag）',
    '2. 将自定义的二开代码合并（merge）进最新基础代码，处理可能存在的冲突',
    '3. 构建并发布更新后的前端服务，使新版本前端生效',
    '若系统中**没有**前端二次开发，忽略本注意事项。',
    '对数据存储相关的服务器进行备份，确保以下组件的数据均已备份：MongoDB、文件存储服务及其他有状态服务。',
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--mode", choices=("single", "cluster"), required=True)
    parser.add_argument("--html", type=Path)
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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

    if args.mode == "cluster":
        for required_line in CLUSTER_PREP_EXACT_LINES:
            if required_line not in text:
                errors.append(f"集群升级前准备必须与单机逐条一致，缺少固定文案：{required_line}")
        auth_lines = [line for line in lines if line.startswith('> ⚠️ **重要提示**：请确保您的授权密钥仍在"升级服务"有效期内。若目标版本（**')]
        if len(auth_lines) != 1:
            errors.append("集群授权有效期检查必须保留 WorkBuddy 集群成品的完整重要提示，不能压缩或改写")
        if text.count("### 1. 授权有效期检查") != 1 or text.count("### 2. 前端二次开发注意事项") != 1:
            errors.append("集群升级前准备的授权和前端二开章节必须各出现一次，不能缺失或重复")
        if "请参考官方备份与部署文档执行备份" in text or "https://docs-pd.mingdao.com/deployment/docker-compose/standalone/data/backup" in text:
            errors.append("集群数据备份不得套用单机备份说明或单机备份链接")

    # 第二阶段的固定步骤必须保持对应模板的 h4 层级，防止生成器降级标题。
    if args.mode == "single":
        for heading in ("#### 1. 修改镜像版本号", "#### 2. 重启服务"):
            if heading not in lines:
                errors.append(f"缺少或错误降级第二阶段固定步骤：{heading}")
    if args.mode == "cluster":
        for heading in ("#### 1. 滚动更新", "#### 2. 非滚动更新"):
            if heading not in lines:
                errors.append(f"缺少或错误降级集群更新方式步骤：{heading}")

    # 防止生成器绕过模板，输出摘要式文档。
    if "| 项目 | 内容 |" not in lines or not any("**升级路径**" in line for line in lines):
        errors.append("缺少模板规定的版本信息表格；禁止用摘要段落替代版本信息表格")

    # 单机备份只允许提示和官方链接，不允许把旧版备份命令带回来。
    if args.mode == "single":
        try:
            backup_start = lines.index("### 3. 数据备份")
            backup_end = next(
                (i for i in range(backup_start + 1, len(lines)) if re.match(r"^###? ", lines[i])),
                len(lines),
            )
            backup_text = "\n".join(lines[backup_start:backup_end])
            if "⚠️ **升级前必须完成备份，此步骤不可跳过。**" not in backup_text:
                errors.append("单机数据备份缺少强制提示")
            if "https://docs-pd.mingdao.com/deployment/docker-compose/standalone/data/backup" not in backup_text:
                errors.append("单机数据备份缺少官方备份文档完整 URL")
            for token in ("docker exec", "mongodump", "backup mysql mongodb file"):
                if token in backup_text:
                    errors.append(f"单机数据备份区域禁止出现备份命令：{token}")
        except ValueError:
            pass

    # 镜像导入和验证命令必须在同一代码块中有用途注释。
    for index, line in enumerate(lines):
        if line.strip().startswith(("docker load", "gunzip -c ")) or line.strip() in ("docker images", "crictl images | grep mingdaoyun"):
            previous = lines[index - 1].strip() if index else ""
            if not previous.startswith("# 作用："):
                errors.append(f"镜像命令缺少上一行用途注释：{line.strip()}")

    # 单机和集群的升级前/升级后附加操作都必须在标题上标出来源版本。
    if args.mode in ("single", "cluster"):
        phase = None
        for line in lines:
            if line.startswith("### 第一阶段："):
                phase = "before"
            elif line.startswith("### 第三阶段："):
                phase = "after"
            elif line.startswith("## "):
                phase = None
            if phase and line.startswith("#### ") and re.match(r"^#### \d+\. ", line):
                allowed = ("进入 config Pod", "进入微服务容器", "在{数据库名}数据库中执行 DDL")
                if "来自 v" not in line and not any(item in line for item in allowed):
                    errors.append(f"附加操作标题缺少来源版本：{line}")

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

    if args.mode == "cluster":
        service_headings = [
            (index, line)
            for index, line in enumerate(lines)
            if line.startswith("#### ") and "来自 v" in line and ("删除" in line or "新增" in line)
        ]
        code_lines: list[str] = []
        in_code = False
        for line in lines:
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                code_lines.append(line)
        api_count = sum(1 for line in code_lines if line.strip().startswith("apiVersion:"))
        separator_count = sum(1 for line in code_lines if line.strip() == "---")
        for index, heading in service_headings:
            if lines[index - 1].strip() if index else False:
                errors.append(f"集群服务版本块前必须保留一个空行：{heading}")
            if "删除" in heading and api_count < 2:
                errors.append(f"删除服务必须包含完整 Deployment 和 Service YAML：{heading}")
            if "新增" in heading and api_count < 2:
                errors.append(f"新增服务必须包含完整 Deployment 和 Service YAML：{heading}")
            if ("、" in heading or " 和 " in heading) and ("删除" in heading or "新增" in heading):
                errors.append(f"不同服务不得合并到同一版本块：{heading}")
        if service_headings and api_count and separator_count == 0:
            errors.append("集群 service.yaml YAML 配置缺少 --- 分隔符")

    # 提到 run.sh 就必须提供完整的判断、替换命令和结束符，禁止只留文字提示。
    if "run.sh" in text:
        required_run_lines = (
            "if [ -f /data/mingdao/script/run.sh ]; then",
            "sed -i -e 's/mingdaoyun-community/mingdaoyun-hap/g' /data/mingdao/script/run.sh",
            "fi",
        )
        for required_line in required_run_lines:
            if required_line not in text:
                errors.append(f"提到 run.sh 但缺少完整操作命令：{required_line}")

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
