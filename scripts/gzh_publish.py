#!/usr/bin/env python3
"""gzh_publish.py — 公众号草稿包校验 + 推送到草稿箱。

两种模式：
  1. 默认（校验 + 手动发布清单）：不碰任何微信 API，只校验草稿目录是否齐全合规，
     并打印「人工把它发到公众号」的逐步清单。任何公众号都能用。
  2. --draft-push（认证公众号 API）：把文章推到公众号【草稿箱】（draft/add 接口）。
     只创建草稿，**绝不自动群发** —— 你在公众号后台审核后再手动点「发布」。
     这一步天然契合「人工审核」要求。

凭证（仅 --draft-push 需要）放在 secrets/weixin.json：
    {"appId":"...","appSecret":"...","author":"BioSpark",
     "needOpenComment":1,"onlyFansCanComment":0}
见 secrets/weixin.example.json 模板。weixin.json 已被 .gitignore 忽略。

用法:
    python3 scripts/gzh_publish.py <draft_dir>                  # 校验 + 清单
    python3 scripts/gzh_publish.py <draft_dir> --json           # 机器可读校验
    python3 scripts/gzh_publish.py <draft_dir> --check-token    # 仅测连通性（取 access_token）
    python3 scripts/gzh_publish.py <draft_dir> --draft-push     # 推到草稿箱
    python3 scripts/gzh_publish.py <draft_dir> --draft-push --title "标题"

草稿目录约定:
    gongzhonghao.html   正文（带内联 style=）。配图可写成 <img src="images/figures/fig-N.jpg">，
                        或沿用占位 <figure>…【图N：fig-N.jpg …】…</figure> 块 —— 两种都会被
                        自动上传到微信并替换成微信图片 URL。
    cover_gzh.png       封面图（1800x766），作为草稿 thumb。
    title.txt           标题（首行）。也可用 --title 覆盖。
    article.md          正文同源稿（用于字数校验 + 自动摘要）。
    sources.json        溯源（main_source.url 作为「阅读原文」链接）。
    images/figures/     配图。
"""

import argparse
import json
import re
import sys
from pathlib import Path

MIN_WORDS, MAX_WORDS = 1200, 2600   # 科普文英文术语多，粗计字数偏低，下限设 1200
COVER_W, COVER_H = 1800, 766          # 900x383 @2x
MIN_FIGURES = 3
BANNED = ["赋能", "抓手", "闭环", "底层逻辑", "总而言之", "综上所述",
          "众所周知", "毫无疑问", "干货满满", "重新定义"]

API = "https://api.weixin.qq.com/cgi-bin"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS = PROJECT_ROOT / "secrets" / "weixin.json"

_WX_SESSION = None


def _wx():
    """微信接口专用会话：直连（trust_env=False 绕开本机 Clash/VPN 代理）。
    微信是腾讯国内服务器，国内机器直连最稳；代理的境外节点上传大文件易断。
    直连时出口 IP = 本机真实公网 IP，需把它加进公众号 IP 白名单。"""
    global _WX_SESSION
    if _WX_SESSION is None:
        import requests
        s = requests.Session()
        s.trust_env = False
        _WX_SESSION = s
    return _WX_SESSION


def _cn_word_count(text: str) -> int:
    """粗略中文字数：中文字符 + 连续英文/数字串各计一。"""
    cn = len(re.findall(r"[一-鿿]", text))
    en = len(re.findall(r"[A-Za-z0-9]+", text))
    return cn + en


# --------------------------------------------------------------------------- #
#  校验（两种模式共用）
# --------------------------------------------------------------------------- #
def validate(draft: Path) -> dict:
    checks = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    html = draft / "gongzhonghao.html"
    if html.exists():
        h = html.read_text(encoding="utf-8", errors="ignore")
        n_style = h.count("style=")
        has_blocked = ("<style" in h.lower())
        add("gongzhonghao.html 存在", True)
        add("内联 style= 数量 >= 8（粘贴存活）", n_style >= 8, f"找到 {n_style} 处")
        add("未依赖 <style> 块", not has_blocked,
            "发现 <style> 块——粘进公众号会丢样式" if has_blocked else "")
        n_fig_ph = len(re.findall(r"【图\s*\d+", h))
    else:
        add("gongzhonghao.html 存在", False, "缺文件")
        n_fig_ph = 0

    art = draft / "article.md"
    if art.exists():
        a = art.read_text(encoding="utf-8", errors="ignore")
        wc = _cn_word_count(a)
        add(f"article.md 字数 {MIN_WORDS}-{MAX_WORDS}", MIN_WORDS <= wc <= MAX_WORDS, f"{wc} 字")
        hit = [w for w in BANNED if w in a]
        add("无 AI 味禁用词", not hit, ("命中: " + "、".join(hit)) if hit else "")
    else:
        add("article.md 存在", False, "缺文件")

    cover = draft / "cover_gzh.png"
    if cover.exists():
        try:
            from PIL import Image
            cw, ch = Image.open(cover).size
            add("cover_gzh.png 尺寸 1800x766", (cw, ch) == (COVER_W, COVER_H), f"{cw}x{ch}")
        except ImportError:
            add("cover_gzh.png 尺寸校验", False, "未装 Pillow，跳过")
    else:
        add("cover_gzh.png 存在", False, "缺封面")

    figdir = draft / "images" / "figures"
    figs = sorted(figdir.glob("fig-*.*")) if figdir.exists() else []
    add(f"配图 >= {MIN_FIGURES} 张", len(figs) >= MIN_FIGURES, f"{len(figs)} 张")
    if html.exists():
        n_img = len(re.findall(r"<img\b", h, re.I))
        # 占位或 <img> 二者其一对得上配图数即可
        ok_ref = (n_fig_ph == len(figs)) or (n_img == len(figs))
        add("正文配图引用数 == 配图数", ok_ref,
            f"占位 {n_fig_ph} / <img> {n_img} / 配图 {len(figs)}")

    sj = draft / "sources.json"
    if sj.exists():
        try:
            data = json.loads(sj.read_text(encoding="utf-8"))
            url = (data.get("main_source") or {}).get("url")
            add("sources.json 可解析且有主源 URL", bool(url), url or "缺 main_source.url")
        except json.JSONDecodeError as e:
            add("sources.json 可解析", False, str(e))
    else:
        add("sources.json 存在", False, "缺文件")

    passed = all(c["ok"] for c in checks)
    return {"draft": str(draft), "passed": passed, "checks": checks}


def print_human(result: dict):
    print(f"\n=== 草稿校验: {result['draft']} ===\n")
    for c in result["checks"]:
        mark = "✅" if c["ok"] else "❌"
        line = f"  {mark} {c['name']}"
        if c["detail"]:
            line += f"  — {c['detail']}"
        print(line)

    print()
    if result["passed"]:
        print("校验通过。两种发布方式：")
        print("  [A] 全自动推草稿箱（认证公众号）：")
        print("      scripts/push_wechat.sh <draft>    ← 推荐：自动关梯子直连、传完再开，绝不掉线")
        print("      （或 python3 scripts/gzh_publish.py <draft> --draft-push，梯子开着大文件可能被境外节点掐断）")
        print("      文章进入后台【草稿箱】，你审核后手动点「发布」。")
        print("  [B] 手动粘贴（任何公众号）：")
        print("      1. 浏览器打开 gongzhonghao.html → 全选(⌘A)复制(⌘C)。")
        print("      2. 公众号后台 → 新建图文 → 正文粘贴(⌘V)。")
        print("      3. 按【图N】占位逐张上传 images/figures/fig-N.jpg。")
        print("      4. 上传 cover_gzh.png 作封面，标题栏单独填标题。")
        print("      5. 核对无误 → 保存草稿 / 发布。")
        print("  发布后把草稿目录移到 published/，在 topic_history.jsonl 标 published。")
    else:
        print("❌ 校验未通过，请先修复上面标红项，再发布。")


# --------------------------------------------------------------------------- #
#  微信 API（仅 --draft-push / --check-token）
# --------------------------------------------------------------------------- #
class WeixinError(RuntimeError):
    pass


def _load_creds() -> dict:
    if not SECRETS.exists():
        raise WeixinError(
            f"缺凭证文件 {SECRETS}\n"
            f"  请复制 secrets/weixin.example.json 为 secrets/weixin.json 并填入 AppID/AppSecret。")
    try:
        c = json.loads(SECRETS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise WeixinError(f"{SECRETS} 不是合法 JSON: {e}")
    if not c.get("appId") or not c.get("appSecret"):
        raise WeixinError(f"{SECRETS} 里 appId / appSecret 未填。")
    return c


def _hint_for_errcode(code: int, msg: str) -> str:
    hints = {
        40164: "调用方 IP 不在白名单。把下面这个 IP 加到 公众号后台→设置与开发→基本配置→IP白名单。",
        40125: "AppSecret 不对。去 基本配置 重置 AppSecret，更新 secrets/weixin.json。",
        40013: "AppID 不对。核对 基本配置 里的 AppID。",
        48001: "接口未授权。你的公众号可能没有「草稿箱/素材管理」接口权限（需已认证）。",
        45009: "接口调用频率超限（每日额度用完），明天再试或检查是否有脚本在刷。",
        41001: "缺 access_token。",
    }
    return hints.get(code, "")


def _check_wx(resp_json: dict, where: str):
    code = resp_json.get("errcode", 0)
    if code and code != 0:
        msg = resp_json.get("errmsg", "")
        hint = _hint_for_errcode(code, msg)
        extra = ""
        if code == 40164:
            ip = re.search(r"(\d+\.\d+\.\d+\.\d+)", msg)
            if ip:
                extra = f"\n      → 需加白名单的 IP：{ip.group(1)}"
        raise WeixinError(f"[{where}] 微信返回 errcode={code} errmsg={msg}"
                          + (f"\n  提示：{hint}{extra}" if hint else ""))


def get_access_token(appid: str, secret: str) -> str:
    r = _wx().get(f"{API}/token", params={
        "grant_type": "client_credential", "appid": appid, "secret": secret,
    }, timeout=20)
    j = r.json()
    _check_wx(j, "get_access_token")
    tok = j.get("access_token")
    if not tok:
        raise WeixinError(f"未取到 access_token：{j}")
    return tok


def _upload_file(url: str, path: Path, field="media"):
    import mimetypes
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    with open(path, "rb") as f:
        r = _wx().post(url, files={field: (path.name, f, mime)}, timeout=60)
    j = r.json()
    return j


def _shrink_if_needed(path: Path, limit=1020000) -> Path:
    """微信 uploadimg 单图上限 1MB。超限则等比缩 + 降质重存到临时文件。"""
    if path.stat().st_size <= limit:
        return path
    try:
        from PIL import Image
    except ImportError:
        return path
    img = Image.open(path).convert("RGB")
    tmp = path.with_name("_wxtmp_" + path.stem + ".jpg")
    w, h = img.size
    for scale in (1.0, 0.85, 0.7, 0.55):
        rw = max(640, int(w * scale))
        resized = img.resize((rw, int(h * rw / w)), Image.LANCZOS) if scale < 1.0 else img
        for q in (85, 75, 65):
            resized.save(tmp, "JPEG", quality=q, optimize=True)
            if tmp.stat().st_size <= limit:
                return tmp
    return tmp  # 已是最小尝试


def upload_body_image(token: str, path: Path) -> str:
    """正文内图片 → 返回微信图片 URL（不占素材库）。"""
    path = _shrink_if_needed(path)
    j = _upload_file(f"{API}/media/uploadimg?access_token={token}", path)
    _check_wx(j, f"uploadimg {path.name}")
    if not j.get("url"):
        raise WeixinError(f"uploadimg 未返回 url：{j}")
    return j["url"]


def upload_thumb(token: str, path: Path) -> str:
    """封面 → 永久图片素材，返回 media_id 作 thumb_media_id。"""
    j = _upload_file(f"{API}/material/add_material?access_token={token}&type=image", path)
    _check_wx(j, "add_material(thumb)")
    if not j.get("media_id"):
        raise WeixinError(f"add_material 未返回 media_id：{j}")
    return j["media_id"]


def _resolve_img(draft: Path, ref: str):
    """把正文里引用的图片名/相对路径解析成真实文件。"""
    ref = ref.strip().split("?")[0]
    for cand in (draft / ref, draft / "images" / "figures" / Path(ref).name, draft / Path(ref).name):
        if cand.exists():
            return cand
    return None


def rewrite_images(content: str, draft: Path, token: str) -> tuple:
    """把正文里的本地图片（占位 figure 块 + <img src=本地>）上传到微信、替换为微信 URL。"""
    cache: dict = {}
    uploaded = []
    warnings = []

    def up(local: Path) -> str:
        key = str(local)
        if key not in cache:
            cache[key] = upload_body_image(token, local)
            uploaded.append(local.name)
        return cache[key]

    # 1) 占位 figure 块：<figure ...> …【图N：fig-N.jpg …】… <figcaption>…</figcaption> </figure>
    def repl_figure(m):
        block = m.group(0)
        inner = m.group(1)
        fn = re.search(r"(fig-[\w\-]+\.\w+)", inner)
        if not fn:
            return block  # 没认出文件名，原样保留
        local = _resolve_img(draft, fn.group(1))
        if not local:
            warnings.append(f"占位引用 {fn.group(1)} 找不到对应文件，跳过")
            return block
        url = up(local)
        cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, re.S | re.I)
        cap_html = (f'<figcaption style="font-size:13px;color:#888;text-align:center;'
                    f'margin-top:8px;line-height:1.6;">{cap.group(1).strip()}</figcaption>'
                    if cap else "")
        return (f'<figure style="margin:24px 0;">'
                f'<img src="{url}" style="width:100%;border-radius:8px;display:block;">'
                f'{cap_html}</figure>')

    content = re.sub(r"<figure\b[^>]*>(.*?)</figure>", repl_figure, content, flags=re.S | re.I)

    # 2) 仍是本地路径的 <img src="...">
    def repl_img(m):
        src = m.group(2)
        if src.startswith("http://") or src.startswith("https://"):
            return m.group(0)
        local = _resolve_img(draft, src)
        if not local:
            warnings.append(f"<img src={src}> 找不到对应文件，跳过")
            return m.group(0)
        return m.group(1) + up(local) + m.group(3)

    content = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)("[^>]*>)', repl_img, content, flags=re.I)
    return content, uploaded, warnings


def _extract_body(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    return (m.group(1) if m else html).strip()


_BLOCKS = "p|h1|h2|h3|div|section|figure|figcaption|td|th|li|blockquote|ul|ol"


def _strip_block_ws(html: str) -> str:
    """删掉块级元素开标签后 / 闭标签前的源码换行缩进。
    否则微信导入时会把 <p> 后的源码缩进(如 '\\n    ')当成正文的一部分渲染出来，
    叠加 text-indent 后，原有段缩进会比"回车新起的段"多两格，全篇不齐。"""
    html = re.sub(rf'(<(?:{_BLOCKS})\b[^>]*>)[ \t]*\n[ \t]*', r'\1', html)
    html = re.sub(rf'[ \t]*\n[ \t]*(</(?:{_BLOCKS})>)', r'\1', html)
    return html


def _read_title(draft: Path, override) -> str:
    if override:
        return override.strip()
    tf = draft / "title.txt"
    if tf.exists():
        for line in tf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip()
    sj = draft / "sources.json"
    if sj.exists():
        try:
            return (json.loads(sj.read_text(encoding="utf-8")).get("topic") or "").strip() or "未命名"
        except json.JSONDecodeError:
            pass
    return "未命名"


def _auto_digest(draft: Path) -> str:
    art = draft / "article.md"
    if not art.exists():
        return ""
    text = re.sub(r"[#>*`\-\n\r]+", " ", art.read_text(encoding="utf-8"))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:100]


def draft_push(draft: Path, title_override=None) -> dict:
    creds = _load_creds()
    html_path = draft / "gongzhonghao.html"
    cover = draft / "cover_gzh.png"
    if not html_path.exists():
        raise WeixinError("缺 gongzhonghao.html")
    if not cover.exists():
        raise WeixinError("缺 cover_gzh.png（草稿封面必需）")

    print("· 获取 access_token …")
    token = get_access_token(creds["appId"], creds["appSecret"])

    print("· 上传封面缩略图 …")
    thumb_id = upload_thumb(token, cover)

    print("· 上传正文配图 …")
    content = _strip_block_ws(_extract_body(html_path.read_text(encoding="utf-8")))
    content, uploaded, warnings = rewrite_images(content, draft, token)
    for w in warnings:
        print(f"  ⚠ {w}")
    print(f"  上传了 {len(uploaded)} 张正文图：{', '.join(uploaded) or '(无)'}")

    title = _read_title(draft, title_override)
    digest = _auto_digest(draft)
    source_url = ""
    sj = draft / "sources.json"
    if sj.exists():
        try:
            source_url = (json.loads(sj.read_text(encoding="utf-8")).get("main_source") or {}).get("url", "")
        except json.JSONDecodeError:
            pass

    article = {
        "title": title[:64],
        "author": creds.get("author", "BioSpark"),
        "digest": digest,
        "content": content,
        "content_source_url": source_url,
        "thumb_media_id": thumb_id,
        "need_open_comment": int(creds.get("needOpenComment", 1)),
        "only_fans_can_comment": int(creds.get("onlyFansCanComment", 0)),
    }

    print(f"· 创建草稿（标题：{title}）…")
    body = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    r = _wx().post(f"{API}/draft/add?access_token={token}", data=body,
                   headers={"Content-Type": "application/json"}, timeout=60)
    j = r.json()
    _check_wx(j, "draft/add")
    media_id = j.get("media_id")
    print(f"\n✅ 草稿已创建，draft media_id = {media_id}")
    print("   打开公众号后台 → 草稿箱，即可看到这篇。审核无误后手动点「发布」。")
    print("   （本脚本只建草稿，绝不自动群发。）")
    return {"media_id": media_id, "title": title, "uploaded": uploaded}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="公众号草稿校验 + 推草稿箱")
    ap.add_argument("draft", help="草稿目录，如 drafts/2026-06-29_xxx")
    ap.add_argument("--json", action="store_true", help="输出机器可读校验 JSON")
    ap.add_argument("--check-token", action="store_true",
                    help="仅测连通性：用 secrets/weixin.json 取 access_token")
    ap.add_argument("--draft-push", action="store_true",
                    help="推到公众号草稿箱（draft/add，仅建草稿不群发）")
    ap.add_argument("--title", default=None, help="覆盖标题（否则读 title.txt）")
    args = ap.parse_args()

    draft = Path(args.draft).resolve()

    if args.check_token:
        try:
            creds = _load_creds()
            tok = get_access_token(creds["appId"], creds["appSecret"])
            print(f"✅ 连通正常，access_token 取到（前12位）：{tok[:12]}…")
            return 0
        except WeixinError as e:
            print(f"❌ {e}", file=sys.stderr)
            return 2

    if not draft.is_dir():
        print(f"错误: 目录不存在: {draft}", file=sys.stderr)
        return 1

    # 推草稿箱前先跑校验，挡掉残缺草稿
    if args.draft_push:
        result = validate(draft)
        if not result["passed"]:
            print_human(result)
            print("\n❌ 校验未通过，已中止推送。修复后重试。", file=sys.stderr)
            return 1
        try:
            draft_push(draft, args.title)
            return 0
        except WeixinError as e:
            print(f"\n❌ 推送失败：{e}", file=sys.stderr)
            return 2

    result = validate(draft)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
