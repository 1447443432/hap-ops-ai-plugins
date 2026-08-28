# HAP 运维 AI Codex Plugin

这是一个可通过 Codex plugin marketplace 安装的 HAP 运维 skills 插件。

## 当前包含

- `skills/hap-upgrade-guide/`：HAP 私有部署版本升级咨询与 Markdown + HTML 升级文档生成。
- `skills/hap-private-document-release/`：HAP Private Document Jenkins 构建、微服务工作表发布申请和结果核验 SOP。
- `skills/utf8-safe-write/`：Windows PowerShell/Git 项目中的 UTF-8、BOM 和换行安全编辑规范。
- `skills/ponytail/`：编码任务的最小实现、YAGNI 和反过度设计约束。
- `skills/hap-delivery-docs/`：HAP 私有部署交付文档套件生成。
- `skills/hap-deployment-troubleshooter/`：HAP 私有部署故障排查和实战案例。
- `skills/hap-mongodb-slowlog-analysis/`：MongoDB 4.4.x 慢日志分析、索引建议和可执行命令生成。
- `skills/github-image-workflow-builder/`：创建、修复和验证 amd64/arm64 GitHub Actions 镜像构建、Release、镜像推送和 HAP Webhook Workflow。
- `skills/nginx-https-cert-rotation/`：按 Nginx 安装路径、配置文件和证书路径生成 HTTPS 证书更换、校验与回滚手册。

## 扩展其他 skill

在 `skills/` 下新增一个目录，并放入该目录自己的 `SKILL.md`；同时按需加入 `references/`、`assets/`、`tools/` 等资源。插件 manifest 已通过 `"skills": "./skills/"` 自动发现这些 skill，通常不需要修改 `plugin.json`。

新增或修改 skill 后，重新运行插件校验，并用 cachebuster 更新本地安装缓存：

```powershell
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" "plugins/hap-ops-ai-plugins"
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py" "plugins/hap-ops-ai-plugins"
```
