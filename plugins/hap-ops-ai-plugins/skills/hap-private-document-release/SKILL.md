---
name: hap-private-document-release
description: HAP Private Document 更新发布 SOP（标准流程）。从 Jenkins 构建到写入「研发管理-发布-微服务」工作表并核验的端到端发布流程。触发：用户提到“发布微服务”“更新 hc/ophc”“HAP Private Document 更新”“触发 document 构建并上线”“按发布 SOP 走”“走标准发布流程”等。涉及提交身份、Jenkins 用户名/token 等认证信息时，一律提示用户当场授权或输入，绝不硬编码。
---

# HAP Private Document 更新发布 SOP（标准流程）

Jenkins 构建 → 取镜像值 → 写入「研发管理 → 发布 → 微服务」工作表 → 工作流自动发布 → 读回核验。

> 本 skill 不含任何账号、邮箱、token 等个人凭据。凭据必须由执行者当场提供，仅在本次会话内存使用，不写入 skill 或仓库。

## 初次使用准备

第一次在某仓库或某会话执行前，必须确认以下两项：

1. 提交身份：检查 `git -C <repo> config --local user.email`。若为空或不正确，先让用户提供姓名和邮箱，再设置仓库级 `user.name` 和 `user.email`。
2. Jenkins 登录用户 id 和 API token。注意使用用户 id，不使用邮箱；凭据缺失时停止并让用户输入或授权。

## 认证与工具选择

- Jenkins 地址：`https://nextci.mingdao.net/`，使用用户当场提供的 `<JENKINS_USER>:<TOKEN>`。
- HAP 数据连接优先使用 `hap-cli`，其次才回退 HAP MCP。
- 先运行 `hap auth whoami` 确认当前账号、组织和环境；异常时先引导用户登录或切换环境。
- 脚本化 `hap-cli` 命令必须使用 `--json`；写入前设置默认应用：`hap app select 86892856-1fb7-4cee-b4a9-36caa9e8798a`。
- `record create/update/delete` 不接收 `--app-id`，依赖默认应用；`record list/get` 可显式传 `--app-id`。
- 只有 `hap-cli` 不可用、登录失败、权限不足或无法可靠处理字段格式时，才回退 HAP MCP。
- MCP 返回 `10001 Http Headers verification failed` 时，按本机 reauth → 重启 mcp-remote → `/reload-plugins` 流程处理；无该流程时提示用户执行 `/hap-mcp:setup`。

## 发布步骤

### 1. 触发 Jenkins 构建

前置条件：代码已推送目标分支；HAP_Document 远端使用 `sourcecode.mingdao.net`。

```bash
CRUMB=$(curl -s -u "$JENKINS_USER:$TOKEN" "https://nextci.mingdao.net/crumbIssuer/api/json" | grep -o '"crumb":"[^"]*"' | cut -d'"' -f4)
curl -u "$JENKINS_USER:$TOKEN" -H "Jenkins-Crumb: $CRUMB" -X POST \
  "https://nextci.mingdao.net/job/<job>/buildWithParameters?BRANCH=origin/<branch>"
```

`BRANCH` 必须带 `origin/` 前缀。轮询 `/job/<job>/lastBuild/api/json`，直到 `building:false` 且 `result:SUCCESS`。

### 2. 从控制台尾部取值

- 末尾出现 `{"success":true}` 才算构建成功；`error_code:1` 是发消息接口返回，不代表构建失败。
- 镜像串形如 `hub.mingdao.com/private/<svc>:<tag>`，按最后一个冒号切分：服务为 `<svc>`，版本号为 `<tag>`。

### 3. 写入微服务工作表

优先使用 `hap-cli`，其次使用 HAP MCP。

- appId：`86892856-1fb7-4cee-b4a9-36caa9e8798a`
- worksheet：`5ba9e096ca6edd0001c9d4da`

#### 创建前强制约束

执行 `record create` 或 MCP `create_record` 前，缺一不可：

1. 若用户未指定版本，查询版本规划工作表 `5cc5907771f24d00018030f7`，必须带 viewId `5cc5907771f24d00018030f8`；只取状态为“已发布”的记录，按语义版本号比较。
2. 获取当前 HAP 操作人 accountId；优先从 `hap auth whoami --json` 获取，回退 MCP 时再使用 `get_current_user` 或本机账号文件。
3. 打印完整待创建参数，包含 appId、worksheet、triggerWorkflow 及全部字段 ID、名称和值。
4. 必须等待用户明确回复“确认创建”“确认”或“可以创建”等同意语义后，才能真实创建记录。

#### 字段映射

| 字段 | ID | 取值 |
|---|---|---|
| 更新的服务（关联） | `5e22b0e044a07d00010e102d` | `/hc`→hc-private（`ab28007a-36e1-4d2d-8e1f-6fb17ca28e92`），`/ophc`→ophc-private（`3bf1c547-1479-4723-bcad-4c00c5e8589b`）；其他服务先查询服务列表 `5dd7b13a44d0ca000162e790` |
| 服务版本号 | `5bbef4c8442bf3ca1009e7f6` | Jenkins 镜像 tag |
| 更新环境（多选） | `5ba9e0d4442bf3b958fa9eab` | 用户指定：生产/梅花/沙盒/沙盒2，传选项值数组 |
| 紧急程度（评分） | `5da7fde89da28200014ce5fb` | 用户指定 1-5，传字符串 |
| 版本（关联） | `5e2298bd681ea5000146c199` | 从版本规划工作表查询 rowId，不能硬编码旧版本 |
| 更新说明 | `5c77a4d1442bf213144e35ad` | 默认 `<动态版本名> bugfix` |
| 操作人（协作人） | `5ba9e13b442bf3b958fa9ed3` | 当前 HAP accountId 数组 |

常用默认值：

| 字段 | ID | 默认 |
|---|---|---|
| 集群（多选） | `617fc605a0673108fbc4ed66` | 默认 |
| 配置（单选） | `5bbee773442bf3ca1009e510` | 否 |
| Redis/Kafka（单选） | `62a7f157fe536211a3ab871b` | 否 |
| 服务更新状态（单选） | `5bac8d88442bf3b070e3436a` | 未更新 |

写入时使用 `triggerWorkflow=true`，因为这是真实生产更新申请，创建前必须完成参数确认。

### 4. 读回核验

使用 `get_record_details`（参数名为 `row_id`）检查：

- 「服务更新状态」是否被工作流改写为“已更新”；
- 对应环境字段是否为“更新成功”；
- `_processStatus` 是否存在审批挂起。

hc/ophc 这类 nginx 文档站预检通过后通常可自动更新；若长时间未完成，继续检查流程节点。
