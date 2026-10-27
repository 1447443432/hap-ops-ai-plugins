---
name: hap-private-document-release
description: HAP Private Document 更新发布 SOP（标准流程）。从 Jenkins 构建到写入「研发管理-发布-微服务」工作表并核验的端到端发布流程。触发：用户提到"发布微服务""更新发布""更新 hc/ophc""HAP Private Document 更新""触发 document 构建并上线""按发布 SOP 走""走标准发布流程"等。涉及提交身份、Jenkins 用户名/token 等认证信息时，一律提示用户当场授权或输入，绝不硬编码——本 skill 可多人多机共用。
---

# HAP Private Document 更新发布 SOP（标准流程）

Jenkins 构建 → 取镜像值 → 写「研发管理 → 发布 → 微服务」工作表 → 工作流自动发布 → 读回核验。

> 本 skill 不含任何账号、邮箱、token 等个人凭据，均由执行者当场提供；这些只存在各自本机记忆里。

## 初次使用准备（首次必做，缺一不可）

第一次在某仓库/某会话执行前，先确认并向用户索取以下两项，缺失则停下来让用户填写或授权：

1. **提交身份（commit author）**：检查目标仓库 local 身份
   ```bash
   git -C <repo> config --local user.email
   ```
   若为空或与用户的 sourcecode 账号不符，提示用户给出其姓名/邮箱后设置（注意：全局身份可能是别的账号，会被继承盖错，必须在本仓库 local 覆盖）：
   ```bash
   git -C <repo> config --local user.name  "<用户提供的名字>"
   git -C <repo> config --local user.email "<用户提供的邮箱>"
   ```
2. **Jenkins 凭据**：向用户索取其 Jenkins **登录用户 id**（注意是用户 id，不是邮箱；带域名可能 500）和 **API token**，或让用户用 `! <命令>` 自行运行带凭据的 curl。凭据仅在本次会话内存使用，不写盘、不写入 skill。

两项就绪后再进入下面的步骤。

## 认证（每次都要用户提供，不硬编码）

- **Jenkins**：`https://nextci.mingdao.net/`，basic-auth 用 `<JENKINS_USER>:<TOKEN>`，由用户提供。
- **HAP 数据连接固定使用 `hap-cli`**：本 SOP 的 HAP 查询、创建、回读和核验一律使用 `hap-cli`，不要在 `hap-cli` 可用时切换到 HAP MCP。
  1. 先运行 `hap auth whoami` 或 `hap --profile <profile> auth whoami --json` 确认当前 HAP 登录态、账号、组织和环境。若未安装 `hap`、未登录、当前账号/环境不对，先引导用户执行 `hap auth login`、`hap auth accounts`、`hap auth use <profile>` 或 `hap auth set-current-org <ORG_ID>`。
  2. 使用 `hap-cli` 读写 HAP 工作表时，脚本化场景必须加 `--json`，并在写入前确认当前应用：`hap app select 86892856-1fb7-4cee-b4a9-36caa9e8798a`。可用 profile 时所有命令都带 `--profile <profile>`。
  3. `record create` 支持 `-a/--app-id`，但发布记录创建前仍必须先执行 `hap app select 86892856-1fb7-4cee-b4a9-36caa9e8798a`，避免默认应用为空或指错应用。`record get` 不支持 `--use-field-id-as-key`，回读时直接读取原始字段 ID。
  4. Windows 下执行 `hap-cli` 前设置 `PYTHONIOENCODING=utf-8`；JSON 输出保存到 UTF-8 文件后再解析，避免中文响应被 GBK 破坏。不要根据乱码、空输出或控制台编码异常直接判断请求失败。
  5. 如果 `hap auth whoami` 报 token 缺失、无效或过期，停止 HAP 操作并让用户重新执行 `hap auth login`（推荐 PAT）；重新登录成功并核对账号、组织、环境后再继续。不要切到 HAP MCP，也不要把 token 打印到日志。
  6. 禁止把 HAP MCP 作为发布记录读写 fallback。只有用户明确要求改用 MCP，或本机没有 `hap-cli` 且用户确认允许改用 MCP 时，才使用 HAP MCP；否则应停止并报告 `hap-cli` 阻塞原因。

## 步骤

### 项目、分支、Jenkins job 与 HAP 服务映射

发布 `hc` 和 `ophc` 必须严格使用下表映射，不能互换项目、分支、Jenkins job 或 HAP 服务记录：

| 发布目标 | 代码项目 / branch | Jenkins job | HAP「更新的服务」记录 |
|---|---|---|---|
| `hc` | `Document` / `origin/dev` | `https://nextci.mingdao.net/job/document/`（job：`document`） | `hc-private`，service rowId：`ab28007a-36e1-4d2d-8e1f-6fb17ca28e92` |
| `ophc` | `Document-ops` / `origin/master` | `https://nextci.mingdao.net/job/document-ops/`（job：`document-ops`） | `ophc-private`，service rowId：`3bf1c547-1479-4723-bcad-4c00c5e8589b` |

HAP 服务表 `5dd7b13a44d0ca000162e790` 中，`hc-private` 对应源码仓库 `https://sourcecode.mingdao.net/private/Document`、镜像仓库 `hub.mingdao.com/private/hc`；`ophc-private` 对应源码仓库 `https://sourcecode.mingdao.net/private/Document-ops`、镜像仓库 `hub.mingdao.com/private/ophc`。创建申请时服务关联字段 `5e22b0e044a07d00010e102d` 传上表对应的 service rowId。

每次触发前仍需核实本次项目 remote/branch、Jenkins job API 的规范 URL/SCM/参数以及目标 HAP 服务记录。构建后必须检查本次 `BRANCH` 和镜像仓库与上表完全一致。不一致或无法核实时停止，不得尝试另一 job/branch，也不得创建 HAP 记录。

### 1. 触发 Jenkins 构建
前置：代码已推送到映射表指定项目和分支。当前工作目录不一定是目标项目，必须先核对 `git remote` 和 branch。
```bash
CRUMB=$(curl -s -u "$JENKINS_USER:$TOKEN" "https://nextci.mingdao.net/crumbIssuer/api/json" | grep -o '"crumb":"[^"]*"' | cut -d'"' -f4)
curl -u "$JENKINS_USER:$TOKEN" -H "Jenkins-Crumb: $CRUMB" -X POST \
  "https://nextci.mingdao.net/job/document/buildWithParameters?BRANCH=origin/dev"
# For ophc, use: https://nextci.mingdao.net/job/document-ops/buildWithParameters?BRANCH=origin/master
```
crumb endpoint 位于 Jenkins 根路径，不能拼在 job URL 后。保存 POST 响应的 `Location` queue URL，轮询该 queue item，直到返回 `executable.url` 和构建编号；后续只使用这个精确的 build URL，不要用 `lastBuild` 猜测编号或拼接 job 路径。若 API 返回 404，先用 Jenkins 根 jobs API 和 job API 核对规范 URL，禁止因为路径不确定而重复触发构建。

Windows 下若用 `curl` 查询带 `{}` 的 Jenkins `tree` 参数，必须加 `--globoff`；curl JSON 不要直接交给 PowerShell 默认编码的 `ConvertFrom-Json`，保存为 UTF-8 后用 Node/Python 解析。响应为空、非 JSON 或编码损坏时先报告查询异常，不要据此重触发构建。

Jenkins `consoleText` 可能包含通知 token、Authorization header 或其它凭据。不得打印/转发整段控制台日志，也不得回显包含 `access_token`、`token`、`password`、`Authorization` 等字段的原始行；只抽取必要的构建结束标志、revision 和镜像地址。发现日志暴露凭据时，停止传播该值并提醒凭据管理员轮换。

### 2. 校验构建结果并从控制台尾部取值
- 以 Jenkins 构建 API 为主判定：`building=false` 且 `result=SUCCESS`。
- 控制台日志还必须出现 `Finished: SUCCESS`，并能提取出目标服务的镜像串；两项缺一不可。若 Jenkins API 成功但日志缺少结束标识或镜像串，停止后报告异常，不要创建发布记录。
- `{"success":true}` 不是所有 Job 都会输出，不再作为必需条件；如日志中出现则记录为附加成功信号。`error_code:1` 仅表示发消息接口返回，与 Jenkins 构建结果无关。
- 镜像串形如 `hub.mingdao.com/private/<svc>:<tag>`，按**最后一个冒号**切：服务=`<svc>`、版本号=`<tag>`（YYYYMMDD_HHMM）。同时确认 `<svc>` 与本次发布目标一致，避免把其它服务的镜像写入发布记录。
- 更新说明优先取本次构建对应 Git 提交的 subject：`git log -1 --format=%s <revision>`；若构建 revision 与本地一致可使用 `git log -1 --format=%s HEAD`。清理首尾空白、句末标点和 `feat:`、`fix:`、`docs:`、`refactor:` 等约定式前缀，保留简洁明确的业务描述，建议不超过 80 个字符。提交标题不可用或过于笼统时，才回退为 `V<版本> bugfix`。

### 3. 写微服务工作表（固定使用 `hap-cli`）
appId `86892856-1fb7-4cee-b4a9-36caa9e8798a`，worksheet `5ba9e096ca6edd0001c9d4da`。

#### HAP 工具选择

1. **固定 `hap-cli`**：
   - 认证：`hap auth whoami`。
   - 查询版本/记录：优先用 `hap --json worksheet record list <worksheetId>`，复杂筛选用 `--filter-json`，视图用对应 view 参数；具体参数以 `hap worksheet record list --help` 为准。
   - 使用 `--table-view` 查询版本规划时，返回通常是 `data.rows` 分组；每个分组的 `rows` 可能是 JSON 字符串数组。必须先展开分组并逐条解析，再按状态 key `1000000` 过滤和比较语义版本，不能把 `data` 直接当作记录数组。
   - 创建前先设置默认应用：`hap app select 86892856-1fb7-4cee-b4a9-36caa9e8798a`。
   - 创建记录优先用多组 `-f CONTROL_ID=VALUE`，避免 Windows PowerShell 中 `--fields-json` 被引号转义破坏。关联记录、成员、单选/多选字段用单个 key/rowid/accountId 传给 `-f` 即可，由 `hap-cli` 按字段类型转换；不要把数组字段降级为逗号拼接字符串。
   - 如必须使用 `--fields-json`，不要在 PowerShell 中手写复杂 JSON 参数；应先用可靠方式生成 JSON 并确认传入 CLI 的是合法 JSON。遇到 `--fields-json is not valid JSON` 时，优先改用 `-f`，不要改业务字段值。
   - 若创建返回 `The record was not saved — the form refuses the write`，先依据错误确认是表单规则拦截，而非字段只读、权限或数据校验失败。只有确认属于表单规则拦截、且用户已确认的业务字段完全不变时，才可追加 `--ignore-rules` 重试；不得用它绕过只读/权限控制。特别是“操作人”`5ba9e13b442bf3b958fa9ed3` 为只读隐藏字段，不得强行写入；“服务更新状态”`5bac8d88442bf3b070e3436a` 不得在创建时设为“已更新”。若无法确认拦截类型则停止并报告。
   - `record get` 回读不要带 `--use-field-id-as-key`；该参数是 `record list` 的参数，`record get` 会报 `No such option '--use-field-id-as-key'`。
   - 创建结果以返回的 `data.rowid` 为准；即使顶层 `resultCode` 或 `error_code` 显示为 `1`，只要有 `data.rowid` 且没有错误对象，就保存该 rowid 继续回读，不要误判为创建失败。
2. **不使用 HAP MCP**：
   - 本 SOP 不把 HAP MCP 作为自动 fallback。若 `hap-cli` 无法继续，停止并把 `hap-cli` 的错误和下一步建议报告给用户。

#### 创建前强制约束

执行 `hap-cli record create` 前必须先完成以下动作，缺一不可：

1. **自动获取版本**：若用户未明确指定版本号，先查询版本规划工作表 `5cc5907771f24d00018030f7`，必须带 viewId `5cc5907771f24d00018030f8`。只从状态为“已发布”的记录中取值（状态字段 `625f9219414f3f9418a5564e`，已发布 key `1000000`），按标题字段 `5cc590776f3c6e0001e9b2d4` 的语义版本号比较（如 `V12.3.0` > `V12.2.0`），不要只按创建时间判断。若查询结果不唯一、标题无法解析或无法判断最新版本，停止并让用户确认版本。
2. **自动获取操作人**：优先从 `hap auth whoami --json` 或 `hap --json auth whoami` 的输出获取当前 HAP `accountId` 和姓名；若本机 `hap-cli` 不支持 JSON 输出，则用 `hap auth whoami` 人工核对当前账号，并通过 HAP 查询当前用户信息获取 accountId。写入字段 `5ba9e13b442bf3b958fa9ed3`。
3. **打印待创建参数**：把完整待创建参数打印给用户确认。使用 `hap-cli` 时打印最终命令和字段 JSON/字段清单。至少包含 `appId`、`worksheet_id`、是否触发 workflow、全部 `fields` 的字段 ID、字段名说明和值。
4. **等待明确确认**：只有用户明确回复“确认创建”“确认”“可以创建”等同意语义后，才能实际创建记录。用户只是补充参数、修改版本、询问或发测试内容时，禁止创建。
5. **确认后不再改业务参数**：确认后如遇到 CLI 参数格式、表单规则、编码或回读参数问题，只能调整 `hap-cli` 调用方式（如 `--fields-json` 改 `-f`、在确认属于表单规则拦截时追加 `--ignore-rules`、去掉不支持的回读参数），不得修改已确认的服务、版本、镜像 tag、操作人、环境、说明等业务内容；如确需修改业务内容，必须重新打印参数并再次等待确认。`--ignore-rules` 不得绕过只读或权限控制。

| 字段 | ID | 类型/表单要求 | 取值 |
|---|---|---|---|
| 更新的服务 | `5e22b0e044a07d00010e102d` | Relation，必填 | `hc`→`hc-private` (`ab28007a-36e1-4d2d-8e1f-6fb17ca28e92`)，`ophc`→`ophc-private` (`3bf1c547-1479-4723-bcad-4c00c5e8589b`)；传服务表 rowId，不用显示名代替。其它服务实时查服务表 `5dd7b13a44d0ca000162e790` |
| 服务版本号 | `5bbef4c8442bf3ca1009e7f6` | Text，必填 | Jenkins 本次构建镜像的 tag，不是语义版本 |
| 更新环境 | `5ba9e0d4442bf3b958fa9eab` | MultipleSelect，可选；传 option key | `100`=沙盒，`1`=梅花，`10`=生产，`1000`=沙盒2。只用未删除选项；生产与其它环境分开申请，生产不会自动更新 |
| 集群 | `617fc605a0673108fbc4ed66` | MultipleSelect，必填；传 option key | `4a43d6aa-623a-40e0-ad8b-25d2d0f8f306`=默认，`3a0cd7b6-95fa-418c-8c85-d22c3e0fd58b`=Nocoly，`2b4278bb-3459-47da-9e7c-9b5df97b4928`=代码块，`f0768f3c-db0a-4f3b-874e-566fbd195fa9`=消费，`756396e9-dde9-4380-bd3b-4c7020d2e0d0`=弹性集群（UK8S），`c081acef-c1d2-4ac6-91e9-c976a0bb1caa`=社区BBS专用环境。按字段描述匹配目标环境；hc/ophc 历史记录使用“默认” |
| 紧急程度 | `5da7fde89da28200014ce5fb` | Rating，必填 | 用户指定 1-5，传字符串如 `"3"`；预览中展示星级含义 |
| 配置 | `5bbee773442bf3ca1009e510` | SingleSelect，必填；传 option key | `10`=否，`1`=是；默认 `10`（否） |
| Redis/Kafka | `62a7f157fe536211a3ab871b` | SingleSelect，必填；传 option key | `10`=否，`1`=是；默认 `10`（否） |
| 版本 | `5e2298bd681ea5000146c199` | Relation，必填 | 用户给版本号→查版本规划 `5cc5907771f24d00018030f7` 取 rowId；用户未给版本号→自动取最新已发布版本；**查询必带 viewId `5cc5907771f24d00018030f8`**，否则报 430028；标题字段 `5cc590776f3c6e0001e9b2d4`，命名如 `V12.3.0` |
| 更新说明 | `5c77a4d1442bf213144e35ad` | Text，必填 | 优先使用本次构建对应 Git 提交的简洁 subject；无法取得时回退 `V<版本> bugfix` |
| 操作人 | `5ba9e13b442bf3b958fa9ed3` | Collaborator；只读、创建表单隐藏 | 从 `hap-cli whoami` 获取当前账号 accountId。若通过 CLI 赋值，创建后必须回读确认；若 API 拒绝只读字段，停止报告，不得用 `--ignore-rules` 绕过字段权限 |
| 服务更新状态 | `5bac8d88442bf3b070e3436a` | SingleSelect；schema 必填、创建表单隐藏 | 有效 option：`1`=未更新、`10`=已更新、`0d98ed9a-5100-4b01-a499-5ffc6e71d8a0`=已废弃。不要在创建申请时预设“已更新”；由表单默认/工作流维护并在创建后回读 |

**常用默认值**（用户不另行说明时以此为准，执行者可按各自约定调整）：
| 字段 | ID | 默认 |
|---|---|---|
| hc/ophc 集群 | `617fc605a0673108fbc4ed66` | 默认（key `4a43d6aa-623a-40e0-ad8b-25d2d0f8f306`）；若用户指定其它环境，以用户选择为准 |
| hc/ophc 更新环境 | `5ba9e0d4442bf3b958fa9eab` | 生产（key `10`），基于近期已完成记录；预览时明确展示并允许用户改选 |
| 配置 | `5bbee773442bf3ca1009e510` | 否（key `10`） |
| Redis/Kafka | `62a7f157fe536211a3ab871b` | 否（key `10`） |
| 服务更新状态 | `5bac8d88442bf3b070e3436a` | 不作为普通创建表单输入；不得将“已更新”（key `10`）设成创建默认值 |

**表单传值规则**：单选/多选用当前 schema 的 option key，不用显示文字；Relation 用目标记录 rowId；Collaborator 用 accountId；Rating 用 1-5 字符串。多选按 hap-cli 对字段类型的数组/重复 `-f` 约定传值，禁止逗号拼接。执行发布前用 `hap worksheet fields <worksheetId>` 核对实时 schema；若 option key 或隐藏/只读标记与本表不同，以 live schema 为准并先停止更新本 skill，不得尝试旧 key。

`triggerWorkflow=true`（走镜像 Tag 预检 + 后续发布流程）。这是**真实生产更新申请**，建成功后工作流/运维据此操作生产，执行前向用户确认无误。

### 4. 读回核验（固定使用 `hap-cli worksheet record get`）
创建成功后立即保存 rowid 并回读一次，核对服务、版本、镜像标签、更新说明、环境和操作人。随后以 20 秒间隔轮询，最多等待 3 分钟，检查：「服务更新状态」是否为“已更新”、对应环境字段（如「公网更新」）是否为“更新成功”、流程状态是否有审批挂起。

如果等待命令超时、返回空输出或只显示工具层错误，不要创建第二条记录；直接用已保存的 worksheet ID + rowid 重新执行 `record get`。只有明确读到失败状态或超过上限仍未完成，才报告工作流异常。
