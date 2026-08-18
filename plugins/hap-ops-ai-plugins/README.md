# HAP 运维 AI Codex Plugin

这是一个可通过 Codex plugin marketplace 安装的 HAP 运维 skills 插件。

## 当前包含

- `skills/hap-upgrade-guide/`：HAP 私有部署版本升级咨询与 Markdown + HTML 升级文档生成。

## 扩展其他 skill

在 `skills/` 下新增一个目录，并放入该目录自己的 `SKILL.md`；同时按需加入 `references/`、`assets/`、`tools/` 等资源。插件 manifest 已通过 `"skills": "./skills/"` 自动发现这些 skill，通常不需要修改 `plugin.json`。

新增或修改 skill 后，重新运行插件校验，并用 cachebuster 更新本地安装缓存：

```powershell
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" "plugins/hap-ops-ai-plugins"
python "$env:USERPROFILE/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py" "plugins/hap-ops-ai-plugins"
```
