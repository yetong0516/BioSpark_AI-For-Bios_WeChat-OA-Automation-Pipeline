#!/usr/bin/env python3
"""fetch_openfig.py — 从开放预印本(bioRxiv 等)抓论文原图，用于「顶刊精读」。

为什么需要它：Nature/Science 正刊图有付费墙+版权；开放的 bioRxiv 预印本图可署名转载，
但 bioRxiv 用 Cloudflare 人机验证挡住了 curl/requests（返回"Just a moment"挑战页）。
本脚本用 playwright 真浏览器内核过掉 Cloudflare，再在"已过验证的页面里"取图。

用法：
    python3 scripts/fetch_openfig.py <bioRxiv .full 页面URL> <输出目录> [最大图号=9]
例：
    python3 scripts/fetch_openfig.py \\
      https://www.biorxiv.org/content/10.64898/2026.02.10.704909v1.full \\
      drafts/2026-07-02_xxx/rawfigs 9

抓到的是 F1.jpg、F2.jpg…（论文主图）。best-effort：Cloudflare 偶尔仍会拦个别图，
多跑一两次或减小并发即可。抓到后自己挑一张有代表性的（通常 F1 是研究设计总图）
resize 进 images/figures/，正文图注注明"论文原图（bioRxiv 预印本）"。
"""
import re, sys, time, base64, os
from playwright.sync_api import sync_playwright

PAGE = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = sys.argv[2] if len(sys.argv) > 2 else "rawfigs"
MAXN = int(sys.argv[3]) if len(sys.argv) > 3 else 9
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# 在已过 Cloudflare 的页面里，用 <img>+canvas 把图转出来（走浏览器图片加载通道，不触发 XHR 挑战）
_JS = """async(u)=>{return await new Promise(res=>{const im=new Image();
im.onload=()=>{const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;
c.getContext('2d').drawImage(im,0,0);try{res(c.toDataURL('image/jpeg',0.92))}catch(e){res('TAINT')}};
im.onerror=()=>res('ERR');im.src=u;setTimeout(()=>res('TIMEOUT'),25000)})}"""


def main():
    if not PAGE:
        print("用法: fetch_openfig.py <预印本.full页URL> <输出目录> [最大图号]"); return 1
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(user_agent=UA, viewport={"width": 1400, "height": 1000})
        pg = ctx.new_page()
        pg.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
        for _ in range(20):                       # 等 Cloudflare 挑战过掉
            if "Just a moment" not in pg.title():
                break
            time.sleep(1.5)
        if "Just a moment" in pg.title():
            print("❌ 没能过 Cloudflare，稍后重试或改用浏览器扩展"); b.close(); return 2
        urls = pg.eval_on_selector_all("img,a",
            "els=>[...new Set(els.map(e=>e.src||e.href)"
            ".filter(u=>u&&/\\/F\\d+\\.large\\.jpg/.test(u)).map(u=>u.split('?')[0]))]")
        seen = {}
        for u in urls:
            m = re.search(r'/F(\d+)\.large\.jpg', u)
            if m:
                seen[int(m.group(1))] = u
        figs = [(k, seen[k]) for k in sorted(seen) if k <= MAXN]
        if not figs:
            print("⚠ 页面里没找到 .large.jpg 图链接（可能没渲染完），重跑一次试试"); b.close(); return 3
        got = 0
        for k, u in figs:
            data = None
            for _try in range(3):                 # 每张最多试 3 次
                data = pg.evaluate(_JS, u)
                if isinstance(data, str) and data.startswith("data:image"):
                    break
                time.sleep(2)
            if isinstance(data, str) and data.startswith("data:image"):
                raw = base64.b64decode(data.split(",", 1)[1])
                open(f"{OUT}/F{k}.jpg", "wb").write(raw)
                print(f"  F{k}: OK {len(raw)//1024}KB"); got += 1
            else:
                print(f"  F{k}: 失败({str(data)[:20]})")
            time.sleep(1.5)
        b.close()
        print(f"完成：{got}/{len(figs)} 张 → {OUT}")
        return 0 if got else 4


if __name__ == "__main__":
    sys.exit(main())
