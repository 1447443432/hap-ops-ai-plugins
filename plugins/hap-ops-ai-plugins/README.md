# HAP 运维 AI Codex Plugin

这是一个通过 Codex plugin marketplace 安装的 HAP 运维 skills 插件。

## 当前包含

- `skills/hap-upgrade-guide/`：HAP 私有部署升级咨询、兼容性核验和 Markdown/HTML 文档生成。
- `skills/hap-private-document-release/`：HAP Private Document 构建、发布申请和结果核验 SOP。
- `skills/hap-delivery-docs/`：HAP 私有部署交付文档套件生成。
- `skills/hap-deployment-troubleshooter/`：HAP 私有部署故障排查和实战案例。
- `skills/hap-mongodb-slowlog-analysis/`：MongoDB 4.4.x 慢日志分析、索引建议和命令生成。
- `skills/github-image-workflow-builder/`：多架构 GitHub Actions 镜像构建、推送和 Release 工作流。
- `skills/nginx-https-cert-rotation/`：Nginx HTTPS 证书更换、校验和回滚手册。
- `skills/hap-package-link-sync/`：核验并同步 HAP 软件包信息及文档使用状态。
- `skills/commit/`：生成简体中文分组式 Git 提交说明，并可提交已暂存改动。
- `skills/utf8-safe-write/`：Windows PowerShell/Git 项目的 UTF-8、BOM 和换行安全编辑规范。
- `skills/ponytail/`：编码任务的最小实现、YAGNI 和反过度设计约束。

## 新增或更新 Skill

在 `skills/` 下新增目录并放入 `SKILL.md`，按需添加 `references/`、`assets/`、`tools/` 等资源。manifest 通过 `"skills": "./skills/"` 自动发现 skills，通常无需修改 `plugin.json`。

新增或修改 skill 后，运行插件验证和本地缓存标识更新：

```powershell
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" "plugins/hap-ops-ai-plugins"
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py" "plugins/hap-ops-ai-plugins"
```
