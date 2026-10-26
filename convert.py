#!/usr/bin/env python3
"""把 cfst 的 result.csv 转成 JSON，供外部通过 raw URL 读取。"""

import csv
import datetime
import json
import os
import sys

CSV_PATH = "result.csv"
JSON_PATH = "result.json"
TOP_N = 50


def parse_rows(path):
    """按列索引解析，避免依赖中文表头（不同版本表头可能变）。"""
    rows = []
    if not os.path.exists(path):
        return rows

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # 跳过表头
        except StopIteration:
            return rows

        for r in reader:
            if len(r) < 7:
                continue
            try:
                rows.append({
                    "ip": r[0].strip(),
                    "loss": float(r[3]),
                    "latency_ms": round(float(r[4]), 2),
                    "speed_mbps": round(float(r[5]), 2),
                    "colo": r[6].strip(),
                })
            except (ValueError, IndexError):
                continue
    return rows


def main():
    rows = parse_rows(CSV_PATH)

    # 丢包的直接丢掉
    usable = [r for r in rows if r["loss"] == 0.0]

    # 有速度数据就按速度排，没有就按延迟排（-dd 模式只测延迟）
    has_speed = any(r["speed_mbps"] > 0 for r in usable)
    if has_speed:
        usable.sort(key=lambda x: (-x["speed_mbps"], x["latency_ms"]))
        mode = "latency+speed"
        warning = "速度由 GitHub 机房测出，不代表你的本地带宽，仅作可达性与相对排序参考"
    else:
        usable.sort(key=lambda x: x["latency_ms"])
        mode = "latency_only"
        warning = "仅测延迟未测速度。这是机房到 Cloudflare 的 RTT，不代表你的实际速度，只说明该 IP 当前可达"

    top = usable[:TOP_N]

    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(top),
        "total_tested": len(rows),
        "mode": mode,
        "source": "github-actions-runner",
        "warning": warning,
        "ips": top,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(out, ensure_ascii=False, indent=2))

    if not top:
        print("\n[WARN] 没有可用 IP，可能测速全部失败。", file=sys.stderr)


if __name__ == "__main__":
    main()
