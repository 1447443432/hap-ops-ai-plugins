# HAP 运维 AI Codex Plugin

这是一个通过 Codex plugin marketplace 安装的 HAP 运维 skills 插件。

## 当前包含

- `skills/hap-upgrade-guide/`：HAP 私有部署升级咨询、兼容性核验和 Markdown/HTML 文档生成。
- `skills/hap-private-document-release/`：HAP Private Document 构建、发布申请和结果核验 SOP。
- `skills/hap-delivery-docs/`：HAP 私有部署交付文档套件生成。
- `skills/hap-deployment-troubleshooter/`：HAP 私有部署故障排查和实战案例。
- `skills/hap-mongodb-slowlog-analysis/`：MongoDB 4.4.x 慢日志分析、索引建议和命令生成。
- `skills/mdis-browser-visual-check/`：MDIS 页面主题、可读性与响应式布局的浏览器视觉自测。
- `skills/mdis-issue-log/`：维护 MDIS 问题记录、排查证据和验证状态。
- `skills/mdis-theme-maintenance/`：维护 MDIS 页面和控件的深浅主题一致性。
- `skills/github-image-workflow-builder/`：多架构 GitHub Actions 镜像构建、推送和 Release 工作流。
- `skills/nginx-https-cert-rotation/`：Nginx HTTPS 证书更换、校验和回滚手册。
- `skills/hap-package-link-sync/`：核验并同步 HAP 软件包信息及文档使用状态。
- `skills/commit/`：生成简体中文分组式 Git 提交说明，并可提交已暂存改动。
- `skills/utf8-safe-write/`：Windows PowerShell/Git 项目的 UTF-8、BOM 和换行安全编辑规范。
- `skills/ponytail/`：编码任务的最小实现、YAGNI 和反过度设计约束。

## 新增或更新 Skill

在 `skills/` 下新增目录并放入 `SKILL.md`，按需添加 `references/`、`assets/`、`tools/` 等资源。manifest 通过 `"skills": "./skills/"` 自动发现 skills，通常无需修改 `plugin.json`。

新增或修改 skill 后，在仓库根目录验证插件清单与新增技能，更新 `plugin.json` 的版本缓存标识，然后重新安装插件：

```powershell
python -X utf8 -m json.tool plugins/hap-ops-ai-plugins/.codex-plugin/plugin.json | Out-Null
python -X utf8 "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/hap-ops-ai-plugins/skills/mdis-theme-maintenance
codex plugin add hap-ops-ai-plugins@personal
```
