# Nginx HTTPS 证书更换手册模板

本模板供 nginx-https-cert-rotation 按实际入参填充。尖括号内容必须替换为已确认的值；不能确认时保留并列入“待补充参数”，不要猜测。

## 1. 参数与变更模式

~~~bash
NGINX_BIN='<nginx_bin，默认 /usr/local/nginx/sbin/nginx>'
NGINX_CONF='<nginx_conf，默认 /usr/local/nginx/conf/conf.d/hap.conf>'
CERT='<ssl_certificate，必须是绝对路径>'
KEY='<ssl_certificate_key，必须是绝对路径>'
NEW_CERT_SOURCE='<new_certificate_source；没有时按实际上传路径替换>'
NEW_KEY_SOURCE='<new_key_source；没有时按实际上传路径替换>'
STAMP="$(date +%Y%m%d%H%M%S)"
~~~

- 模式：same-path / path-change / ambiguous。
- same-path 表示当前生效配置已经指向 CERT 和 KEY，只替换文件。
- path-change 表示要改变 Nginx 指令中的路径，必须同时备份配置文件并精确修改两个指令。
- ambiguous 表示存在多个 TLS server 块或多个证书，先按域名和监听端口确认影响范围。

## 2. 操作前确认实际生效配置

NGINX_CONF 是常见的 HAP 业务配置文件候选值，可能只是主配置通过 include 引入的文件。先查看 Nginx 展开的实际配置：

~~~bash
sudo "$NGINX_BIN" -T 2>&1 | grep -nE '^[[:space:]]*ssl_certificate(_key)?[[:space:]]'
~~~

同时确认目标文件和配置上下文：

~~~bash
sudo grep -nE '^[[:space:]]*(server_name|listen|ssl_certificate(_key)?)[[:space:]]' "$NGINX_CONF"
sudo "$NGINX_BIN" -t
~~~

如果 NGINX_CONF 不是实际文件，或 -T 显示的是另一份主配置，先根据 include、systemd unit、Nginx master 进程参数确定真实路径。不要把 conf.d/hap.conf 直接作为 -c 参数，除非已确认它就是主配置文件。

记录与目标域名对应的 server_name、listen 443 ssl、ssl_certificate 和 ssl_certificate_key。如果有多组结果，停止并先完成映射。

## 3. 备份

### same-path 模式

确认 CERT 和 KEY 都是当前生效文件后执行：

~~~bash
sudo test -f "$CERT" || { echo "certificate not found: $CERT"; exit 1; }
sudo test -f "$KEY" || { echo "private key not found: $KEY"; exit 1; }
sudo cp -p -- "$CERT" "$CERT.$STAMP.bak"
sudo cp -p -- "$KEY" "$KEY.$STAMP.bak"
sudo stat -c '%U:%G %a %n' "$CERT" "$KEY" "$CERT.$STAMP.bak" "$KEY.$STAMP.bak"
echo "backup timestamp: $STAMP"
~~~

### path-change 模式

除上面两份当前证书/私钥备份外，还要备份实际被加载的配置文件：

~~~bash
sudo cp -p -- "$NGINX_CONF" "$NGINX_CONF.$STAMP.bak"
~~~

将 ACTIVE_CERT 和 ACTIVE_KEY 替换为第 2 节从 nginx -T 确认的旧路径；新路径必须是用户明确提供的 CERT 和 KEY。不要批量替换所有配置文件中的同名字符串。

## 4. 上传并替换新文件

先把新证书和私钥通过受控方式上传到服务器。不要在聊天、工单或命令输出中粘贴私钥内容。

如果输入了 NEW_CERT_SOURCE 和 NEW_KEY_SOURCE，并且它们已确认是本次上传的文件，可使用同一文件系统中的临时文件：

~~~bash
sudo test -f "$NEW_CERT_SOURCE" || { echo "new certificate source not found: $NEW_CERT_SOURCE"; exit 1; }
sudo test -f "$NEW_KEY_SOURCE" || { echo "new key source not found: $NEW_KEY_SOURCE"; exit 1; }

sudo cp -- "$NEW_CERT_SOURCE" "$CERT.tmp.$STAMP"
sudo cp -- "$NEW_KEY_SOURCE" "$KEY.tmp.$STAMP"
sudo chmod 0644 "$CERT.tmp.$STAMP"
sudo chmod 0600 "$KEY.tmp.$STAMP"

# 若原文件存在，替换前按原文件核对并保留 owner/group；不要盲目 chown。
if sudo test -e "$CERT"; then sudo chown --reference="$CERT" "$CERT.tmp.$STAMP"; fi
if sudo test -e "$KEY"; then sudo chown --reference="$KEY" "$KEY.tmp.$STAMP"; fi

# 先校验临时文件，成功后才替换线上目标文件。
openssl x509 -in "$CERT.tmp.$STAMP" -noout -subject -issuer -dates -ext subjectAltName
openssl x509 -in "$CERT.tmp.$STAMP" -pubkey -noout \
  | openssl pkey -pubin -outform DER \
  | openssl sha256
openssl pkey -in "$KEY.tmp.$STAMP" -pubout \
  | openssl pkey -pubin -outform DER \
  | openssl sha256

sudo mv -f -- "$CERT.tmp.$STAMP" "$CERT"
sudo mv -f -- "$KEY.tmp.$STAMP" "$KEY"
sudo stat -c '%U:%G %a %n' "$CERT" "$KEY"
~~~

如果没有输入源文件路径，把上面的两个源路径替换成实际上传位置后再执行。若 CERT/KEY 是新路径而不是现有路径，先完成 path-change 模式的配置修改，再按新路径安装文件，并确认 Nginx master 进程具有读取权限。

## 5. 检查证书和私钥

查看证书主题、SAN、签发者和有效期：

~~~bash
openssl x509 -in "$CERT" -noout -subject -issuer -dates -ext subjectAltName
~~~

openssl x509 默认读取证书文件中的第一张证书；ssl_certificate 应按证书厂商要求包含叶子证书及中间证书链。重点确认域名/SAN、notBefore 和 notAfter。

使用规范化后的公钥 DER 做证书/私钥匹配检查，两个 SHA-256 输出必须一致：

~~~bash
openssl x509 -in "$CERT" -pubkey -noout \
  | openssl pkey -pubin -outform DER \
  | openssl sha256

openssl pkey -in "$KEY" -pubout \
  | openssl pkey -pubin -outform DER \
  | openssl sha256
~~~

私钥如需输入口令，只在服务器交互终端输入，不要把口令写入脚本、命令行参数或手册。若两次摘要不一致，停止，不要 reload。

如果私钥带口令，先确认当前 Nginx 启动方式支持非交互加载；systemd 服务通常不能在 reload 时等待人工输入口令。

## 6. 检查 Nginx 配置

先检查，不通过就停止：

~~~bash
sudo "$NGINX_BIN" -t
~~~

只有返回 syntax is ok 和 test is successful（或同等成功结果）后，才进入 reload。若 Nginx 实际使用非默认主配置，需要改为已确认的主配置参数，例如：

~~~bash
sudo "$NGINX_BIN" -t -c '<已确认的主 nginx.conf 绝对路径>'
~~~

不要用 NGINX_CONF 代替主配置路径，除非已确认文件类型。

## 7. Reload Nginx

优先使用已确认的 systemd unit：

~~~bash
sudo systemctl reload nginx
~~~

如果没有 systemd unit，且 Nginx master 进程正在运行，可使用：

~~~bash
sudo "$NGINX_BIN" -s reload
~~~

同一访问地址的证书续期通常只需 reload Nginx，不需要重启 HAP 服务。若访问域名、协议、端口或 HAP 对外访问地址发生变化，另行核对 HAP 的 ENV_ADDRESS_MAIN；早期版本还要核对 ENV_MINGDAO_PROTO、ENV_MINGDAO_HOST、ENV_MINGDAO_PORT，并按官方文档重启 HAP 使其生效。

## 8. 验证用户实际拿到的证书

把 <verify_host> 换成真实访问域名。必须保留 -servername，否则多域名 Nginx 可能返回默认 server 的证书：

~~~bash
openssl s_client -connect '<verify_host>:443' -servername '<verify_host>' \
  </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -fingerprint -sha256
~~~

如有访问 URL，再执行：

~~~bash
curl -Iv '<verify_url>'
~~~

确认浏览器无证书告警、域名/SAN 正确、有效期已更新、页面和 HAP 长连接/登录功能正常。不要用 curl -k 作为成功判定；它会忽略证书信任错误。

## 9. 回滚

如果 reload 后出现异常，用第 3 节记录的时间戳恢复，不要猜测备份文件名：

~~~bash
ROLLBACK_STAMP='<第 3 节记录的时间戳>'
sudo cp -p -- "$CERT.$ROLLBACK_STAMP.bak" "$CERT"
sudo cp -p -- "$KEY.$ROLLBACK_STAMP.bak" "$KEY"
~~~

path-change 模式还原配置文件：

~~~bash
sudo cp -p -- "$NGINX_CONF.$ROLLBACK_STAMP.bak" "$NGINX_CONF"
~~~

回滚后必须再次检查并仅在通过后 reload：

~~~bash
sudo "$NGINX_BIN" -t && sudo systemctl reload nginx
~~~

如果环境没有 systemd，改用 sudo "$NGINX_BIN" -s reload；若 nginx -t 仍失败，保持停止状态并进入诊断，不要继续反复 reload。

## 10. 常见异常

| 现象 | 优先检查 |
| --- | --- |
| nginx -t 找不到证书 | nginx -T 的实际主配置、include 路径、文件名和权限。 |
| key values mismatch 或摘要不同 | 新证书和私钥不是同一对，重新核对厂商文件。 |
| permission denied | 目录每一级的执行权限、文件 mode、owner/group，以及 Nginx master 的实际读取身份。 |
| 证书仍未更新 | 是否 reload 了正确的 Nginx 实例；外部是否由 CDN/WAF/SLB/Ingress 终止 TLS；是否漏了 -servername。 |
| 浏览器提示链不完整 | 重新确认 ssl_certificate 使用的是厂商要求的 full chain，而不是只有叶子证书。 |
| reload 失败 | 先看 nginx -t 和 error log；不要直接重启 HAP 来掩盖 Nginx 问题。 |
| 只有部分节点更新 | 检查负载均衡后端节点，逐节点或按变更窗口完成并验证。 |

官方参考：

- [如何配置代理 | HAP 私有部署](https://docs-pd.mingdao.com/hap/deployment/proxy/nginx_default/)
- [HTTPS | HAP 私有部署](https://docs-pd.mingdao.com/hap/deployment/proxy/https/)
