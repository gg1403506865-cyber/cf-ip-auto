# Cloudflare 优选 IP 自动更新（GitHub Actions）

每天自动测速，把结果写成 `result.json`，你通过一个固定 URL 就能拿到最新 IP。

## 怎么拿数据

部署完成后，访问：

```
https://raw.githubusercontent.com/<你的用户名>/<仓库名>/main/result.json
```

返回：

```json
{
  "updated": "2026-10-27T04:12:33Z",
  "count": 10,
  "total_tested": 128,
  "source": "github-actions-runner",
  "warning": "速度由 GitHub 机房测出，不代表你的本地带宽，仅作可达性与相对排序参考",
  "ips": [
    { "ip": "104.17.148.68", "loss": 0.0, "latency_ms": 55.18, "speed_mbps": 12.34, "colo": "HKG" }
  ]
}
```

raw.githubusercontent.com 有 **5 分钟 CDN 缓存**，想强制拿最新的，后面加时间戳：
`.../result.json?t=123456`

## ⚠️ 必须先知道的局限

**GitHub 的 runner 在 Azure 机房，不是你家宽带。**

所以测出来的速度是「Azure 机房 → Cloudflare」的速度，**不是「你 → Cloudflare」**。这意味着：

| 这个数据能告诉你 | 这个数据不能告诉你 |
|---|---|
| 哪些 IP 目前可达 | 哪个 IP 对你最快 |
| 大致的地区分布（colo 字段） | 你晚高峰的真实速度 |
| 哪些 IP 完全挂了 | 你的运营商路由质量 |

**结论：把它当作「候选池过滤器」，不要当「最优解」。**

拿到这 10 个 IP 后，最好还是在你本机用 `../test.bat` 再测一遍，从这 10 个里挑。比从 5955 个里盲扫快得多，这才是这个方案真正的价值。

## 部署步骤

### 1. 建仓库

GitHub 新建仓库，**选 Public**（私有仓库的 raw URL 需要带 token，不方便）。

### 2. 上传三个文件

```
convert.py
ip.txt
.github/workflows/cfip.yml
```

`.github` 是隐藏目录，网页拖拽会丢。用 Add file → Create new file，文件名直接输
`.github/workflows/cfip.yml`，路径会自动创建。

### 3. 确认 Actions 权限

仓库 Settings → Actions → General → Workflow permissions
选 **Read and write permissions**（要提交 result.json，必须写权限）。

### 4. 手动跑一次

Actions → `Cloudflare IP Auto Update` → Run workflow。

跑完检查仓库根目录有没有生成 `result.json`。

### 5. 拿到你的 URL

```
https://raw.githubusercontent.com/<用户名>/<仓库名>/main/result.json
```

## 定时设置

`.github/workflows/cfip.yml` 里：

```yaml
schedule:
  - cron: '0 20 * * *'   # UTC 20:00 = 北京 04:00
  - cron: '0 8 * * *'    # UTC 08:00 = 北京 16:00
```

cron 用的是 **UTC**，改时间记得换算。GitHub 的定时任务本身有延迟，通常晚 5-30 分钟，属正常。

## 两个维护点

**60 天无活动会被停用。** GitHub 规定仓库连续 60 天没有提交就停用定时工作流。这个 workflow 每天都会提交 `result.json`，只要测速正常就自动满足，一般不用管。

**IP 池要定期换。** `ip.txt` 是 Cloudflare 官方段，一般不变。但如果你发现结果里长期没有低延迟 IP，可能是这些段对你的运营商不友好，可以自己补充别的段。

## 参数调整

`cfip.yml` 里的这一行：

```
./cfst -f ip.txt -tl 200 -t 300 -dn 5 -p 20 -o result.csv
```

| 参数 | 含义 | 建议 |
|---|---|---|
| `-tl 200` | 延迟上限 | 想严格点改 `-tl 100`，但可能筛不出 IP |
| `-t 300` | 并发线程 | runner 性能好，300 没问题 |
| `-dn 5` | 下载测速次数 | 改大会更准但更慢，注意 25 分钟超时 |
| `-p 20` | 输出前 N 名 | 只影响 csv 行数，JSON 固定取前 10 |

## 如果测出来全是 0

runner 到 Cloudflare 都连不上，几乎不可能。真遇到了看 Actions 日志里 `raw result` 那一段。

更可能的情况是**测出来了但速度很低**——那是 Azure 机房到 CF 的路径问题，跟你的实际体验无关，忽略速度列、只看可达性就行。

## 文件说明

| 文件 | 用途 |
|---|---|
| `convert.py` | csv → json，纯标准库，无依赖 |
| `ip.txt` | Cloudflare 官方 IP 段（25 个） |
| `.github/workflows/cfip.yml` | 定时任务定义 |
| `result.json` | 运行后自动生成，不要手动改 |

测速工具：https://github.com/XIU2/CloudflareSpeedTest （MIT）
