#!/bin/bash
# push_wechat.sh — 稳当地把草稿推到公众号草稿箱。
#
# 背景：梯子(FlClash)开着时，往微信传封面/配图会走境外隧道节点，大文件易被掐断
# (RemoteDisconnected)。微信是国内服务，直连最稳。本脚本在推送前临时退出 FlClash
# 走直连，推完再把它打开——全自动，日更定时用它那一步就永远稳。
#
# 用法：
#   scripts/push_wechat.sh drafts/2026-07-01_claude-science [--title "标题"]
#
# 直连时出口 IP = 你家宽带真实 IP，需提前加进公众号后台的 IP 白名单
# （设置与开发 → 基本配置 → IP 白名单，填你的出口 IP）。

set -u
DRAFT="${1:?用法: push_wechat.sh <draft_dir> [gzh_publish 额外参数]}"
shift || true
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

was_running="no"
if pgrep -x FlClash >/dev/null 2>&1; then
  was_running="yes"
  echo "· 临时退出 FlClash（改走国内直连上传）…"
  osascript -e 'quit app "FlClash"' >/dev/null 2>&1
  # 等隧道关闭、直连生效
  for i in 1 2 3 4 5; do
    sleep 1
    pgrep -x FlClash >/dev/null 2>&1 || break
  done
  sleep 1
fi

python3 "$ROOT/scripts/gzh_publish.py" "$DRAFT" --draft-push "$@"
rc=$?

if [ "$was_running" = "yes" ]; then
  echo "· 重新打开 FlClash…"
  open -a FlClash >/dev/null 2>&1
fi

exit $rc
