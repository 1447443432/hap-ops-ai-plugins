# HAP 升级指南（集群模式）

| 项目 | 内容 |
|------|------|
| **升级路径** | `{当前版本}` → `{目标版本}` |
| **当前版本发布日期** | {YYYY-MM-DD} |
| **目标版本发布日期** | **{YYYY-MM-DD}** ⚠️ |
| **部署模式** | 集群模式（Kubernetes） |
| **服务器架构** | {AMD64 / ARM64} |
| **服务器网络** | {可访问互联网 / 离线} |
| **文档生成日期** | {YYYY-MM-DD} |

---

## 提前准备

> **建议在正式开始升级操作前，提前在相关节点准备本次升级实际会用到的全部资源。**
> 资源不限于 HAP 微服务镜像；若附加操作涉及文档预览、存储组件、预置数据、离线脚本或新增服务镜像，也必须在此节一并整理。

### 若服务器可访问互联网

保留本小节时，删除下方“若服务器离线”小节。

在**对应节点**上提前获取本次升级实际需要的镜像或资源。例如：

```bash
# HAP 微服务镜像
crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{目标版本号}

# 如本次升级步骤实际需要其他镜像，则继续拉取
# crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-doc:{文档预览版本号}
# crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-ldoc:{文档预览扩展版本号}
# crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-sc:{存储组件版本号}
```

```bash
# 作用：确认目标版本镜像已成功从镜像仓库拉取
crictl images | grep mingdaoyun
```

> 若线上文档显示还需要额外服务镜像、预置数据脚本或其他资源，必须在本节继续补全，不得只保留微服务镜像。

### 若服务器离线

保留本小节时，删除上方"若服务器可访问互联网"小节。

请在**可访问互联网的机器上**提前下载本次升级实际需要的全部离线文件，并上传到对应服务器：

| 文件 | 下载链接 |
|------|----------|
| HAP 微服务离线包（按架构保留） | `{按实际架构填写 HAP 微服务离线包链接}` |
| 存储组件离线包（若本次升级涉及，否则删除此行） | `{按实际架构和版本填写}` |
<!-- 以下行仅在本次升级路径中至少一个版本的升级详情页明确要求对应组件升级时才取消注释并填写：
| 文档预览服务离线包 | 见 SKILL.md §4 下载地址规范 |
| 文档预览扩展服务（ldoc）离线包 | 见 SKILL.md §4 下载地址规范 |
| 文件存储服务离线包（**二选一**，根据当前 file 版本选择） | 见 SKILL.md §5 下载地址规范（必须合并为一行两链接，标注二选一）|
-->
| MongoDB 预置数据包（若本次升级涉及该操作，否则删除此行） | {填写对应版本下载链接，例如 https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_{版本}.tar.gz} |
| MongoDB 预置脚本（若本次升级涉及该操作，否则删除此行） | {填写对应脚本下载链接，例如 https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_k8s.sh} |
| 预置文件（若本次升级涉及 fileInit，离线时需提前下载，否则删除此行） | https://pdpublic.mingdao.com/private-deployment/data/preset_file_{含fileInit的最高版本号}.tar.gz（版本号根据升级路径实际扫描确定，详见 SKILL.md §6） |

在对应节点按实际需要导入或校验资源。例如：

```bash
# 作用：解压并将目标版本 HAP 离线镜像导入 Kubernetes 使用的 containerd 镜像仓库
gunzip -c {目标HAP微服务离线包文件名}.tar.gz | ctr -n k8s.io image import -

# 作用：确认目标版本镜像已成功导入 containerd
crictl images | grep mingdaoyun
```

---

## 升级前准备

<!-- 集群前三项按 WorkBuddy 集群成品固定结构生成；不要套用单机备份链接或单机命令。 -->

### 1. 授权有效期检查

> ⚠️ **重要提示**：请确保您的授权密钥仍在"升级服务"有效期内。若目标版本（**{目标版本发布日期}**）晚于授权到期日，强行升级将触发系统受限提示，并导致授权自动降级为免费版。建议在升级前确认版本发布日期与授权期限的匹配情况。

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

对数据存储相关的服务器进行备份，确保以下组件的数据均已备份：MongoDB、文件存储服务及其他有状态服务。

### 4. 确认当前版本

在控制节点执行以下命令确认当前运行版本：

```bash
kubectl get pods -n default -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[*].image}{'\n'}{end}"
```

> 💡 若未使用默认命名空间，请将命令中的 `default` 替换为实际的命名空间（namespace）。

### 5. 检查资源

- 确认各节点磁盘空间充足
- 确认控制节点可正常执行 `kubectl` 命令
- 若计划使用滚动更新，确认各微服务节点有 **40% 左右的可用内存**（不满足则使用非滚动更新）

---

## 升级步骤

### 第一阶段：HAP 微服务升级前操作

{若无操作则删除本节}

#### 1. 来自 v{版本号}：替换镜像名称 ⚠️

> ⚠️ **特别注意**：此操作必须在 HAP 微服务升级前完成。

> 💡 以下命令按默认路径编写。若曾自定义安装路径，请先替换路径再执行。
> - kubernetes yaml 文件默认路径：`/data/mingdao/script/kubernetes`

在控制节点执行：

```bash
# 替换所有 yaml 文件中的镜像名
sed -i -e 's/mingdaoyun-community/mingdaoyun-hap/g' /data/mingdao/script/kubernetes/*.yaml

# 替换 update.sh 中的服务名称
sed -i -e 's/Community/Hap/g' -e 's/community/hap/g' /data/mingdao/script/kubernetes/update.sh

# 如果存在 run.sh，则同步替换其中的镜像名称
if [ -f /data/mingdao/script/run.sh ]; then
  sed -i -e 's/mingdaoyun-community/mingdaoyun-hap/g' /data/mingdao/script/run.sh
fi
```

#### 2. 来自 v{版本号}：创建 MongoDB 数据库（仅开启 MongoDB 认证时执行）

> 💡 仅在已开启 MongoDB 连接认证的情况下执行此步骤。

登录到 MongoDB 服务器，使用含 `admin` 角色的用户连接（将 `用户名` 和 `密码` 替换为实际信息）：

```bash
mongo -u 用户名 -p 密码 --authenticationDatabase admin
```

依次为以下各库执行创建命令（将 `用户名` 和 `密码` 替换为与其他库一致的认证信息）：

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

> 💡 若所有库使用同一用户认证，则需修改该用户权限以授权新数据库，而非创建新用户。

#### 3. 来自 v{版本号}：更新 service.yaml（删除/新增服务配置）⚠️

{若无操作则删除本节}

> ⚠️ **特别注意**：此操作必须在 HAP 微服务升级前完成。

> 💡 `service.yaml` 默认路径：`/data/mingdao/script/kubernetes/service.yaml`

**第一步：删除已废弃的服务**（若跨越路径中有需要删除的服务，则保留此块；否则删除）

在 `service.yaml` 中找到并删除以下服务配置段（从 `---` 分隔符到下一个 `---` 或文件末尾）：

> 每个版本、每个被删除服务必须单独建立一个附加操作块，并完整展示该服务的 Deployment 和 Service 配置。不得只写“删除 {服务名}”，不得把不同版本的不同服务合并到一个块。

```yaml
# ---- 来自 v{版本号}：删除 {服务名} 服务 ----
# 【AI 填写要求】以下 YAML 配置必须从官网详情页原文完整复制，不得省略任何字段，不得使用省略号占位。
# 若官网页面本身的 YAML 有省略号，需标注"以下配置以官网实际内容为准，执行时请对照 service.yaml 中实际存在的 {服务名} 相关配置删除"。
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {服务名}
  namespace: default
spec:
  replicas: {从官网原文复制}
  selector:
    matchLabels:
      app: {服务名}
  template:
    metadata:
      labels:
        app: {服务名}
    spec:
      containers:
      - name: {服务名}
        image: {从官网原文复制}
        # 完整配置均从官网原文复制
---
apiVersion: v1
kind: Service
metadata:
  name: {服务名}
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: {服务名}
  ports:
  - port: {从官网原文复制}
    targetPort: {从官网原文复制}
    protocol: TCP
```

**第二步：新增服务配置**（若跨越路径中有需要新增的服务，则保留此块；否则删除）

<!-- ARM64 架构提示：当架构为 ARM64 时，YAML 中新增服务的镜像名添加 `-arm64` 后缀
     （如 mingdaoyun-platformapi → mingdaoyun-platformapi-arm64）。
     架构校验已通过即代表所有镜像均有 ARM64 版本，无需添加任何可用性警告。AMD64 架构时删除此注释块。 -->

在 `service.yaml` 末尾追加以下服务配置（**将镜像版本号替换为目标版本 `{目标版本号}`**）：

> 每个版本、每个新增服务必须单独建立一个附加操作块，按版本从低到高排列；非重复服务不得合并。以下 YAML 必须完整复制官方内容，保留全部字段和 `---` 分隔符；每个版本块之间留一个空行。

```yaml
# ---- 来自 v{版本号}：新增 {服务名} 服务 ----
{原文复制官方文档中的 yaml 配置，不得改写，将版本号替换为目标版本号}
---
# ---- 来自 v{版本号}：新增 {服务名} 服务 ----
```

#### 4. 来自 v{版本号}：MongoDB 预置数据更新

> 💡 此操作可在**原版本服务运行状态下**执行，无需停机。
> 以下命令使用默认命名空间 `default`；若未使用默认命名空间，请将 `default` 替换为实际命名空间。

若服务器可访问互联网，保留以下代码块并删除后面的离线代码块：

```bash
bash -c "$(curl -fsSL https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_k8s.sh)" -s {该操作涉及的最新版本号} default
```

若服务器离线，保留以下代码块并删除前面的联网代码块：

```bash
# 将提前下载好的 preset_mongodb_k8s.sh 和 preset_mongodb_{该操作涉及的最新版本号}.tar.gz 上传至控制节点同一目录下后执行
bash ./preset_mongodb_k8s.sh {该操作涉及的最新版本号} default ./preset_mongodb_{该操作涉及的最新版本号}.tar.gz
```

---

### 第二阶段：升级微服务

在控制节点 `/data/mingdao/script/kubernetes` 目录下执行：

#### 1. 滚动更新（推荐，需各节点有 40% 左右可用内存）

```bash
bash update.sh update hap {目标版本号}
```

执行后大约等待 3-5 分钟完成，期间服务基本不中断。

#### 2. 非滚动更新（可用内存不足时使用）

```bash
# 先停止微服务
bash stop.sh

# 通过以下命令确认 HAP Pod 已完全停止，再继续下一步
kubectl get pod -n default

# 执行更新
bash update.sh update hap {目标版本号}
```

验证升级结果：

```bash
kubectl get pod -n default
# 正常情况下各 pod 状态均为 2/2
```

> 💡 若未使用默认命名空间，请将命令中的 `default` 替换为实际的命名空间（namespace）。

---

### 第三阶段：HAP 微服务升级后操作

{若无操作则删除本节}

> ⚠️ **特别注意**：以下操作须在 HAP 微服务升级完成后执行。

#### 1. 进入 config Pod 执行脚本

在控制节点执行以下命令进入 config Pod：

```bash
kubectl exec -it $(kubectl get pod -n default | grep config | awk '{print $1}') -n default -- bash
```

> 💡 若未使用默认命名空间，请将命令中的 `default` 替换为实际的命名空间（namespace）。

进入 Pod 后，按版本**从低到高**顺序依次执行以下各步骤（数字小的版本在前，例如先 v7.2.0，再 v7.2.4，最后 v7.3.0）：

---

<!-- 若本次升级涉及非 MySQL 数据库 DDL（如达梦、金仓等）：
     非 MySQL DDL 不进 config Pod 执行，需单独编排为独立大步骤，编号顺接于 1. 进入 config Pod 之后。
     格式：#### N. 在{数据库名}数据库中执行 DDL 变更
     内容：数据库连接命令（如 disql {用户}/{密码}@{IP}:5236）+ DDL 代码块
     注意：该步骤中禁止出现 kubectl exec 或任何进入 config Pod 的命令
-->

#### 2. 来自 v{版本号}：{功能说明，例如：MongoDB 新增索引}

{仅保留实际存在的操作}
{单子操作不编子号}
{多子操作用子编号}
{同类命令合并到同一代码块}

```bash
source /entrypoint.sh && mongodbExecute {库名1} /init/mongodb/{版本号}/{库名1}/DDL.txt
source /entrypoint.sh && mongodbExecute {库名2} /init/mongodb/{版本号}/{库名2}/DDL.txt
source /entrypoint.sh && mongodbExecute {库名3} /init/mongodb/{版本号}/{库名3}/DDL.txt
```

**2.1 更新预置文件**

首先确认 `mingdaoyun-file` 的当前版本以判断文件存储模式。请**登录到 mingdaoyun-file 所在服务器的 Docker Swarm 控制节点**执行版本检查命令（注意：不是 kubectl 命令，不是 Kubernetes 节点）：

```bash
# 查看 file 服务当前镜像版本
docker service ls | grep file
# 或查看更详细的镜像信息
docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' $(docker service ls --filter name=file -q)
```

根据版本号确认存储模式后，**回到 config Pod**（已在第 1 步进入），**三选一**执行：

**情况 1：内置文件存储（mingdaoyun-file 1.x.x，file v1 模式）**

在 config Pod 内执行：
```bash
source /entrypoint-cluster.sh && fileInit
```

**情况 2：外部 MinIO / S3 标准对象存储（mingdaoyun-file 2.x.x，file v2 模式）**

在 config Pod 内执行：
```bash
source /entrypoint-cluster.sh && s3fileInit
```

**情况 3：外部文件对象存储（S3 标准协议，如阿里云 OSS、AWS S3 等，mingdaoyun-file 2.x.x，file v2 模式）**

> 此情况需手动下载预置文件包并上传到对象存储 bucket 中，请参考官方文档操作：
> [https://docs-pd.mingdao.com/faq/oss](https://docs-pd.mingdao.com/faq/oss)

**2.2 MongoDB 新增索引**

```bash
source /entrypoint.sh && mongodbExecute {库名1} /init/mongodb/{版本号}/{库名1}/DDL.txt
source /entrypoint.sh && mongodbExecute {库名2} /init/mongodb/{版本号}/{库名2}/DDL.txt
```

```bash
mysql -h $ENV_MYSQL_HOST -P $ENV_MYSQL_PORT -u$ENV_MYSQL_USERNAME -p$ENV_MYSQL_PASSWORD --default-character-set=utf8 -N < /init/mysql/{版本号}/DDL.sql
```

---

#### 3. 来自 v{版本号}：{功能说明}


---

#### N. 来自 v{最高版本号}：{功能说明}

---

## 升级后验证

#### 1. 确认服务状态

```bash
kubectl get pods -n default
```

> 💡 若未使用默认命名空间，请将命令中的 `default` 替换为实际的命名空间（namespace）。

确认所有 Pod 均处于 `Running` 状态（正常为 `2/2`），`RESTARTS` 次数无异常增长。

#### 2. 登录系统确认版本

登录 HAP 管理后台，确认系统版本号已更新为目标版本 `{目标版本号}`。

#### 3. 功能验证

- [ ] 打开工作表，创建/编辑记录
- [ ] 触发工作流，检查执行情况
- [ ] 检查统计图、报表等功能

---

## 参考文档

<!-- 始终保留 -->
- [版本发布历史](https://docs-pd.mingdao.com/version)
- [离线资源包](https://docs-pd.mingdao.com/deployment/offline)
- [微服务升级](https://docs-pd.mingdao.com/deployment/kubernetes/upgrade/hap)
- [常见问题 FAQ](https://docs-pd.mingdao.com/faq/deployment)
<!-- 条件保留（仅当本次升级实际涉及该操作时取消注释）：
- [MongoDB 预置数据更新](https://docs-pd.mingdao.com/deployment/kubernetes/data/preset/mongodb)
- [MongoDB 新建数据库](https://docs-pd.mingdao.com/deployment/components/mongodb/createdb)
-->

---

💡 声明：内容由 AI 生成。尽管已努力确保信息的合理性，但 AI 模型仍可能产生不准确、过时或存在偏差的内容。请在执行关键操作前，务必对照[官方文档](https://docs-pd.mingdao.com)进行核实校验。
