#!/bin/bash
# ============================================================
# ⚠️  DEPRECATED — DO NOT USE  ⚠️
# ============================================================
# This script is disabled per SKILL.md → "公众号发布" section
# and memory [[never-touch-proxy]].
#
# Why it was disabled:
#   It kills the FlClash VPN process (`osascript -e 'quit app "FlClash"'`)
#   to force direct domestic connection for the WeChat upload. While
#   this *was* a workaround for RemoteDisconnected failures, it
#   breaks the daily scheduled task (the next-day run finds FlClash
#   not running, can't reach Nature/Science/bioRxiv) and is fragile
#   (race conditions, hangs, leaves FlClash off on errors).
#
# What to use instead:
#   python3 scripts/gzh_publish.py <draft> --draft-push
#   with the VPN left ON. WeChat is a Tencent domestic service and
#   gzh_publish.py already sets trust_env=False to use the real
#   network interface; the IP is then your real public IP (add it
#   to the WeChat OA IP allowlist). 40164 errors are recoverable;
#   they are not solved by killing the VPN.
#
# This file is kept ONLY as a historical reference. It will refuse
# to run. If you find yourself un-commenting the body, stop and
# fix the underlying connectivity instead — see SKILL.md.
# ============================================================

echo "❌ push_wechat.sh is deprecated and refuses to run."
echo "   Use: python3 scripts/gzh_publish.py <draft> --draft-push"
echo "   See the deprecation banner at the top of this file."
echo "   (memory [[never-touch-proxy]] + SKILL.md → 公众号发布)"
exit 64

