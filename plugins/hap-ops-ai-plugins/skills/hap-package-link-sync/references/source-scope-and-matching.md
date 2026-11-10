# 来源范围与严格匹配规则

## 来源范围

默认只读取 `https://docs-pdop.mingdao.com/deployment/cluster/architecture` 当前页面中的两张表：

1. `各软件的 x86_64/AMD64 安装包下载链接`
2. `各软件的 ARM64/AARCH64 安装包下载链接`

页面中的其他导航、历史版本、组件页、外部下载页和跳转页均不属于本次同步范围。必须保留两张表的原始行数和每条原始行的来源架构。

## 身份和动作

- `MongoDB` 与 `MongoDB Tools` 是两个不同身份；平台包、版本和架构也分别比较。
- 仅有外部说明页或没有具体版本、架构、完整包地址时，标记“待判定”，不新增、不更新。
- 名称别名只有在身份、架构、版本均能由实际数据证明一致时才可合并；不能只凭名称相似或 URL 文件名推断。
- 本页面约定的特殊版本解析：Docker Compose、Promtail、K8S Metrics 服务镜像、Milvus 在 URL 和名称都没有版本时使用 `latest` 占位；CentOS 从 `centos7.9.2009.tar.gz` 取 `7.9.2009`；MinIO 原样取 `RELEASE.<时间戳>`；mingdaoyun-command 原样取 `node1018-python36`。仅对这些明确列出的软件生效，不能推广或用历史记录猜测。
- `N`：唯一目标记录不存在，创建完整记录。
- `U`：唯一目标记录的身份、架构、版本一致，仅 HAP 地址不同，更新 HAP 地址。
- `R`：唯一目标记录的身份、架构、版本和 HAP 地址一致，仅需追加新名称到备注。
- `S`：身份、架构、版本、HAP 地址均一致，跳过。
- `C`：无法唯一判定，只能列出候选和原因，不能进入执行确认清单。

## 单选架构

目标表架构字段必须从实时字段定义读取 option key。展示时同时显示 option 名称和 key；写入时只使用该 key。`Elasticsearch-ik` 和 `VictoriaLogs 数据源插件` 是当前明确的“通用”例外，其他软件不得自行归入通用。

## MongoDB / Mongo Tools

先按来源表实际架构拆分，再按目标表中具体的 MongoDB 或 MongoDB Tools 记录逐条匹配。若来源只给出平台说明页而没有可核对的版本和包地址，不能把它与目标表中任何历史记录自动绑定；确认页必须列出对应候选记录和待补信息，防止把数据库包和工具包混为一谈。

MongoDB 社区版入口页和 MongoDB Tools 入口页即使在 AMD64 与 ARM64 间使用同一个 URL，也只是官网入口共用，不是 HAP 下载地址。只有 `https://pdpublic.mingdao.com/...` 或 `https://pdpublic.nocoly.com/...` 的具体包地址才可写入目标表“HAP 地址”；MongoDB 官方入口 URL 只能保留在“源地址”或审核依据中。没有具体 HAP 包地址时，四类记录统一待判定，不得自动更新或新增。
