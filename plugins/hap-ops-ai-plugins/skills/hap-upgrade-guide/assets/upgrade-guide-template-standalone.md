# HAP 升级指南（单机模式）

| 项目 | 内容 |
|------|------|
| **升级路径** | `{当前版本}` → `{目标版本}` |
| **当前版本发布日期** | {YYYY-MM-DD} |
| **目标版本发布日期** | **{YYYY-MM-DD}** ⚠️ |
| **部署模式** | 单机模式（Docker Compose） |
| **服务器架构** | {AMD64 / ARM64} |
| **服务器网络** | {可访问互联网 / 离线} |
<!-- 仅当用户明确指定的关系型数据库不是 MySQL 时保留此行；同时在正文保留数据库类型说明。 -->
| **关系型数据库** | {OceanBase / 达梦 / 人大金仓} |
| **文档生成日期** | {YYYY-MM-DD} |

<!-- 只填写 /version 总表中标记“含附加操作”的版本；未标记版本不列入正文。 -->
本次升级正文仅展示标记“含附加操作”的版本：{按 /version 总表从低到高填写动作版本}；其他版本不展示，也不增加额外操作。

<!-- 仅当关系型数据库不是 MySQL 时保留此说明，并将数据库类型替换为现场实际类型。 -->
> ⚠️ **数据库类型说明**：本文档的关系型数据库 DDL 变更操作针对 **{数据库类型}** 数据库，非 MySQL 默认语法。请使用对应的数据库客户端工具执行。

---

### 提前准备

> **建议在正式开始升级操作前，提前准备本次升级实际会用到的全部资源。**
> 资源不限于 HAP 微服务镜像；若附加操作涉及存储组件、文档预览、预置数据、离线脚本或其他组件资源，也必须在此节一并整理。

### 若服务器可访问互联网

保留本小节时，删除下方“若服务器离线”小节。

在服务器上提前获取本次升级实际需要的镜像或资源。例如：

```bash
# HAP 微服务镜像
docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{目标版本号}

# 如本次升级步骤实际需要存储组件镜像，则继续拉取对应镜像
# docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-sc:{目标存储组件版本号}
```

> 若线上文档显示还需要文档预览、预置数据脚本、额外服务镜像或其他资源，必须在本节继续补全，不得只保留微服务镜像。

### 若服务器离线

保留本小节时，删除上方"若服务器可访问互联网"小节。

请在**可访问互联网的机器上**提前下载本次升级实际需要的全部离线文件，并上传到服务器：

| 文件 | 下载链接 |
|------|----------|
| HAP 微服务离线包（按架构保留） | `{按实际架构填写 HAP 微服务离线包链接}` |
| 存储组件离线包（若本次升级涉及，否则删除此行） | `{按实际架构和版本填写，例如 AMD64: https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-sc-linux-amd64-{版本}.tar.gz}` |
<!-- 以下行仅在本次升级路径中至少一个版本的升级详情页明确要求对应组件升级时才取消注释并填写：
| 文档预览服务离线包 | 见 SKILL.md §4 下载地址规范 |
| 文档预览扩展服务（ldoc）离线包 | 见 SKILL.md §4 下载地址规范 |
-->
| MongoDB 预置数据包（若本次升级涉及该操作，否则删除此行） | `{填写对应版本下载链接，例如 https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_{版本}.tar.gz}` |
| MongoDB 预置脚本（若本次升级涉及该操作，否则删除此行） | `{填写对应脚本下载链接，例如 https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_docker.sh}` |
| 外部文件对象存储预置文件包（仅外部 S3/OSS/COS/OBS 时执行；若本次升级不涉及则删除此行） | https://pdpublic.mingdao.com/private-deployment/source/{含fileInit的最高版本号}/file_init.tar.gz |

上传到服务器后，按实际需要导入或校验资源。例如：

```bash
# 作用：将提前上传的目标版本 HAP 离线镜像导入本机 Docker 镜像仓库，供后续升级使用
docker load -i {目标HAP微服务离线包文件名}.tar.gz

# 作用：确认目标版本镜像已成功导入
docker images
```

> 💡 **关于预置文件（fileInit）**：若您的部署使用**外部文件对象存储**（S3 标准协议，如阿里云 OSS、AWS S3 等），还需重新初始化预置文件。离线环境下请提前下载预置文件包 `file_init.tar.gz`（下载链接见“提前准备”），并参考官方文档 [自定义文件对象存储](https://docs-pd.mingdao.com/hap/faq/oss) 完成操作。若使用内置文件存储或 MinIO，无需此步骤。

---

## 升级前准备

### 1. 授权有效期检查

> ⚠️ **重要提示**：请确保您的授权密钥仍在"升级服务"有效期内。若目标版本（**{与上方「目标版本发布日期」一致，如 v7.3.6 的 2026-07-02}**）晚于授权到期日，强行升级将触发系统受限提示，并导致授权自动降级为免费版。建议在升级前确认版本发布日期与授权期限的匹配情况。

请检查您的授权密钥是否仍在"升级服务"有效期内，并确认授权到期日晚于目标版本发布日期。若授权即将到期或已过期，请联系明道云商务团队续期后再执行升级。

### 2. 前端二次开发注意事项

> ⚠️ **注意**：如有前端二次开发，请联系前端二开负责同事确认此操作已完成，否则可能导致升级后前端功能异常。

若系统中存在前端二次开发（即有基于 HAP 前端源码进行过定制开发），升级后前端代码可能与新版本存在差异，需要**前端二开负责同事**执行以下操作：

1. 拉取最新的前端二开基础代码（官方前端仓库对应目标版本的分支或 tag）
2. 将自定义的二开代码合并（merge）进最新基础代码，处理可能存在的冲突
3. 构建并发布更新后的前端服务，使新版本前端生效

若系统中**没有**前端二次开发，忽略本注意事项。

### 3. 数据备份

> ⚠️ **升级前必须完成备份，此步骤不可跳过。**

请参考官方文档完成数据备份：[数据备份文档](https://docs-pd.mingdao.com/hap/deployment/docker-compose/standalone/data/backup)

### 4. 确认当前版本

执行以下命令确认当前运行版本与本文档起始版本一致：

```bash
docker ps --format "table {{.Image}}\t{{.Names}}"
```

### 5. 检查资源

- 确保磁盘空间充足（建议预留 40GB 以上）

<!-- 离线时保留以下三项；在线时删除以下三项。该条件说明不得输出到最终文档。 -->

- 确认目标 HAP 离线镜像已经通过 `docker images` 校验
- 确认 `preset_mongodb_docker.sh` 与 `preset_mongodb_{对应版本}.tar.gz` 已上传到服务器同一目录
- 确认已安排升级窗口，升级过程中不要在 HAP 服务上执行其他变更

建议在升级前记录以下现场信息，便于出现异常时与升级前状态对比：

- 当前 HAP、存储组件、{关系型数据库名称}、MongoDB 等容器名称和状态
- 当前 `docker-compose.yaml` 中 HAP 镜像标签、数据目录挂载和外部代理相关配置
- 当前系统登录地址、组织授权状态以及前端二次开发发布状态
- 备份文件的实际保存位置、文件名和完整性校验结果

执行操作时，所有默认路径都必须以现场实际配置为准。除 MongoDB 认证建库和预置数据更新外，本次升级不要先停止原版本服务，如果某一步命令报错，应保留错误输出，先完成原因判断，再决定是否继续。

---

## 升级步骤

### 第一阶段：HAP 微服务升级前操作

{若无操作则删除本节}

#### 1. 来自 v{版本号}：替换镜像名称 ⚠️

> 💡 以下命令按默认路径编写。若曾自定义安装路径，请先替换路径再执行。
> - `docker-compose.yaml` 默认路径：`/data/mingdao/script/`
> - `service.sh` 默认路径：`/usr/local/MDPrivateDeployment/`
> - `run.sh` 默认路径：`/data/mingdao/script/`

```bash
# 替换 docker-compose.yaml 中的镜像名
sed -i -e 's/mingdaoyun-community/mingdaoyun-hap/g' /data/mingdao/script/docker-compose.yaml

# 替换 service.sh 中的服务名称
sed -i -e 's/Community/Hap/g' -e 's/community/hap/g' /usr/local/MDPrivateDeployment/service.sh

# 替换 run.sh 中的镜像名（如文件存在）
if [ -f /data/mingdao/script/run.sh ]; then
  sed -i -e 's/mingdaoyun-community/mingdaoyun-hap/g' /data/mingdao/script/run.sh
fi
```

#### 2. 来自 v{版本号}：创建 MongoDB 数据库（仅开启 MongoDB 认证时执行）

> 单机模式下 MongoDB 默认未开启认证，仅在自定义过开启 MongoDB 连接认证的情况下执行此步骤

1. 进入存储组件容器：

```bash
docker exec -it $(docker ps | grep mingdaoyun-sc | awk '{print $1}') bash
```

2. 在容器内，使用含 `admin` 角色的用户登录 MongoDB（将 `用户名` 和 `密码` 替换为实际信息）：

```bash
mongo -u 用户名 -p 密码 --authenticationDatabase admin
```

3. 依次为以下各库执行创建命令（将 `用户名` 和 `密码` 替换为与其他库一致的认证信息）：

**创建 `{库名1}` 库**（{vX.X.X} 要求）

```javascript
use {库名1}
db.createUser({ user: "用户名", pwd: "密码", roles: [{ role: "readWrite", db: "{库名1}" }] })
```

**创建 `{库名2}` 库**（{vX.X.X} 要求）

```javascript
use {库名2}
db.createUser({ user: "用户名", pwd: "密码", roles: [{ role: "readWrite", db: "{库名2}" }] })
```

#### 3. 来自 v{版本号}：存储组件升级

{若跨越多个含存储组件升级的版本，直接升级到所有版本中要求的最高版本号。}

<!-- ARM64 架构提示：当架构为 ARM64 时，存储组件镜像名使用 -arm64 后缀
     （如 mingdaoyun-sc-arm64）。架构校验已通过即代表所有镜像均有 ARM64 版本，无需添加可用性警告。AMD64 架构时删除此注释块。 -->

1. 修改 `/data/mingdao/script/docker-compose.yaml` 中存储组件的镜像版本号为 `{目标存储组件版本号}`

>  如果存储组件与 HAP 微服务同时升级，可在修改完两处版本号后，最后只执行一次 `restartall`，无需分开重启。

#### 4. 来自 v{版本号}：MongoDB 预置数据更新

> 此操作在**原版本服务运行状态下**执行，无需停机。

若服务器可访问互联网，保留以下代码块并删除后面的离线代码块：

```bash
bash -c "$(curl -fsSL https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_docker.sh)" -s {该操作涉及的最新版本号}
```

若服务器离线，保留以下代码块并删除前面的联网代码块：

```bash
# 将提前下载好的 preset_mongodb_docker.sh 和 preset_mongodb_{该操作涉及的最新版本号}.tar.gz 上传至服务器同一目录下后执行
bash ./preset_mongodb_docker.sh {该操作涉及的最新版本号} ./preset_mongodb_{该操作涉及的最新版本号}.tar.gz
```

---

### 第二阶段：升级微服务

#### 1. 修改镜像版本号

编辑 `/data/mingdao/script/docker-compose.yaml`，将 HAP 镜像版本号修改为目标版本，并确保 `ENV_APP_VERSION` 环境变量的值与微服务镜像版本号保持一致：

```yaml
# 修改前
image: registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{当前版本号}
environment:
  ENV_APP_VERSION: "{当前版本号}"

# 修改后
image: registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{目标版本号}
environment:
  ENV_APP_VERSION: "{目标版本号}"
```

> 💡 **重要说明**：`ENV_APP_VERSION` 环境变量的值必须与微服务镜像版本号保持一致（例如：微服务版本是 7.1.1，`ENV_APP_VERSION` 的值也应设为 7.1.1），否则可能导致系统功能异常。

#### 2. 重启服务

在管理器根目录下执行（通常在 `/usr/local/MDPrivateDeployment/`，以实际为准）：

```bash
bash ./service.sh restartall
```

等待命令执行完成，服务将自动完成升级并重启。

- 如遗忘 `service.sh` 文件所在路径，可使用以下命令查找

  ```text
  find / -path /proc -prune -o -name "service.sh" -print
  ```

---

### 第三阶段：HAP 微服务升级后操作

{仅当本次升级存在官方明确要求在微服务升级完成后执行的变更/附加操作时保留本节；若无此类变更，删除整个本节，包括进入容器步骤。}

> ⚠️ 本阶段只执行升级后的变更或附加操作，不用于确认服务状态、查看日志、确认版本或业务功能验证；这些内容统一放在“升级后验证”。

#### 1. 进入微服务容器执行脚本

进入容器：

```bash
docker exec -it $(docker ps | grep -E 'mingdaoyun-community|mingdaoyun-hap' | awk '{print $1}') bash
```

> 💡 如本文档包含关系型数据库命令，注意将数据库类型、连接地址、端口、租户、用户名和密码替换为现场实际值。

在容器内按版本**从低到高**顺序执行以下操作：

---

<!-- 若本次升级涉及非 MySQL 数据库 DDL（如达梦、金仓等）：
     非 MySQL DDL 不进 HAP 容器执行，需单独编排为独立大步骤，编号顺接。
     格式：#### N. 在{数据库名}数据库中执行 DDL 变更
     内容：数据库连接命令（如 docker exec -it {达梦容器名} disql ... 或 disql {用户}/{密码}@{IP}:5236）+ DDL 代码块
     注意：该步骤中禁止出现 docker exec -it $(docker ps | grep mingdaoyun...) 进入 HAP 容器的命令
-->

#### 2. 来自 v{版本号}：{功能说明，例如：关系型数据库新增索引}

{仅保留实际存在的操作}

<!-- MySQL 分支：仅当关系型数据库为 MySQL，且官方详情明确要求在 HAP 微服务容器内执行时保留；OceanBase/其他非 MySQL 数据库删除此分支。 -->
```bash
{仅 MySQL 场景：从本次官方详情页完整填入命令；非 MySQL 场景删除本代码块}
```

**2.1 执行预置数据脚本**

```bash
source /entrypoint.sh && /init/script/{版本号}/preset.sh
```

**2.2 关系型数据库新增索引（仅 MySQL 容器内分支）**

```bash
{仅 MySQL 场景：从本次官方详情页完整填入命令；非 MySQL 场景删除本代码块}
```

```bash
{仅 MySQL 场景：从本次官方详情页完整填入全部命令；非 MySQL 场景删除本代码块}
```

<!-- 非 MySQL 关系型数据库分支：不得进入 HAP 微服务容器，必须单独编号并在数据库服务器或运维机执行。 -->
#### {N}. 在{数据库类型}数据库中执行 DDL 变更

> ⚠️ **此步骤不在 HAP 微服务容器内执行**。请将连接地址、端口、租户、用户名、密码和数据库名替换为现场实际值。

OceanBase 使用 MySQL 兼容模式的 `obclient`，示例：

```bash
obclient -h {数据库服务器IP} -P {端口} -u "{用户名}@{租户名}" -p"{密码}" -D {数据库名} < {官方SQL文件路径}.sql
```

```sql
{从官方数据库变更 SQL 页面按来源版本从低到高填入对应数据库 DDL；不得用 MySQL DDL 代替}
```

---

#### {N}. 来自 v{版本号}：{功能说明}

---

## 升级后验证

#### 1. 确认服务状态

```bash
docker ps
```

确认所有容器均处于 `Up` 状态，无异常重启。

#### 2. 检查HAP微服务容器日志

```
docker logs $(docker ps | grep -E 'mingdaoyun-community|mingdaoyun-hap' | awk '{print $1}')
```

正常所输出日志应都是 `INFO `级别

#### 3. 登录系统确认版本

登录 HAP 管理后台，确认系统版本号已更新为目标版本 `{目标版本号}`。

#### 4. 功能验证

- [ ] 打开工作表，创建/编辑记录
- [ ] 触发工作流，检查执行情况
- [ ] 检查统计图、报表等功能
- [ ] 检查附件上传、下载和预览功能

## 异常情况排查

参考[服务运行状况检查](https://docs-pd.mingdao.com/hap/faq/troubleshooting/service-status-check)文档对容器日志进行检查

### 1. 容器日志检查

查看微服务应用容器健康检查日志

```text
docker logs $(docker ps -a | grep mingdaoyun-community|mingdaoyun-hap | awk '{print $1}')
```

查看存储组件容器健康检查日志

```text
docker logs $(docker ps -a | grep mingdaoyun-sc | awk '{print $1}')
```

---

## 参考文档

<!-- 始终保留 -->
- [版本发布历史](https://docs-pd.mingdao.com/hap/version)
- [离线资源包](https://docs-pd.mingdao.com/hap/deployment/offline)
- [数据备份](https://docs-pd.mingdao.com/hap/deployment/docker-compose/standalone/data/backup)
- [微服务升级](https://docs-pd.mingdao.com/hap/deployment/docker-compose/standalone/upgrade/hap)
- [常见问题 FAQ](https://docs-pd.mingdao.com/hap/faq/deployment)
<!-- 条件保留（仅当本次升级实际涉及该操作时取消注释）：
- [MongoDB 预置数据更新](https://docs-pd.mingdao.com/hap/deployment/docker-compose/standalone/data/preset/mongodb)
- [存储组件升级](https://docs-pd.mingdao.com/hap/deployment/docker-compose/standalone/upgrade/sc)
-->

---

💡 声明：内容由 AI 生成。尽管已努力确保信息的合理性，但 AI 模型仍可能产生不准确、过时或存在偏差的内容。请在执行关键操作前，务必对照[官方文档](https://docs-pd.mingdao.com)进行核实校验。
