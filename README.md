# HAP 运维 AI Codex Plugins

本项目提供可安装的 Codex 插件，涵盖 HAP 私有部署升级、发布、交付、排障和日常运维，并包含通用的 Git 提交说明、安全文件写入与最小实现 skills。

## 插件位置

- 插件目录：`plugins/hap-ops-ai-plugins/`
- 插件清单：`plugins/hap-ops-ai-plugins/.codex-plugin/plugin.json`
- Marketplace 清单：`.agents/plugins/marketplace.json`

## 当前 Skills

- `hap-upgrade-guide`：HAP 私有部署升级咨询、兼容性核验和升级文档生成。
- `hap-upgrade-issue-log`：记录 HAP 升级文档、模板约束和 HTML 输出问题及处理结果。
- `hap-private-document-release`：HAP Private Document 构建、发布申请和结果核验。
- `hap-delivery-docs`：HAP 私有部署交付文档套件生成。
- `hap-deployment-troubleshooter`：HAP 私有部署故障排查和实战案例分析。
- `hap-mongodb-slowlog-analysis`：MongoDB 4.4.x 慢日志分析、索引建议和命令生成。
- `mdis-browser-visual-check`：MDIS 页面主题、可读性与响应式布局的浏览器视觉自测。
- `mdis-issue-log`：维护 MDIS 问题记录、排查证据和验证状态。
- `hap-upgrade-issue-log`：维护 HAP 升级文档生成、模板约束和 HTML 输出的问题记录。
- `mdis-theme-maintenance`：维护 MDIS 页面和控件的深浅主题一致性。
- `github-image-workflow-builder`：创建、修复和验证多架构 GitHub Actions 镜像构建及发布流程。
- `nginx-https-cert-rotation`：生成 Nginx HTTPS 证书更换、校验和回滚手册。
- `hap-package-link-sync`：核验并同步 HAP 软件包信息及文档使用状态。
- `commit`：生成简体中文分组式 Git 提交说明，并可提交已暂存的改动。
- `utf8-safe-write`：安全编辑 UTF-8、BOM 和换行格式的文件。
- `ponytail`：编码任务的最小实现、YAGNI 和反过度设计约束。

各 skill 位于 `plugins/hap-ops-ai-plugins/skills/<skill-name>/`。

## 安装

在项目根目录执行：

```powershell
codex plugin marketplace add .
codex plugin add hap-ops-ai-plugins@personal
```

## 新增或更新 Skill

在插件的 `skills/` 下创建小写连字符目录，并添加 `SKILL.md`。可按需添加 `references/`、`assets/`、`tools/` 等资源。插件 manifest 通过 `"skills": "./skills/"` 自动发现 skills，通常不需要修改 `plugin.json`。

完成变更后，验证插件清单与新增技能，并更新 `plugin.json` 中的版本缓存标识，再重新安装插件：

```powershell
python -X utf8 -m json.tool plugins/hap-ops-ai-plugins/.codex-plugin/plugin.json | Out-Null
python -X utf8 "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/hap-ops-ai-plugins/skills/mdis-theme-maintenance
codex plugin add hap-ops-ai-plugins@personal
```
