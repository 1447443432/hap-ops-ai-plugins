# HAP 运维 AI Codex Plugins

本项目是可安装的 Codex plugin，当前包含 HAP 私有部署升级和 Private Document 发布 skills。

## 插件位置

- 插件目录：`plugins/hap-ops-ai-plugins/`
- 插件清单：`plugins/hap-ops-ai-plugins/.codex-plugin/plugin.json`
- marketplace 清单：`.agents/plugins/marketplace.json`
- 当前 skills：
  - `plugins/hap-ops-ai-plugins/skills/hap-upgrade-guide/`
  - `plugins/hap-ops-ai-plugins/skills/hap-private-document-release/`
  - `plugins/hap-ops-ai-plugins/skills/utf8-safe-write/`

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
