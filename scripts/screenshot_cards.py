#!/usr/bin/env python3
"""screenshot_cards.py — 将卡片 HTML 截图为 PNG（默认 1080x1440 @2x，小红书）。

也可用于公众号封面（900x383）等其它尺寸：用 --width/--height 指定视口，
用 --name 指定输出文件前缀。

用法:
    # 小红书 6 卡片（默认尺寸，行为与旧版完全一致）
    python3 screenshot_cards.py <html_file> [--out DIR] [--scale N]

    # 公众号封面 900x383 @2x → cover_gzh-1.png
    python3 screenshot_cards.py cover_gzh.html --out DIR \
        --width 900 --height 383 --name cover_gzh

输出:
    <name>-1.png, <name>-2.png, ... 到指定目录（默认与 HTML 同目录）
    默认 name=card，即 card-1.png ...
"""

import argparse
import sys
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="卡片 HTML → PNG 截图")
    ap.add_argument("html", help="卡片 HTML 文件路径")
    ap.add_argument("--out", default=None, help="输出目录（默认与 HTML 同目录）")
    ap.add_argument("--scale", type=int, default=2, help="设备缩放因子（默认 2）")
    ap.add_argument("--width", type=int, default=1080, help="视口宽度（默认 1080）")
    ap.add_argument("--height", type=int, default=1440, help="视口高度（默认 1440）")
    ap.add_argument("--name", default="card", help="输出文件前缀（默认 card → card-1.png）")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"错误: 文件不存在: {html_path}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else html_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: 需要安装 playwright (pip install playwright && playwright install chromium)",
              file=sys.stderr)
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
        )
        page.goto(f"file://{html_path}", wait_until="networkidle")
        time.sleep(1)

        cards = page.query_selector_all(".card")
        if not cards:
            print("错误: 未找到 .card 元素", file=sys.stderr)
            browser.close()
            return 1

        print(f"找到 {len(cards)} 张卡片")
        for i, card in enumerate(cards, 1):
            path = out_dir / f"{args.name}-{i}.png"
            card.screenshot(path=str(path))
            print(f"  {args.name}-{i}.png ({path.stat().st_size // 1024} KB)")

        browser.close()

    from PIL import Image
    for i in range(1, len(cards) + 1):
        im = Image.open(out_dir / f"{args.name}-{i}.png")
        w, h = im.size
        expected_w, expected_h = args.width * args.scale, args.height * args.scale
        if w != expected_w or h != expected_h:
            print(f"  警告: {args.name}-{i}.png 尺寸 {w}x{h}, 预期 {expected_w}x{expected_h}")

    print(f"\n完成: {len(cards)} 张卡片 → {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
