#!/usr/bin/env python3
"""gzh_theme.py — 给公众号草稿切换品牌主题配色。

公众号只认内联 style，不能用 class 切主题。所以做法是：正文/封面统一用「青绿 aqua」
这套基准色值书写，本脚本把调色板里那几个**主题色值**整体替换成目标主题。
中性色（标题黑 #1a1a1a、正文 #333、灰阶、黑色渐变等）一律不动。

三套主题 = 三个板块各一色（见 SKILL.md 阶段 5-GZH、templates/gzh_themes.md）：
  aqua   青绿     #4ecdc4 — 板块「前沿科创」
  orange 橙       #ec7a26 — 板块「顶刊精读」
  indigo 靛蓝紫   #6366f1 — 板块「人物专访」
  blue   钴蓝     #2563eb — 板块「工具介绍」

可在任意两套主题间来回切换（幂等）：脚本认识所有主题的色值，统一映射到目标。

用法:
    python3 scripts/gzh_theme.py <draft_dir> --theme indigo
    python3 scripts/gzh_theme.py <draft_dir> --theme coral --files gongzhonghao.html
"""

import argparse
import sys
from pathlib import Path

# 每套主题 6 个「角色色值」：主色(hex)、主色(rgb，用于封面 rgba)、
# 数据卡底、引语卡底、浅边框、虚线分隔。角色之间值互不相同，跨主题也互不相同，
# 所以可安全地按角色分组替换。
THEMES = {
    "aqua":   {"accent": "#4ecdc4", "accent_rgb": "78,205,196", "accent_text": "#16a394",
               "tint_bg": "#f0fbfa", "tint_bg2": "#f4fbfa",
               "border": "#e0f3f1", "border2": "#cfeae6", "hl_bg": "#c7f0eb"},
    "indigo": {"accent": "#6366f1", "accent_rgb": "99,102,241", "accent_text": "#4f46e5",
               "tint_bg": "#f0f1fe", "tint_bg2": "#f4f4fe",
               "border": "#dfe0fb", "border2": "#cdcef6", "hl_bg": "#dcdefb"},
    "orange": {"accent": "#ec7a26", "accent_rgb": "236,122,38", "accent_text": "#cf6411",
               "tint_bg": "#fef3ea", "tint_bg2": "#fff6f0",
               "border": "#f7ddc4", "border2": "#f2cba6", "hl_bg": "#fde2c4"},
    "blue":   {"accent": "#2563eb", "accent_rgb": "37,99,235", "accent_text": "#1d4ed8",
               "tint_bg": "#eef3fd", "tint_bg2": "#f3f7fe",
               "border": "#d3e0fb", "border2": "#b9d0f8", "hl_bg": "#cddffb"},
}

# 板块 → 主题（公众号各板块固定一个主题色）
SECTION_THEME = {
    "前沿科创": "aqua",
    "顶刊精读": "orange",
    "人物专访": "indigo",
    "工具介绍": "blue",
}

ROLES = ["accent", "accent_rgb", "accent_text", "tint_bg", "tint_bg2", "border", "border2", "hl_bg"]
DEFAULT_FILES = ["gongzhonghao.html", "gongzhonghao_preview.html", "cover_gzh.html"]

# ──────────────────────────────────────────────────────────────────────
# 自动版权声明（BSL 1.1 要求保留版权声明；本脚本自动追加，避免漏掉）
# 标记：CREDIT_FOOTER_MARKER —— 若文中已有此标记，则不再追加，避免重复
# ──────────────────────────────────────────────────────────────────────
CREDIT_FOOTER_MARKER = "BioSpark · AI For Bios"
CREDIT_FOOTER_HTML = (
    '\n<p style="text-align:center; color:#999; font-size:12px; '
    'margin-top:24px; padding-top:12px; border-top:1px dashed #ddd;">'
    "本公众号使用 BioSpark 公众号模板<br>"
    "由 BioSpark · AI For Bios 开源提供<br>"
    "GitHub: github.com/yetong0516/BioSpark_AI-For-Bios_WeChat-OA-Automation-Pipeline<br>"
    "License: BSL 1.1（仅供非商业使用）"
    "</p>\n"
)


def ensure_credit_footer(text: str) -> tuple:
    """若文中没有 BioSpark 版权声明，则自动追加到末尾。返回 (新文本, 是否追加)。"""
    if CREDIT_FOOTER_MARKER in text:
        return text, False
    return text + CREDIT_FOOTER_HTML, True


def apply_theme(text: str, target: str) -> tuple:
    """把 text 里任何已知主题的色值，按角色替换为 target 主题的色值。返回 (新文本, 替换次数)。"""
    tgt = THEMES[target]
    n = 0
    for role in ROLES:
        tv = tgt[role]
        for name, theme in THEMES.items():
            sv = theme[role]
            if sv == tv:
                continue
            # hex 大小写都换
            for variant in {sv, sv.lower(), sv.upper()}:
                cnt = text.count(variant)
                if cnt:
                    text = text.replace(variant, tv)
                    n += cnt
    return text, n


def main():
    ap = argparse.ArgumentParser(description="切换公众号草稿的品牌主题配色")
    ap.add_argument("draft", help="草稿目录")
    ap.add_argument("--theme", required=True, choices=list(THEMES), help="目标主题")
    ap.add_argument("--files", nargs="*", default=None,
                    help=f"要处理的文件（默认 {DEFAULT_FILES}）")
    args = ap.parse_args()

    draft = Path(args.draft).resolve()
    if not draft.is_dir():
        print(f"错误: 目录不存在: {draft}", file=sys.stderr)
        return 1

    files = args.files or DEFAULT_FILES
    total, touched = 0, 0
    footers_added = 0
    for fn in files:
        p = draft / fn
        if not p.exists():
            continue
        old = p.read_text(encoding="utf-8")
        new, n = apply_theme(old, args.theme)
        # 自动追加 BioSpark 版权声明（BSL 1.1 要求保留）
        new, added = ensure_credit_footer(new)
        if added:
            footers_added += 1
        if n or added:
            p.write_text(new, encoding="utf-8")
            touched += 1
        total += n
        suffix = " 版权声明:已自动追加" if added else ""
        print(f"  {fn}: 替换 {n} 处{suffix}")
    print(f"\n✅ 已切到主题「{args.theme}」（{THEMES[args.theme]['accent']}），"
          f"共改 {touched} 个文件 {total} 处色值。")
    if footers_added:
        print(f"   🛡️  已自动追加 BioSpark 版权声明到 {footers_added} 个文件（BSL 1.1 要求）。")
    if "cover_gzh.html" in files or (args.files is None):
        print("   提醒：封面 HTML 改了色，需重跑 screenshot_cards.py 重新生成 cover_gzh.png。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
