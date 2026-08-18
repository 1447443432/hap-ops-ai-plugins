# HAP 升级命令库

本库用于为升级指南提供命令骨架和 URL 规律。使用时遵循以下规则：

- 本文件只作为命令参考库；若实时升级详情页给出了更具体的命令或参数，以实时页面为准
- 所有版本号均使用**应用版本**，即不带 `v` 的形式，如 `7.1.0`
- 根据部署模式、联网情况、CPU 架构选择对应命令，禁止混用单机与集群命令
- 模板中出现的 `{命名空间}`、`{目标版本号}`、`{目标存储组件版本号}` 等占位内容，最终输出前必须替换成实际值
- 提前准备阶段要汇总**本次升级实际会用到的全部资源**，不要默认只有 HAP 微服务镜像
- 离线文件清单只保留本次升级真正需要的文件。未出现在升级路径中任何一个版本详情页的组件离线包（如 doc/ldoc/file 存储服务），**禁止**列入清单。禁止推断式添加
- 如果线上文档中的附加操作指向其他页面，本文件只提供命令模式参考；最终文档仍应以实际打开后的页面内容为准并展开步骤

## 1. 镜像拉取 / 导入（根据网络情况）

### 联网模式 — 单机
- **AMD64**: `docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{目标版本号}` 
  - **示例**：`docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:7.1.0` 

- **ARM64**: `docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap-arm64:{目标版本号}` 
  - 示例：`docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap-arm64:7.1.0` 


### 联网模式 — 集群 (每台微服务节点)
- **AMD64**：`crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:{目标版本号}` 
  - **通用**: `crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap:7.1.0` 

- **ARM64**: `crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap-arm64:{目标版本号}` 
  - 示例：`crictl pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-hap-arm64:7.1.0` 

### 离线模式 — 镜像下载链接 URL 规律
- **AMD64**: `https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-hap-linux-amd64-{版本号}.tar.gz` 
  - **示例**： `https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-hap-linux-amd64-7.1.0.tar.gz` 

- **ARM64**: `https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-hap-linux-arm64-{版本号}.tar.gz` 
  - **示例**： `https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-hap-linux-arm64-7.1.0.tar.gz` 


### 离线模式 — 导入
- **单机模式**：基于 docker 命令导入离线镜像文件

  ```text
  docker load -i xxx.tar.gz
  ```

  

- **集群模式**：基于 K8s 环境，将离线镜像上传到每个节点，解压并导入离线镜像文件（使用管道方式，无需中间文件）

  ```
  gunzip -c xxx.tar.gz | ctr -n k8s.io image import -
  ```

  

---

## 2. MongoDB 预置数据更新

> 若跨版本升级中包含多次MongoDB 预置数据更新操作，仅需执行最新版本的相应操作即可。

### 单机联网
```bash
bash -c "$(curl -fsSL https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_docker.sh)" -s {该操作涉及的最新版本号}
```

### 单机离线
1. 提前下载离线文件： 

   ```
   更新脚本下载链接：https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_docker.sh
   预置数据下载链接：https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_{该操作涉及的最新版本号}.tar.gz
   ```

2. 将离线文件上传至服务器

3. 执行更新命令: `bash ./preset_mongodb_docker.sh {该操作涉及的最新版本号} ./preset_mongodb_{该操作涉及的最新版本号}.tar.gz`

### 集群联网
```bash
bash -c "$(curl -fsSL https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_k8s.sh)" -s {该操作涉及的最新版本号} {命名空间}
```

### 集群离线
1. 提前下载离线文件： 

   ```
   更新脚本下载链接：https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_k8s.sh
   预置数据下载链接：https://pdpublic.mingdao.com/private-deployment/data/preset_mongodb_{该操作涉及的最新版本号}.tar.gz
   ```
2. 将离线文件上传至控制节点服务器

3. **执行更新命令**: `bash ./preset_mongodb_k8s.sh {该操作涉及的最新版本号} {命名空间} ./preset_mongodb_{该操作涉及的最新版本号}.tar.gz`

---

## 2.5 预置文件（fileInit / s3fileInit）

> 若跨版本升级中包含多次 fileInit 操作，仅需执行最新版本的相应操作即可（与 MongoDB 预置数据合并规则一致）。

### URL 规律
```
https://pdpublic.mingdao.com/private-deployment/data/preset_file_{版本号}.tar.gz
```
- `{版本号}` 取升级路径中含 fileInit 操作的**最高版本号**（不带 `v` 前缀）
- 详见 SKILL.md §6「预置文件（preset_file）下载地址规范」

### 离线场景
1. 提前下载预置文件：`https://pdpublic.mingdao.com/private-deployment/data/preset_file_{该操作涉及的最新版本号}.tar.gz`
2. 上传至服务器
3. 在 config Pod 内执行（集群模式）：
   - 内置存储（file v1）：`source /entrypoint-cluster.sh && fileInit`
   - MinIO/S3（file v2）：`source /entrypoint-cluster.sh && s3fileInit`
   - 外部对象存储（S3 标准协议）：手动上传 preset_file 包到对象存储 bucket

### 联网场景
- 情况 1/2：fileInit / s3fileInit 命令在容器内直接执行，自动拉取预置文件，无需提前下载
- 情况 3（外部 S3）：仍需手动下载 preset_file 包并上传到对象存储 bucket

---

## 3. HAP 微服务升级命令

- **单机模式**: 修改 `docker-compose.yaml` 镜像版本号，在管理器所在路径执行 `bash ./service.sh restartall`
- **集群模式**: 在 `/data/mingdao/script/kubernetes` 目录下执行：
  - 滚动更新: `bash update.sh update hap {目标版本号}`
  - 非滚动更新: 先 `bash stop.sh`，确认 Pod 消失后执行 `bash update.sh update hap {目标版本号}`
  - 如是 ARM64 镜像更新，更新脚本执行时，`hap` 需要加上 `-arm64` 的标识，例如：`bash update.sh update hap-arm64 {目标版本号}`

> ⚠️ **ARM64 架构下 service.yaml 新增服务镜像命名规则**：
> - 当架构为 ARM64 且 service.yaml 需要新增服务时，YAML 中新增服务的镜像名称必须添加 `-arm64` 后缀
> - 命名规则：`mingdaoyun-{服务名}` → `mingdaoyun-{服务名}-arm64`
> - 示例：`mingdaoyun-platformapi:7.3.0` → `mingdaoyun-platformapi-arm64:7.3.0`
> - 架构校验（Step 5）已通过即代表所有镜像均有 ARM64 版本，**禁止**在文档中添加可用性警告或确认提示
> - **禁止**在 ARM64 文档中直接使用不带 `-arm64` 后缀的镜像名

---

## 4. 存储组件升级

- **联网 AMD64**: `docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-sc:{存储组件镜像版本号}`

- **联网 ARM64**: `docker pull registry.cn-hangzhou.aliyuncs.com/mdpublic/mingdaoyun-sc-arm64:{存储组件镜像版本号}`

- 离线情况下，则提前下载对应镜像，上传到服务器后导入。离线镜像下载链接示例：

  ```
  AMD64: https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-sc-linux-amd64-{存储组件镜像版本号}.tar.gz
  ARM64: https://pdpublic.mingdao.com/private-deployment/offline/mingdaoyun-sc-linux-arm64-{存储组件镜像版本号}.tar.gz
  ```

- **升级操作**: 修改 `docker-compose.yaml` 中存储组件镜像版本号，执行 `bash ./service.sh restartall`

---

## 5. 创建 MongoDB 数据库 (认证开启时)

### 单机模式
```bash
# 进入存储组件容器
docker exec -it $(docker ps | grep mingdaoyun-sc | awk '{print $1}') bash

# 容器内登录 (替换用户名和密码)
mongo -u 用户名 -p 密码 --authenticationDatabase admin

# 库创建
use {库名}
db.createUser({ user: "与其他库一致用户名", pwd: "与其他库一致密码", roles: [{ role: "readWrite", db: "{库名}" }] })
```

### 集群模式
```bash
# 使用含 admin 角色的用户登录 (替换连接信息)
mongo -u 用户名 -p 密码 --authenticationDatabase admin

# 库创建
use {库名}
db.createUser({ user: "与其他库一致用户名", pwd: "与其他库一致密码", roles: [{ role: "readWrite", db: "{库名}" }] })
```

---

## 6. Markdown 转 HTML 转换工具

### md2html（Go 语言）

位于 `tools/md2html/`，使用 goldmark 解析 Markdown + goquery 处理 HTML。

**特点**：
- ✅ 单文件可执行（`md2html` / `md2html.exe`），编译后无需任何运行时依赖
- ✅ HTML 模板通过 `go:embed` 嵌入，分发时只需一个二进制文件
- ✅ 静态生成 TOC 目录树（支持 h2/h3/h4/h5 五级，折叠/展开，#anchor 导航）
- ✅ 代码块自动加语言标签 + 右上角一键复制按钮
- ✅ 版本信息表格（首个表格）自动加 `class="meta-block"` 特殊样式
- ✅ 日期高亮：`.date-val` / `.date-val-primary` / `.inline-date`
- ✅ `⚠️ 特别注意` 引用块 → `blockquote.attention` 红底醒目样式
- ✅ 跨平台：Win/macOS/Linux 均可编译运行

**使用方式**：
```bash
# 编译（首次或源码变更后）
cd tools/md2html && go build -o md2html . && cd ../..

# 转换
tools/md2html/md2html(.exe) -input {Markdown文件路径} -output {HTML输出路径}
```

**依赖**：Go 1.26+（仅编译时需要）

**位置**：`tools/md2html/main.go` + `tools/md2html/template.html`

**注意事项**：
- 转换前确保 Markdown 文件完整性（无模板占位符残留）
- HTML 样式在模板文件中维护，修改样式需更新 `template.html` 后重新编译

---

## 7. 非 MySQL 数据库 DDL 执行命令

> 当用户指定使用非 MySQL 关系型数据库时，升级后操作中的 DDL 执行命令需替换为对应数据库的命令行工具。以下为各数据库的连接命令模板。
>
> **DDL 内容来源**：通过 hap CLI 查询明道云工作表获取（详见 SKILL.md「关系型数据库变更 DDL（非 MySQL 场景）」章节），**禁止**直接使用 MySQL DDL 语法。

### 达梦 DM

- **命令行工具**：`disql`
- **单机模式**：
  * **达梦为独立服务器部署** → 直接在数据库服务器上执行：
    ```bash
    disql {用户名}/{密码}@{数据库服务器IP}:5236
    ```
  * **达梦为容器部署（与 HAP 在同一台机器）** → 进入**达梦自身的容器**（非 HAP 微服务容器）执行：
    ```bash
    # 进入达梦数据库容器（替换为实际达梦容器名，禁止使用 mingdaoyun-hap/community 容器）
    docker exec -it {达梦容器名} bash
    # 在容器内连接达梦
    disql {用户名}/{密码}@localhost:5236
    ```
  * **禁止**在非 MySQL DDL 步骤中使用 `docker exec -it $(docker ps | grep mingdaoyun...)` 进入 HAP 微服务容器执行 DDL
- **集群模式 / 外部部署**：
  ```bash
  # 在数据库服务器上直接执行
  disql {用户名}/{密码}@{数据库服务器IP}:5236
  ```
- **执行 DDL 脚本**：
  ```bash
  disql {用户名}/{密码}@{IP}:5236 \`{DDL脚本路径}.sql
  ```
- **注意事项**：达梦使用模式（Schema）隔离数据，DDL 中库名需用双引号包裹（如 `"MDPROJECT"`）

### 电科金仓 KingbaseES

- **命令行工具**：`ksql`
- **连接命令**：
  ```bash
  ksql -h {数据库服务器IP} -p 54321 -U {用户名} -d {库名}
  ```
- **执行 DDL 脚本**：
  ```bash
  ksql -h {IP} -p 54321 -U {用户名} -d {库名} -f {DDL脚本路径}.sql
  ```

### OceanBase

- **命令行工具**：`obclient`（MySQL 兼容模式）
- **连接命令**：
  ```bash
  obclient -h {数据库服务器IP} -P 2883 -u {用户名}@{租户名} -p{密码} -D {库名}
  ```
- **执行 DDL 脚本**：
  ```bash
  obclient -h {IP} -P 2883 -u {用户名}@{租户名} -p{密码} -D {库名} < {DDL脚本路径}.sql
  ```

### 虚谷

- **命令行工具**：`xugucli`
- **连接命令**：
  ```bash
  xugucli -h {数据库服务器IP} -p 5138 -u {用户名} -p {密码} -d {库名}
  ```

### 瀚高 HighGo

- **命令行工具**：`psql`（PostgreSQL 兼容）
- **连接命令**：
  ```bash
  psql -h {数据库服务器IP} -p 5866 -U {用户名} -d {库名}
  ```
- **执行 DDL 脚本**：
  ```bash
  psql -h {IP} -p 5866 -U {用户名} -d {库名} -f {DDL脚本路径}.sql
  ```

### 南大通用 GBase8c

- **命令行工具**：`gsql`
- **连接命令**：
  ```bash
  gsql -h {数据库服务器IP} -p 5432 -U {用户名} -d {库名} -W {密码}
  ```

### TiDB

- **命令行工具**：`mysql`（MySQL 协议兼容）
- **连接命令**：
  ```bash
  mysql -h {数据库服务器IP} -P 4000 -u {用户名} -p{密码} {库名}
  ```
- **说明**：TiDB 兼容 MySQL 协议，DDL 语法与 MySQL 基本一致，但仍以工作表查询到的 TiDB 专用 DDL 为准

### TDSQL

- **命令行工具**：`mysql`（MySQL 协议兼容）
- **连接命令**：参考 TiDB，使用对应的 TDSQL 网关地址和端口
- **说明**：TDSQL 兼容 MySQL 协议，DDL 语法与 MySQL 基本一致

### openGauss

- **命令行工具**：`gsql`（PostgreSQL 兼容）
- **连接命令**：
  ```bash
  gsql -h {数据库服务器IP} -p 5432 -U {用户名} -d {库名} -W {密码}
  ```

> ⚠️ **重要提醒**：
> - 以上命令模板中的 `{IP}`、`{端口}`、`{用户名}`、`{密码}`、`{库名}` 等占位符需替换为实际值
> - 各数据库的默认端口可能因部署配置不同而异，以实际环境为准
> - DDL 内容必须从工作表查询获取，**禁止**将 MySQL DDL 直接用于非 MySQL 数据库
