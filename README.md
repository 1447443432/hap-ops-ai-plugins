# HAP 运维 AI Codex Plugins

本项目是可安装的 Codex plugin，面向 HAP 私有部署升级、发布、交付、排障和日常运维，同时提供通用的安全写入与最小实现约束 skills。

## 插件位置

- 插件目录：`plugins/hap-ops-ai-plugins/`
- 插件清单：`plugins/hap-ops-ai-plugins/.codex-plugin/plugin.json`
- marketplace 清单：`.agents/plugins/marketplace.json`
- 当前 skills：
  - `hap-upgrade-guide`：HAP 私有部署版本升级咨询、兼容性核验和 Markdown/HTML 升级文档生成。
  - `hap-private-document-release`：Jenkins 构建、微服务工作表发布申请和结果核验。
  - `hap-delivery-docs`：HAP 私有部署交付文档套件生成。
  - `hap-deployment-troubleshooter`：HAP 私有部署故障排查和实战案例分析。
  - `hap-mongodb-slowlog-analysis`：MongoDB 4.4.x 慢日志分析、索引建议和可执行命令生成。
  - `github-image-workflow-builder`：创建、修复和验证 amd64/arm64 GitHub Actions 镜像构建、Release、镜像推送和 HAP Webhook Workflow。
  - `utf8-safe-write`：Windows PowerShell/Git 项目的 UTF-8、BOM 和换行安全编辑。
  - `ponytail`：编码任务的最小实现、YAGNI 和反过度设计约束。

对应目录：`plugins/hap-ops-ai-plugins/skills/<skill-name>/`

## 安装

在项目根目录执行：

```powershell
codex plugin marketplace add .
codex plugin add hap-ops-ai-plugins@personal
```

## 扩展其他 skill

在插件的 `skills/` 下新增一个小写连字符目录，并放入 `SKILL.md`：

```text
plugins/hap-ops-ai-plugins/skills/<skill-name>/SKILL.md
```

可按需在该目录中加入 `references/`、`assets/`、`tools/` 等资源。新增 skill 后重新安装或更新插件缓存即可。

## 校验

```powershell
py -3.14 "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" `
  "plugins/hap-ops-ai-plugins"
```
