---
name: github-image-workflow-builder
description: 创建、修复和验证项目级 GitHub Actions 镜像构建 Workflow，适用于 amd64/arm64 分开构建、可选镜像推送、Release 打包、Webhook 通知和按策略清理 Workflow 运行记录。
metadata:
  short-description: 严谨构建和排障 GitHub 镜像 Workflow
---

# GitHub Image Workflow Builder

## 适用范围

当用户要求创建、修改、排障或验证 GitHub Actions 镜像构建 Workflow 时使用本技能。常见任务包括：

- amd64 和 arm64 分开构建，并使用对应 Runner；
- 构建、保存、推送镜像，生成 Release 附件；
- 从已有镜像拉取后打包 Release；
- 发送 HAP Webhook；
- 清理 GitHub Actions 运行记录；
- 分析 actionlint、Job skipped、权限、Artifact、Release、buildx 和镜像构建失败。

不用于只修改普通 Dockerfile、普通业务脚本或与 GitHub Workflow 无关的发布任务。

## 开始前检查

先读取并保留用户已有改动，至少检查：

- `Dockerfile`、`.dockerignore`；
- `.github/workflows/`；
- `.github/image-make/`、`.image-build.env`；
- `README.md`、Git 状态和远程分支。

不得把项目的镜像仓库、Release 名、Webhook 地址、账号或密码硬编码进通用 Workflow。项目专属值放在配置文件、Repository Variables 或 Secrets 中。

## 架构构建要求

- amd64 使用 `linux/amd64` 和 `ubuntu-24.04`；
- arm64 使用 `linux/arm64` 和原生 `ubuntu-24.04-arm`；
- 除非用户明确要求，不使用 QEMU 在 amd64 Runner 上模拟 arm64；
- `BASE_IMAGE_AMD64` 与 `BASE_IMAGE_ARM64` 独立解析和校验，不通过字符串替换推导架构镜像；
- Dockerfile 保持可手动构建，CI 通过 `--build-arg BASE_IMAGE=...` 覆盖基础镜像；
- buildx 必须显式初始化并使用明确的 Builder，不依赖空的 `BUILDX_BUILDER` 或隐式 Builder；
- 第三方 Action 固定到完整 commit SHA；Docker 相关 Action 固定到经过验证的 digest 或完整 SHA。

默认不要创建多架构 manifest。除非用户明确要求，否则分别生成 amd64 和 arm64 镜像、Artifact 与 Release 附件。

## 运行模式和配置优先级

如果项目支持多种运行模式，必须明确区分：

- `build-release`：构建并生成 Release；
- `pull-release`：不构建，从指定已有镜像拉取并生成 Release；
- `build-push-release`：构建、推送镜像并生成 Release。

Git push 与 `workflow_dispatch` 的输入必须区分。推荐使用 `PUSH_OPERATION=auto|build-release|pull-release|build-push-release`：

- `auto` 仅在 Aliyun Registry、目标镜像和认证配置完整时选择推送模式，否则降级为 `build-release`；
- 手动指定具体模式时必须严格执行该模式，不能因缺少配置偷偷改成其他模式；
- `pull-release` 不得误启动 Build；
- `build-push-release` 缺少必要推送配置时必须阻止后续构建、打包和 Release，并在 Summary 说明缺失项。

推荐优先级：`workflow_dispatch` 输入 > Repository Variables > 项目配置文件 > Workflow 默认值。账号、密码、Webhook URL、AppKey、Sign 只允许来自 Secrets，不得写入仓库。

## Aliyun 镜像要求

推送前必须校验：

- Registry 地址非空且与目标镜像 Registry 一致；
- 目标镜像包含 namespace 和 repository；
- amd64、arm64 目标地址明确且架构对应；
- Registry 登录使用 Secrets；
- `docker tag` 和 `docker push` 使用完整目标地址，不自行拼接或强制追加 `latest`。

缺少推送配置时，`build-release` 仍可独立工作；不要因为未配置推送而伪造镜像地址或让 Release 失败。

## Release、Artifact 和 Summary

- Release tag 只允许 `[A-Za-z0-9._-]+`，同时用于 Release 和 Artifact 文件名；
- Artifact 名称由镜像最后一段、架构和 tag 生成，例如 `hap-alloy-vlogs-mongodb-amd64_1.0.0.tar.gz`；
- Release manifest 必须根据实际 Artifact、镜像来源、架构和 SHA256 生成；
- `pull-release` 和 `build-push-release` 的 manifest 记录 Aliyun 镜像，`build-release` 记录本地构建镜像；
- Summary 展示实际 tag、Release 名、Dockerfile、Build context、基础镜像、目标镜像、模块状态、跳过原因、Artifact 名称和下载链接；
- Summary、日志和 Webhook 不得输出密码、Token、签名或完整 Secret；
- Webhook 仅在 URL、开关和必要凭据齐全且 Release 成功后发送；Webhook 跳过不应导致 Release 失败；
- `attachment_urls` 若为兼容 HAP 的字段，应输出 JSON 字符串而不是 JSON 数组。

## Workflow 运行记录清理

只有在当前 Workflow 的构建、打包、Release 以及必要通知流程成功后，才运行清理 Job。清理 Job 必须使用：

```yaml
permissions:
  actions: write
  contents: read
```

清理语义固定为：

1. 当前 Job 执行时，当前 Workflow 通常仍是 `in_progress`，所以 GitHub API 的 `status=completed` 结果不包含当前运行；
2. 使用 `github.run_id` 显式保护当前运行；
3. 查询目标 Workflow 的所有 `status=completed` 运行；
4. 删除除当前 `github.run_id` 外的全部已完成运行，包括 `success`、`failure`、`cancelled` 等结论；
5. 当前运行、排队中和进行中的运行不得删除；
6. 当前运行必须成功后才允许执行清理，这样最终只保留最新成功运行；
7. 删除运行会同时删除其日志和关联 Artifact，但不会删除 GitHub Release 或 Release 附件；
8. 清理失败不应使已经成功的构建或 Release 变成失败，建议清理 Job 使用 `continue-on-error: true`，同时在日志和 Summary 中明确报告删除失败。

分页 API 必须使用以下思路，不能把 GitHub CLI 的 `--slurp` 和 `--jq` 同时使用：

```bash
completed_runs="$(
  gh api --paginate "${endpoint}" \
    | jq -s -r --arg current_run_id "${CURRENT_RUN_ID}" '
      [.[].workflow_runs[]
        | select(.status == "completed")
        | select((.id | tostring) != $current_run_id)]
      | .[]
      | [.id, .run_number, .created_at]
      | @tsv
    '
)"
```

不能使用“按成功结论排序后保留第一条”的逻辑，因为清理 Job 执行时当前运行尚未完成，会把旧成功运行误认为最新成功运行。不能默认保留失败记录；是否保留失败记录必须由用户明确要求。

清理脚本应使用 `set -euo pipefail`，避免 `head` 造成 SIGPIPE；删除前输出候选 ID 和当前保留 ID；删除后输出实际删除数量。删除循环最好收集单个删除失败并继续处理，最后通过 Summary 报告失败项。

## 权限和 Job 依赖

- Workflow 默认权限为 `contents: read`；
- 只有创建或更新 Release 的 Job 才提升到 `contents: write`；
- 只有清理 Job 使用 `actions: write`；
- 清理 Job 使用 `always()` 配合显式的上游结果判断，避免可选 Job 的 `skipped` 造成误判；
- 每个需要读取仓库文件的独立 Job 都要自行 checkout；Job 之间只通过 Artifact 和 Outputs 共享结果，不依赖共享工作目录；
- 清理 Job 不得依赖一个已经被清理的外部 Workflow。

## 验证和排障

修改后按实际范围验证：

1. YAML 和表达式通过 `actionlint`；
2. Python 脚本通过 `ast.parse` 或项目测试；
3. Shell 脚本通过 `bash -n`；
4. `git diff --check` 通过；
5. 检查 Job、matrix、Runner、Outputs、Secrets、权限和 `if` 条件；
6. 运行一次手动或推送 Workflow，核对每个 Job 的真实结论；
7. 成功运行后检查 Actions 列表：应只剩当前最新成功运行，失败和取消的旧运行也应被删除；
8. 检查清理 Job 日志，确认当前 `run_id` 未被删除、候选记录和删除数量符合预期；
9. 若清理 Job 失败，先看其 API/JQ 日志，不要误判为 Docker 构建失败；
10. 若看到 `--slurp option is not supported with --jq`，立即改为 `gh api --paginate ... | jq -s`；
11. 若 Build 成功但 Workflow 失败，检查清理、通知和 Release Job 是否把非核心收尾错误传播到了 Workflow 总结。

## 交付规则

用户明确要求提交时才 commit；用户明确要求推送时才 push。提交前检查 Git 状态、差异和验证结果，提交后报告 commit、分支、Workflow run ID 和最终运行状态。不要声称本地未执行的 Docker 构建已经验证。

项目专属说明应写入项目 README；本技能只保留通用规则，不写入具体仓库名、镜像地址、客户地址或凭据。
