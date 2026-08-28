# <参考指南名称>

> 本手册用于 HAP 私有部署前置 Nginx 的 HTTPS 证书更换，按“目的 → 命令 → 正常结果 → 出错处理”编写，Linux 初学者也可以照着做。

> ⚠️ 重要：所有命令默认直接由 root 用户执行。先确认路径再复制命令；/data/mdtemp/ 下的文件名只是上传示例。nginx -t 检查失败时，停在当前步骤，不要重载或重启 Nginx。

## 1. 参数摘要

| 参数 | 值 | 来源或说明 |
| --- | --- | --- |
| Nginx 可执行文件 | /usr/local/nginx/sbin/nginx | 🟨 待确认 |
| Nginx 业务配置文件 | /usr/local/nginx/conf/conf.d/hap.conf | 🟨 待确认 |
| 证书目标路径 | <ssl_certificate> | 🟥 缺失 |
| 私钥目标路径 | <ssl_certificate_key> | 🟥 缺失 |
| 新证书来源 | /data/mdtemp/new-certificate.crt | 🟨 待确认 |
| 新私钥来源 | /data/mdtemp/new-private-key.key | 🟨 待确认 |
| 访问域名 | <待补充域名> | 🟨 待确认 |

状态图例：🟩 已确认（用户明确提供）；🟨 待确认（默认值、示例或需要现场核验）；🟥 缺失（不能据此生成精确替换命令）。

目录就是文件夹；绝对路径就是从 / 开始的完整文件位置；备份就是先复制一份旧文件。

## 2. 第 1 步：确认活动配置

**目的：** 找到 Nginx 当前真正使用的证书和私钥，避免改错文件。

**执行：**

~~~bash
/usr/local/nginx/sbin/nginx -T 2>&1 | grep -nE 'ssl_certificate(_key)?|server_name|listen[[:space:]].*443'
grep -nE 'include|ssl_certificate(_key)?|server_name|listen[[:space:]].*443' /usr/local/nginx/conf/conf.d/hap.conf
~~~

**正常结果：** 能看到 HTTPS 配置，并且证书、私钥路径与参数摘要一致。

**出错处理：** ⚠️ 如果没有看到目标路径，不要替换文件。先检查主配置引用了哪些文件：

~~~bash
grep -nE '^[[:space:]]*include[[:space:]]+' /usr/local/nginx/conf/nginx.conf
~~~

沿着 include 找到真正的配置后再继续。conf.d 下的业务配置文件不要直接当作 Nginx 主配置文件。

## 3. 第 2 步：备份旧文件

**目的：** 出问题时可以恢复旧证书。

先执行并记下显示的数字，例如 20260828103000：

~~~bash
date '+%Y%m%d%H%M%S'
~~~

把下面的 YYYYMMDDHHMMSS 换成刚才的数字，两条命令使用同一个数字：

~~~bash
cp -p -- <ssl_certificate> <ssl_certificate>.YYYYMMDDHHMMSS.bak
cp -p -- <ssl_certificate_key> <ssl_certificate_key>.YYYYMMDDHHMMSS.bak
ls -l -- <ssl_certificate>.YYYYMMDDHHMMSS.bak <ssl_certificate_key>.YYYYMMDDHHMMSS.bak
~~~

**正常结果：** 能看到两个 .bak 文件，大小不是 0。

**出错处理：** ⚠️ 任一命令报错，就停在这里，先检查路径、磁盘空间或权限。

## 4. 第 3 步：确认新文件

**目的：** 确认新证书和新私钥已经在服务器上。没有提供上传源时，下面是上传到 /data/mdtemp/ 的示例。

~~~bash
ls -l -- /data/mdtemp/new-certificate.crt /data/mdtemp/new-private-key.key
~~~

**正常结果：** 能看到两个文件，大小大于 0。实际文件名不同，就把后续命令中的示例路径换成真实绝对路径。

**出错处理：** ⚠️ 找不到文件时不要继续，先上传文件或确认目录和文件名。

## 5. 第 4 步：检查证书和私钥

**目的：** 确认域名、有效期正确，并确认两者是一对。

查看证书信息：

~~~bash
openssl x509 -in /data/mdtemp/new-certificate.crt -noout -subject -issuer -dates -ext subjectAltName
~~~

如果提示不认识 -ext，改用：

~~~bash
openssl x509 -in /data/mdtemp/new-certificate.crt -noout -text
~~~

比较公钥摘要：

~~~bash
openssl x509 -in /data/mdtemp/new-certificate.crt -pubkey -noout | openssl pkey -pubin -outform DER | sha256sum
openssl pkey -in /data/mdtemp/new-private-key.key -pubout -outform DER | sha256sum
~~~

**正常结果：** 域名和有效期符合预期，最后两行摘要完全相同。

**出错处理：** ⚠️ 域名不对、证书过期、摘要不一致或私钥无法读取时，停在这里，不要覆盖旧文件。加密私钥提示口令时只在终端输入，不要写入手册。

## 6. 第 5 步：准备临时文件并替换

**目的：** 先复制、再替换，减少直接覆盖出错的风险。

把 YYYYMMDDHHMMSS 换成第 3 步的同一个数字：

~~~bash
cp -p -- /data/mdtemp/new-certificate.crt <ssl_certificate>.tmp.YYYYMMDDHHMMSS
cp -p -- /data/mdtemp/new-private-key.key <ssl_certificate_key>.tmp.YYYYMMDDHHMMSS
chown --reference=<ssl_certificate> <ssl_certificate>.tmp.YYYYMMDDHHMMSS
chown --reference=<ssl_certificate_key> <ssl_certificate_key>.tmp.YYYYMMDDHHMMSS
chmod --reference=<ssl_certificate> <ssl_certificate>.tmp.YYYYMMDDHHMMSS
chmod --reference=<ssl_certificate_key> <ssl_certificate_key>.tmp.YYYYMMDDHHMMSS
ls -l -- <ssl_certificate>.tmp.YYYYMMDDHHMMSS <ssl_certificate_key>.tmp.YYYYMMDDHHMMSS
~~~

**正常结果：** 能看到两个临时文件，命令没有报错。

确认第 4 步检查通过后，再执行替换：

~~~bash
mv -f -- <ssl_certificate>.tmp.YYYYMMDDHHMMSS <ssl_certificate>
mv -f -- <ssl_certificate_key>.tmp.YYYYMMDDHHMMSS <ssl_certificate_key>
~~~

**出错处理：** ⚠️ 复制、权限处理或替换失败时，不要重载，先检查路径和权限。

## 7. 第 6 步：检查 Nginx 配置

**目的：** 确认 Nginx 能读取新证书和完整配置。

~~~bash
/usr/local/nginx/sbin/nginx -t
~~~

**正常结果：** 看到 syntax is ok 和 test is successful。

**出错处理：** ⚠️ 看到 test failed 或其他错误时，停在这里，不能重载或重启；先按报错修复，再重新检查。

## 8. 第 7 步：重载 Nginx

**目的：** 让 Nginx 重新读取新证书。旧部署可能没有 systemd，默认使用 Nginx 二进制平滑重载。

默认方式：

~~~bash
/usr/local/nginx/sbin/nginx -s reload
~~~

只有确认服务器存在 nginx.service 时，才可以二选一使用完整重启：

~~~bash
systemctl restart nginx
~~~

**正常结果：** 默认重载命令没有报错；有些版本会显示 signal process started。

**出错处理：** ⚠️ 两种方式只选一种，不要连续执行。systemctl 不可用时，使用第一种方式。

## 9. 第 8 步：验证并回滚

### 验证 HTTPS

**目的：** 确认用户实际访问到新证书。

有域名时，把 <实际域名> 换成真实域名：

~~~bash
curl -Iv https://<实际域名>/
openssl s_client -connect <实际域名>:443 -servername <实际域名> </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
~~~

**正常结果：** 浏览器没有证书警告，域名匹配，有效期已更新，业务页面可以打开。

**出错处理：** ⚠️ 没有域名时先标记待确认；如果仍返回旧证书，检查 CDN、WAF、SLB、Ingress 或其他 Nginx 节点。

### 回滚

如果检查、重载或访问失败，把 YYYYMMDDHHMMSS 换成备份时的数字：

~~~bash
cp -p -- <ssl_certificate>.YYYYMMDDHHMMSS.bak <ssl_certificate>
cp -p -- <ssl_certificate_key>.YYYYMMDDHHMMSS.bak <ssl_certificate_key>
/usr/local/nginx/sbin/nginx -t
/usr/local/nginx/sbin/nginx -s reload
~~~

**正常结果：** nginx -t 成功后，旧证书恢复。

**出错处理：** ⚠️ 回滚后的 nginx -t 仍失败时，不要反复重启；保留报错并检查备份路径、权限和主配置。

## 如果遇到问题

| 现象 | 先做什么 |
| --- | --- |
| 找不到证书配置 | 重新执行 nginx -T，沿着 include 找真正配置 |
| 证书和私钥不匹配 | 重新执行公钥摘要命令，确认两行最后摘要相同 |
| Nginx 无法读取私钥 | 检查私钥属主、权限和父目录权限 |
| 浏览器提示链不完整 | 确认证书文件第一张是服务器证书，后面包含中间证书 |
| 重载后仍是旧证书 | 检查 CDN、WAF、SLB 或其他 Nginx 节点 |

## 参考文档

- [如何配置代理 | HAP 私有部署](https://docs-pd.mingdao.com/deployment/proxy/nginx_default/)
- [HTTPS | HAP 私有部署](https://docs-pd.mingdao.com/deployment/proxy/https/)
