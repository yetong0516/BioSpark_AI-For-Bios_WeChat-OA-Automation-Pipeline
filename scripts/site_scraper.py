#!/usr/bin/env python3
"""site_scraper.py — 抓取一个网站的所有图片和文字，分别存入 images/ 和 text/ 文件夹。

特性:
- 广告过滤: 广告域名黑名单 + DOM 特征(class/id token) + 追踪像素剔除，
  广告容器内的图片和文字都不会进入输出
- 防盗链: 图片请求自动携带 Referer
- 截图兜底: --render auto (默认) 时，SPA/JS 渲染页面自动用 playwright
  重新渲染提取；下载失败的图片在渲染页面中对 <img> 元素截图保存

用法:
    python3 site_scraper.py <URL> [--out DIR] [--depth N] [--max-pages N]
                            [--render auto|always|never] [--keep-ads]
                            [--max-image-mb N] [--timeout SEC] [--quiet]

输出结构:
    <out>/
    ├── images/          所有下载/截图的图片（按内容去重）
    ├── text/            每个页面一个 .txt（可见文字）+ metadata.json
    └── manifest.json    抓取清单（页面、图片映射、广告过滤记录、失败记录）
"""

import argparse
import copy
import hashlib
import io
import json
import mimetypes
import re
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

IMG_EXT_BY_MIME = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/svg+xml": ".svg", "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico", "image/avif": ".avif",
    "image/bmp": ".bmp", "image/tiff": ".tiff",
}

CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", re.I)

# ---------- 广告过滤规则 ----------

# 广告/追踪域名黑名单（匹配 host 或其父域）
AD_HOSTS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "adservice.google.com", "googletagservices.com", "2mdn.net",
    "amazon-adsystem.com", "taboola.com", "outbrain.com", "criteo.com",
    "criteo.net", "adnxs.com", "rubiconproject.com", "pubmatic.com",
    "openx.net", "moatads.com", "scorecardresearch.com",
    "adsafeprotected.com", "smartadserver.com", "yieldmo.com", "teads.tv",
    "adroll.com", "advertising.com", "adform.net", "casalemedia.com",
    "bidswitch.net", "mgid.com", "revcontent.com", "zemanta.com",
    # 中文广告联盟
    "pos.baidu.com", "cpro.baidu.com", "alimama.com", "tanx.com",
    "mediav.com", "irs01.com", "miaozhen.com",
}

# class/id 中表示广告的 token（按 - _ 空格 切分后精确匹配，避免误杀
# header/badge/gradient 等词；刻意不含 "banner"，hero banner 多为正文内容）
AD_TOKENS = {
    "ad", "ads", "adv", "advert", "adverts", "advertise", "advertising",
    "advertisement", "advertisements", "adsense", "adsbygoogle", "adslot",
    "adbox", "adframe", "adbanner", "adwrap", "adwrapper", "adcontainer",
    "sponsor", "sponsored", "sponsorship", "taboola", "outbrain",
    "doubleclick", "popunder", "popup-ad", "guanggao",  # 广告拼音
}

TOKEN_SPLIT_RE = re.compile(r"[-_\s]+")
CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")

# 页面 HTML 响应大小上限（防恶意超大响应 OOM）
MAX_HTML_BYTES = 50 * 1024 * 1024


def tokenize_attr(value):
    """按 camelCase / kebab-case / snake_case / 空格 统一切分为小写 token，
    使 adSection / ad-section / ad_section 都能命中 AD_TOKENS。"""
    return TOKEN_SPLIT_RE.split(CAMEL_RE.sub("-", value).lower())

# 追踪像素：HTML 宽高属性或实际像素 ≤ 此值则丢弃
TRACKING_PIXEL_MAX = 3
# SPA 判定：静态抓取可见文字少于此字符数则触发渲染
RENDER_TEXT_THRESHOLD = 200


def host_is_ad(url):
    host = (urlparse(url).netloc or "").lower().split(":")[0]
    parts = host.split(".")
    return any(".".join(parts[i:]) in AD_HOSTS for i in range(len(parts)))


def element_is_ad(tag):
    """class/id token 精确命中广告词，或 adsbygoogle 标记属性，或广告 iframe。"""
    if getattr(tag, "name", None) is None:
        return False
    if tag.get("data-ad-client") or tag.get("data-ad-slot"):
        return True
    attrs = []
    cls = tag.get("class")
    if cls:
        attrs.extend(cls if isinstance(cls, list) else [cls])
    v = tag.get("id")
    if v:
        attrs.append(v if isinstance(v, str) else " ".join(v))
    for a in attrs:
        for token in tokenize_attr(a):
            if token in AD_TOKENS:
                return True
    if tag.name == "iframe":
        src = tag.get("src") or ""
        if src and host_is_ad(src):
            return True
    return False


def strip_ads(soup):
    """从 soup 中移除广告元素，返回移除记录列表。"""
    removed = []
    for tag in soup.find_all(element_is_ad):
        desc = f"<{tag.name} class={tag.get('class')} id={tag.get('id')}>"
        removed.append(desc)
        tag.decompose()
    return removed


def log(msg, quiet=False):
    if not quiet:
        print(msg, flush=True)


def safe_name(text, maxlen=80):
    text = re.sub(r"[^\w\-.]+", "_", text, flags=re.U)
    return text[:maxlen].strip("_.") or "unnamed"


def is_http_url(url):
    try:
        return urlparse(url).scheme in ("http", "https")
    except ValueError:
        return False


def image_dims(data):
    """返回 (宽, 高)，识别失败返回 None。依赖 Pillow，缺失时返回 None。"""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:
        return None


class Renderer:
    """playwright 渲染器，懒启动、整个抓取过程复用一个浏览器实例。"""

    def __init__(self, timeout_ms=30000, quiet=False):
        self.timeout_ms = timeout_ms
        self.quiet = quiet
        self._pw = None
        self._browser = None
        self.available = None  # None=未尝试

    def _ensure(self):
        if self._browser is not None:
            return True
        if self.available is False:
            return False
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self.available = True
            return True
        except Exception as e:
            log(f"  [render] playwright 不可用: {e}", self.quiet)
            self.available = False
            return False

    def open_page(self, url):
        """渲染页面，返回 playwright page 对象（调用方负责 close）或 None。"""
        if not self._ensure():
            return None
        page = None
        try:
            page = self._browser.new_page(user_agent=UA)
            # domcontentloaded 先保证可用，networkidle 尽力等待（长轮询/
            # WebSocket 站点会一直有网络活动，等不到也不算失败）
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            return page
        except Exception as e:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            log(f"  [render] 渲染失败 {url}: {e}", self.quiet)
            return None

    def screenshot_images(self, page, wanted_urls):
        """在已渲染页面中找到 src 命中 wanted_urls 的 <img>，逐个截图。
        返回 {url: png_bytes}。"""
        shots = {}
        if page is None or not wanted_urls:
            return shots
        try:
            imgs = page.query_selector_all("img")
        except Exception:
            return shots
        for el in imgs:
            try:
                src = el.evaluate("e => e.currentSrc || e.src") or ""
                if src in wanted_urls and src not in shots:
                    el.scroll_into_view_if_needed(timeout=3000)
                    data = el.screenshot(timeout=5000)
                    if data:
                        shots[src] = data
            except Exception:
                continue
        return shots

    def close(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass


class SiteScraper:
    def __init__(self, start_url, out_dir, depth=1, max_pages=30,
                 max_image_mb=20, timeout=15, render="auto",
                 filter_ads=True, quiet=False):
        self.start_url = start_url
        self.out = Path(out_dir)
        self.img_dir = self.out / "images"
        self.txt_dir = self.out / "text"
        self.depth = depth
        self.max_pages = max_pages
        self.max_image_bytes = max_image_mb * 1024 * 1024
        self.timeout = timeout
        self.render_mode = render  # auto | always | never
        self.filter_ads = filter_ads
        self.quiet = quiet

        self.session = requests.Session()
        self.session.headers["User-Agent"] = UA
        self.renderer = Renderer(timeout_ms=max(timeout, 30) * 1000, quiet=quiet)

        self.domain = self._norm_host(urlparse(start_url).netloc)
        self.seen_pages = set()
        self.seen_img_urls = set()
        self.seen_img_hashes = {}  # content sha1 -> filename
        self.manifest = {
            "start_url": start_url,
            "pages": [],
            "images": [],
            "ads_filtered": [],
            "errors": [],
        }

    @staticmethod
    def _norm_host(netloc):
        host = netloc.lower()
        return host[4:] if host.startswith("www.") else host

    # ---------- 网络 ----------
    def fetch(self, url, stream=False, referer=None):
        headers = {"Referer": referer} if referer else None
        return self.session.get(url, timeout=self.timeout, stream=stream,
                                allow_redirects=True, headers=headers)

    # ---------- 图片收集 ----------
    def collect_image_urls(self, soup, base_url):
        """收集图片 URL，跳过广告域名与属性标明的追踪像素。"""
        raw = []

        for img in soup.find_all("img"):
            # 属性宽高 ≤3 视为追踪像素
            try:
                w = int(re.sub(r"\D", "", str(img.get("width") or "")) or 999)
                h = int(re.sub(r"\D", "", str(img.get("height") or "")) or 999)
                if w <= TRACKING_PIXEL_MAX and h <= TRACKING_PIXEL_MAX:
                    self._note_ad(img.get("src") or "", "tracking-pixel-attr")
                    continue
            except ValueError:
                pass
            for attr in ("src", "data-src", "data-original", "data-lazy-src"):
                v = img.get(attr)
                if v:
                    raw.append(v)
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                raw.extend(self._parse_srcset(srcset))

        for source in soup.find_all("source"):
            srcset = source.get("srcset")
            if srcset:
                raw.extend(self._parse_srcset(srcset))

        for meta in soup.find_all("meta"):
            prop = (meta.get("property") or meta.get("name") or "").lower()
            if prop in ("og:image", "twitter:image", "og:image:url"):
                v = meta.get("content")
                if v:
                    raw.append(v)

        for link in soup.find_all("link", rel=True):
            rels = " ".join(link.get("rel")).lower()
            if "icon" in rels or "apple-touch" in rels:
                v = link.get("href")
                if v:
                    raw.append(v)

        for tag in soup.find_all(style=True):
            raw.extend(CSS_URL_RE.findall(tag["style"]))
        for style in soup.find_all("style"):
            if style.string:
                raw.extend(CSS_URL_RE.findall(style.string))

        result = []
        for u in raw:
            u = u.strip()
            if not u or u.startswith(("data:", "javascript:", "about:")):
                continue
            absu = urldefrag(urljoin(base_url, u))[0]
            if not is_http_url(absu):
                continue
            if self.filter_ads and host_is_ad(absu):
                self._note_ad(absu, "ad-host")
                continue
            result.append(absu)
        return result

    @staticmethod
    def _parse_srcset(srcset):
        out = []
        for part in srcset.split(","):
            cand = part.strip().split()[0] if part.strip() else ""
            if cand:
                out.append(cand)
        return out

    def _note_ad(self, url, reason):
        if self.filter_ads:
            self.manifest["ads_filtered"].append({"url": url, "reason": reason})

    # ---------- 图片落盘 ----------
    def _save_image_bytes(self, data, img_url, page_url, method, ctype=""):
        """去重并写盘，返回是否新文件。"""
        digest = hashlib.sha1(data).hexdigest()
        if digest in self.seen_img_hashes:
            self.manifest["images"].append({
                "url": img_url, "page": page_url,
                "file": self.seen_img_hashes[digest], "dedup": True,
            })
            return False

        dims = image_dims(data)
        if dims and dims[0] <= TRACKING_PIXEL_MAX and dims[1] <= TRACKING_PIXEL_MAX:
            self._note_ad(img_url, f"tracking-pixel-{dims[0]}x{dims[1]}")
            return False

        upath = urlparse(img_url).path
        stem = safe_name(Path(upath).stem or "image")
        if method == "screenshot":
            ext = ".png"
        else:
            ext = Path(upath).suffix.lower()
            if not re.fullmatch(r"\.[a-z0-9]{2,5}", ext or ""):
                ext = IMG_EXT_BY_MIME.get(ctype) or mimetypes.guess_extension(ctype or "") or ".bin"
        fname = f"{stem}_{digest[:8]}{ext}"
        (self.img_dir / fname).write_bytes(data)
        self.seen_img_hashes[digest] = fname
        self.manifest["images"].append({
            "url": img_url, "page": page_url, "file": fname,
            "bytes": len(data), "method": method, "content_type": ctype,
        })
        log(f"  [{'shot' if method == 'screenshot' else 'img'}] {fname} ({len(data)//1024} KB)",
            self.quiet)
        return True

    def download_image(self, img_url, page_url):
        """下载图片；返回 None 表示成功/跳过，返回 img_url 表示失败待截图。"""
        if img_url in self.seen_img_urls:
            return None
        self.seen_img_urls.add(img_url)
        r = None
        try:
            r = self.fetch(img_url, stream=True, referer=page_url)
            r.raise_for_status()
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype and not ctype.startswith("image/"):
                return img_url  # 可能被防盗链替换成 HTML，交给截图兜底
            chunks, total = [], 0
            for chunk in r.iter_content(65536):
                total += len(chunk)
                if total > self.max_image_bytes:
                    raise ValueError(f"超过大小上限 {self.max_image_bytes} bytes")
                chunks.append(chunk)
            data = b"".join(chunks)
            if not data:
                return img_url
            self._save_image_bytes(data, img_url, page_url, "download", ctype)
            return None
        except ValueError as e:  # 尺寸超限：不值得截图重试
            self.manifest["errors"].append({"type": "image", "url": img_url, "error": str(e)})
            return None
        except Exception as e:
            self.manifest["errors"].append(
                {"type": "image", "url": img_url, "error": str(e), "fallback": "screenshot"})
            return img_url
        finally:
            if r is not None:
                r.close()

    # ---------- 文字 ----------
    def extract_text(self, soup, url, index, rendered=False):
        # 在副本上操作，避免 decompose 删掉原 soup 中 <noscript> 等里的链接，
        # 影响后续 collect_links 爬取
        work = copy.copy(soup)
        for tag in work(["script", "style", "noscript", "template"]):
            tag.decompose()
        title = (work.title.string or "").strip() if work.title and work.title.string else ""
        body_text = work.get_text(separator="\n")
        lines = [ln.strip() for ln in body_text.splitlines()]
        text = "\n".join(ln for ln in lines if ln)

        slug = safe_name(urlparse(url).path.strip("/").replace("/", "_") or "index")
        fname = f"{index:03d}_{slug}.txt"
        content = f"URL: {url}\nTITLE: {title}\n{'=' * 60}\n{text}\n"
        (self.txt_dir / fname).write_text(content, encoding="utf-8")
        log(f"  [txt] {fname} ({len(text)} chars{', rendered' if rendered else ''})", self.quiet)
        return {"url": url, "title": title, "text_file": fname,
                "chars": len(text), "rendered": rendered}

    # ---------- 链接 ----------
    def collect_links(self, soup, base_url):
        links = []
        for a in soup.find_all("a", href=True):
            absu = urldefrag(urljoin(base_url, a["href"]))[0]
            if is_http_url(absu) and self._norm_host(urlparse(absu).netloc) == self.domain:
                links.append(absu)
        return links

    # ---------- 单页处理 ----------
    def process_page(self, norm, page_index):
        """抓取单页：静态优先，必要时渲染 + 截图兜底。
        返回 (meta, soup_for_links) 或 (None, None)。"""
        soup = None
        static_failed = False
        try:
            r = self.fetch(norm, stream=True)
            try:
                r.raise_for_status()
                ctype = (r.headers.get("Content-Type") or "").lower()
                if "html" not in ctype:
                    return None, None
                chunks, total = [], 0
                for chunk in r.iter_content(65536):
                    total += len(chunk)
                    if total > MAX_HTML_BYTES:
                        raise ValueError(f"HTML 响应超过 {MAX_HTML_BYTES} bytes 上限")
                    chunks.append(chunk)
                soup = BeautifulSoup(b"".join(chunks), "lxml")
            finally:
                r.close()
        except Exception as e:
            self.manifest["errors"].append({"type": "page_static", "url": norm, "error": str(e)})
            static_failed = True
            if self.render_mode == "never":
                return None, None
            log(f"  [static] 失败 ({e})，尝试 playwright 渲染回退...", self.quiet)
        final_url = norm

        if soup is not None and self.filter_ads:
            for desc in strip_ads(soup):
                self._note_ad(desc, "ad-element@" + norm)

        img_urls = [] if soup is None else self.collect_image_urls(soup, final_url)
        skip_parents = {"script", "style", "noscript", "template"}
        static_chars = 0 if soup is None else sum(
            len("".join(s.split()))
            for s in soup.strings
            if s.strip() and getattr(s.parent, "name", None) not in skip_parents
        )

        rendered = False
        pw_page = None
        need_render = (
            static_failed
            or self.render_mode == "always"
            or (self.render_mode == "auto"
                and (static_chars < RENDER_TEXT_THRESHOLD or not img_urls))
        )
        if need_render:
            pw_page = self.renderer.open_page(norm)
            if pw_page is not None:
                try:
                    soup2 = BeautifulSoup(pw_page.content(), "lxml")
                    if self.filter_ads:
                        for desc in strip_ads(soup2):
                            self._note_ad(desc, "ad-element@" + norm)
                    soup = soup2
                    img_urls = self.collect_image_urls(soup, norm)
                    rendered = True
                except Exception as e:
                    self.manifest["errors"].append(
                        {"type": "render", "url": norm, "error": str(e)})

        # 下载图片，收集失败项
        failed = []
        for img_url in img_urls:
            miss = self.download_image(img_url, final_url)
            if miss:
                failed.append(miss)

        # 截图兜底
        if failed and self.render_mode != "never":
            if pw_page is None:
                pw_page = self.renderer.open_page(norm)
            shots = self.renderer.screenshot_images(pw_page, set(failed))
            for src, png in shots.items():
                self._save_image_bytes(png, src, final_url, "screenshot", "image/png")
                # 截图成功的，把先前的下载失败记录标记为已解决
                for err in self.manifest["errors"]:
                    if err.get("url") == src and err.get("fallback") == "screenshot":
                        err["resolved"] = True

        if pw_page is not None:
            try:
                pw_page.close()
            except Exception:
                pass

        if soup is None:
            self.manifest["errors"].append(
                {"type": "page", "url": norm, "error": "静态和渲染均失败"})
            return None, None

        meta = self.extract_text(soup, final_url, page_index, rendered=rendered)
        return meta, soup

    # ---------- 主流程 ----------
    def run(self):
        if not is_http_url(self.start_url):
            print(f"错误: 仅支持 http/https URL，收到: {self.start_url}", file=sys.stderr)
            return 2
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.txt_dir.mkdir(parents=True, exist_ok=True)

        queue = deque([(self.start_url, 0)])
        page_index = 0
        pages_meta = []

        try:
            while queue and page_index < self.max_pages:
                url, d = queue.popleft()
                norm = urldefrag(url)[0]
                if norm in self.seen_pages:
                    continue
                self.seen_pages.add(norm)

                log(f"[page {page_index + 1}] {norm}", self.quiet)
                meta, soup = self.process_page(norm, page_index + 1)
                if meta is None:
                    continue
                page_index += 1
                pages_meta.append(meta)
                self.manifest["pages"].append(meta)

                if d < self.depth and soup is not None:
                    for link in self.collect_links(soup, norm):
                        if urldefrag(link)[0] not in self.seen_pages:
                            queue.append((link, d + 1))
                time.sleep(0.2)  # 礼貌性间隔
        finally:
            self.renderer.close()

        (self.txt_dir / "metadata.json").write_text(
            json.dumps(pages_meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.out / "manifest.json").write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        n_img = len(self.seen_img_hashes)
        n_shot = sum(1 for i in self.manifest["images"] if i.get("method") == "screenshot")
        n_ads = len(self.manifest["ads_filtered"])
        n_err = len(self.manifest["errors"])
        log(f"\n完成: {page_index} 个页面, {n_img} 张图片 (其中截图 {n_shot}), "
            f"过滤广告 {n_ads} 项, {n_err} 个错误", self.quiet)
        log(f"图片目录: {self.img_dir}\n文字目录: {self.txt_dir}", self.quiet)
        return 0


def main():
    ap = argparse.ArgumentParser(description="抓取网站图片与文字到本地文件夹（带广告过滤与截图兜底）")
    ap.add_argument("url", help="起始网址 (http/https)")
    ap.add_argument("--out", default=None, help="输出目录 (默认 ./output/<域名>)")
    ap.add_argument("--depth", type=int, default=1,
                    help="同域名爬取深度, 0=仅当前页 (默认 1)")
    ap.add_argument("--max-pages", type=int, default=30, help="最多抓取页面数 (默认 30)")
    ap.add_argument("--render", choices=["auto", "always", "never"], default="auto",
                    help="playwright 渲染策略: auto=SPA/下载失败时兜底(默认), "
                         "always=每页都渲染, never=纯静态")
    ap.add_argument("--keep-ads", action="store_true", help="不过滤广告")
    ap.add_argument("--max-image-mb", type=int, default=20, help="单张图片大小上限 MB (默认 20)")
    ap.add_argument("--timeout", type=int, default=15, help="请求超时秒数 (默认 15)")
    ap.add_argument("--quiet", action="store_true", help="安静模式")
    args = ap.parse_args()

    out = args.out or str(Path("output") / safe_name(urlparse(args.url).netloc or "site"))
    scraper = SiteScraper(args.url, out, depth=args.depth, max_pages=args.max_pages,
                          max_image_mb=args.max_image_mb, timeout=args.timeout,
                          render=args.render, filter_ads=not args.keep_ads,
                          quiet=args.quiet)
    sys.exit(scraper.run())


if __name__ == "__main__":
    main()
