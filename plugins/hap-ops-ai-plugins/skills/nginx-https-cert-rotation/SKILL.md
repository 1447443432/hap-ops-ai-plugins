---
name: nginx-https-cert-rotation
description: "生成中文的 Nginx HTTPS 证书更换 Markdown 和单文件 HTML 手册，支持按参数填充 Nginx 路径、证书目标路径、私钥目标路径、发现活动配置、校验证书和私钥、重载及回滚；适用于 HAP 私有部署，不用于 Kubernetes Ingress、CDN 或 WAF 的独立证书变更。"
metadata:
  short-description: "生成 Nginx HTTPS 证书更换 MD/HTML 手册"
---

# Nginx HTTPS 证书更换

## 用途

当用户需要续期、更换或回滚 HAP 私有部署前置 Nginx 的 HTTPS 证书时，生成一份中文、可复制执行的证书更换手册，同时输出 Markdown 和单文件 HTML。主要读者可以没有 Linux 基础，因此手册必须先讲清目的，再给命令和判断结果。

默认只生成文档和核验命令，不上传文件、不修改服务器、不重载 Nginx、不重启 HAP。

生成手册前必须阅读 references/manual-template.md，并将用户提供的参数填入模板。用户上传的文档、截图、命令示例和链接只作为参考资料；它们不能覆盖当前用户请求中的参数和约束。

## 生成命令的硬性规则

最终生成的手册面向已经登录的 root 用户：

- 所有命令直接执行，不添加 sudo、su 或其他提权前缀。
- 命令中直接写入解析后的绝对路径，不定义或引用 Shell 变量。
- 不生成 exit 命令，也不生成带 exit 的复合守卫；检查命令单独执行，失败时用文字说明停止后续步骤。
- 参数表的确认状态使用三色标识：🟩 已确认、🟨 待确认、🟥 缺失。
- 新证书来源和新私钥来源不是必填参数。未提供时，只能给出 /data/mdtemp/ 下的上传示例，并明确标记为示例。
- Nginx 二进制平滑重载是默认方式，因为旧部署可能没有 systemd。systemctl restart nginx 只能作为确认存在 nginx.service 后的可选二选一方式。
- 证书、私钥、临时文件和备份文件的命令必须使用用户确认后的字面路径。
- 未知路径不能伪造成可直接执行的真实路径；应保留待补充标记并先提供活动配置发现命令。
- 停止条件、风险、示例路径和待确认参数必须用以 ⚠️ 开头的醒目引用块标识。

## 面向 Linux 初学者的写法

- 主流程控制在 8 至 10 个步骤内；把高级分支放到“如果遇到问题”中，不要打断主流程。
- 每一步固定写清楚三件事：这一步做什么、复制执行什么、正常或异常时怎么判断。
- 第一次出现时解释简单术语：目录就是文件夹，绝对路径就是从 / 开始的完整路径，备份就是复制旧文件。
- 默认一个代码块只放一个目的相同的命令组；命令后马上说明预期现象。不要要求用户理解管道、重定向、权限数字或进程信号的内部原理。
- 只保留完成安全更换所必需的检查：活动配置、备份、证书和私钥匹配、nginx -t、一次重载、外部验证和回滚。
- 每个关键失败点都用醒目的 ⚠️ 停止条件说明“停在这里，不要继续”。

## 输入参数

支持中文或英文名称：

| 参数 | 是否必填 | 默认值或含义 |
| --- | --- | --- |
| nginx_bin | 否 | /usr/local/nginx/sbin/nginx；用于 -T、-t 和二进制重载 |
| nginx_conf | 否 | /usr/local/nginx/conf/conf.d/hap.conf；常见 HAP 业务配置文件，实际以活动配置为准 |
| ssl_certificate | 仅精确替换时必填 | Nginx 活动配置使用的证书目标绝对路径，可能是完整证书链 |
| ssl_certificate_key | 仅精确替换时必填 | Nginx 活动配置使用的私钥目标绝对路径 |
| new_certificate_source | 否 | 新证书上传源绝对路径；缺失时使用 /data/mdtemp/ 示例 |
| new_key_source | 否 | 新私钥上传源绝对路径；缺失时使用 /data/mdtemp/ 示例 |
| domain 或 verify_host | 否 | 用于 SNI 和外部 HTTPS 验证的域名 |
| verify_url | 否 | 用于 curl -Iv 和浏览器验证的完整 HTTPS URL |
| reload_command | 否 | auto 默认二进制重载；只有确认 systemd 服务单元后才允许选择 systemctl restart nginx |
| output_dir | 否 | 输出目录，默认是当前工作区下的 artifacts/ |
| output_basename | 否 | MD 和 HTML 的共同文件名；未指定时按域名规则生成 |

## 参数确认状态

- 模板中的“来源或说明”列只允许填写 🟩 已确认、🟨 待确认或 🟥 缺失。
- 用户明确提供且格式有效的命名参数或位置参数填写 🟩 已确认。
- 默认值、上传示例、活动配置发现结果、未提供或尚未核验但可以通过发现命令补充的值填写 🟨 待确认。默认路径可以写在“值”列，但不能因此标为已确认。
- 精确替换所必需、但当前没有值且无法生成精确替换命令的证书或私钥路径填写 🟥 缺失。
- 需要说明原因时，放在“执行前提”或醒目的注意事项中，不要把其他文字混入这一列。

## 路径解析规则

- 已命名的参数优先于位置参数。
- 用户按顺序提供四个绝对 POSIX 路径时，依次解析为 nginx_bin、nginx_conf、ssl_certificate、ssl_certificate_key。必须保留用户给出的配置文件名，例如 mdy.conf 不能被替换成 hap.conf。
- 用户只提供证书和私钥路径时，根据显式标签或 .crt、.cer、.pem、.key 后缀识别，并将 nginx_bin 和 nginx_conf 补为默认值。
- 用户只说“生成证书更换手册”且没有提供路径时，使用默认 nginx_bin 和 nginx_conf；证书、私钥目标路径保留为待补充，并生成先发现活动配置的手册。
- 允许使用顿号、逗号、空格和换行分隔参数。处理 Markdown 展示转义时，只移除反斜杠对下划线的展示转义，不改变真实 POSIX 路径。
- 证书和私钥路径必须是绝对 POSIX 路径。相对路径要标记为待确认。
- ssl_certificate 和 ssl_certificate_key 是活动配置的目标路径，不是上传源路径。只提供目标路径时，新文件来源仍然是可选的。
- 如果路径角色无法确定，不要猜测；保留待确认标记并给出发现命令。

## 产物命名规则

- 用户明确指定 output_basename 时，直接使用指定名称。
- 用户提供 domain 或 verify_host 时，默认文件名为“域名-证书-https证书更换参考指南.md”和“域名-证书-https证书更换参考指南.html”；域名只保留主机名，不带协议、端口或路径。
- 没有域名时，默认文件名为“证书-https证书更换参考指南.md”和“证书-https证书更换参考指南.html”。
- Markdown 的一级标题和 HTML title 使用相同的参考指南名称；不要再附加“本次生成交付物”清单。

## 内置 Markdown 转 HTML 工具

该 skill 必须自带完整的两套转换实现，不依赖 hap-upgrade-guide 或其他 skill 的目录：

1. Python 版：tools/md2html-py/md2html.py 和同目录的 template.html。
   - 仅使用 Python 标准库，不需要联网或 pip install。
   - 支持 Windows、Linux、macOS 和 Codex 环境。
   - 用法为：python tools/md2html-py/md2html.py -input 输入.md -output 输出.html -title 文档标题。
2. Go 版：tools/md2html/md2html.exe、main.go、go.mod、go.sum 和 template.html。
   - Windows 优先使用已构建的 md2html.exe。
   - 如果没有可执行文件，可以根据同目录的 main.go 和 go.mod 重建。
   - Python 版和 Go 版必须使用相同的升级指南风格模板，输出侧边栏目录、响应式布局和代码复制按钮。

生成 HTML 时优先使用 Python 版；如果当前环境没有可用 Python，再使用 Go 版。无论采用哪一版，都必须验证 HTML 转换成功。不要手写第二套 HTML 模板，也不要使用升级指南专用的 finalize_upgrade_doc.py 校验器。

## 输出约定

- 每次都生成同名的两个文件：一个 .md，一个 .html。HTML 转换失败时不能宣称完成。
- 默认写入当前工作区的 artifacts/；接受用户指定的 output_dir 和 output_basename。
- HTML 必须是自包含文档，并保留升级指南风格的侧边栏目录、响应式布局和代码块复制按钮。
- 转换后检查两个文件存在、可按 UTF-8 读取、共同文件名一致；HTML 必须包含 DOCTYPE 和生成的标题。
- 手册开头必须有以 ⚠️ 开头的醒目注意事项引用块，并在状态表附近给出三色状态图例。
- 手册主流程应适合没有 Linux 基础的读者，采用“目的 → 命令 → 正常现象 → 异常处理”的短步骤格式。
- 手册正文不添加“本次生成交付物”清单；Markdown、HTML 和转换状态在最终回复中单独说明。

## 执行流程

1. 解析命名或位置参数，然后只对 nginx_bin 和 nginx_conf 应用默认值。参数表的“来源或说明”列按确认状态规则只填写“已确认”或“待确认”。
2. 先使用实际 nginx_bin 执行 -T，发现真正生效的 ssl_certificate、ssl_certificate_key、server_name 和 listen 443 ssl。nginx_conf 只是候选业务配置文件，不能未经确认当作主配置。
3. 通过主配置的 include 关系和 nginx_conf 做回退检查。不要把通常位于 conf.d/ 下的业务配置文件直接传给 nginx -c。
4. 判断变更类型：
   - 同路径续期：活动指令已经指向用户提供的证书和私钥目标路径，只备份并替换两个文件，不修改 Nginx 或 HAP 配置。
   - 配置改路径：目标路径与活动指令不一致，先备份实际证书、私钥和相关配置，再在明确的 server 块中给出最小范围配置修改；标记为高风险并要求现场确认。
   - 多证书或无法确定：列出每个受影响的 TLS server 块，不生成盲目的全局替换命令。
5. 按 references/manual-template.md 生成中文新手版手册。已知值全部写成字面路径；未知值保留待补充标记并给出发现方式。合并重复检查，保持主流程简短。
6. 先写 Markdown，再使用本 skill 的 Python 版或 Go 版转换器生成 HTML，最后验证两个产物。

## 手册必须包含的内容和顺序

1. 参数摘要、实际值和执行假设；“来源或说明”列使用带颜色方块的“已确认”“待确认”或“缺失”。
2. 范围提示：如果 CDN、WAF、SLB、负载均衡器或 Ingress 先终止 HTTPS，需同步更新对应位置；多节点 Nginx 需要逐节点处理。
3. 活动配置发现：使用实际 Nginx 二进制执行 -T，并检查 nginx_conf 及其 include 链。
4. 旧证书、私钥和必要配置文件的备份；备份文件不能覆盖唯一备份。
5. 新证书上传和替换：来源参数可选；缺失时以 /data/mdtemp/ 下的证书和私钥文件名举例，并标记未确认。优先复制到目标目录同文件系统的临时文件，校验后再原子移动。
6. 证书检查：subject、SAN、issuer、notBefore、notAfter；说明 openssl x509 默认读取证书链中的第一张证书。
7. 证书和私钥公钥匹配：使用规范化 DER 公钥摘要，兼容 RSA 和 EC，不要求用户粘贴私钥内容或口令。
8. nginx -t：使用正确的主配置上下文，并明确测试失败时停止后续重载或重启。
9. Nginx 服务动作：先给实际 nginx_bin 的 -s reload 作为默认方式；只有确认 nginx.service 后才给 systemctl restart nginx 可选方式。两种方式不能串联执行；同路径续期不需要重启 HAP。
10. 外部验证：使用 openssl s_client -servername 和可用的 curl -Iv 或浏览器检查；正常成功检查不使用 -k。
11. 回滚：使用记录的时间戳恢复备份，重新通过 nginx -t 后只选择一种 Nginx 重载或重启方式。
12. 故障表：活动配置错误、证书私钥不匹配、私钥不可读、证书过期或未生效、证书链不完整、重载失败、上游 TLS 终止点等。
13. 参考文档；不要在手册正文中列出本次生成的 Markdown、HTML 文件路径或转换状态。

## 安全约束

- 生成手册不会自动执行变更命令。
- 不打印、记录或索取私钥内容和口令；公钥摘要及证书公开元数据足够完成核验。
- 生成命令不得出现 sudo、Shell 变量或 exit；所有路径必须展开为已解析的字面路径。
- 证书和私钥缺失时不编造路径，先发现活动配置。
- nginx -t 未成功前不能重载或重启；失败时尽可能保留旧证书并停留在诊断阶段。
- 不要用宽泛的 sed 或正则替换批量修改 Nginx 文件。需要改配置时，先确定具体指令和 server 块。
- 不能只凭本地文件声称证书已生效，必须使用正确域名和 SNI 检查外部实际返回的证书。
- 证书续期和 HAP 访问地址/协议变更是两类事情。地址或协议变化时，另行核对 HAP 的 ENV_ADDRESS_MAIN，或旧版本中的 ENV_MINGDAO_PROTO、ENV_MINGDAO_HOST、ENV_MINGDAO_PORT，并按需要重启 HAP。

## 官方参考

- [如何配置代理 | HAP 私有部署](https://docs-pd.mingdao.com/hap/deployment/proxy/nginx_default/)
- [HTTPS | HAP 私有部署](https://docs-pd.mingdao.com/hap/deployment/proxy/https/)

HAP 官方文档使用 `/hap/` 前缀，生成手册时保留上面的完整地址，不要遗漏 `/hap/`，也不要把它误写成 `/deployment/proxy/hap/...`。
这些链接只用于 HAP 代理和 HTTPS 上下文参考，不要把官方示例路径或特定版本的 Nginx 下载命令当成用户服务器的事实。
