---
name: ai4s-xhs-pipeline
description: BioSpark 生物资讯日更产线。输入一个生物/生命科学主题（或让我自动找最新热点），经过新闻搜索 → 多源抓取 → 素材筛选 → 中文写稿 → 双平台产出（公众号长图文 + 小红书6卡片），停在人工审核闸等你点头，再由你手动发布。支持一天一篇定时。触发关键词：ai4s-xhs, 生物产线, BioSpark, 公众号, 小红书产线, 做一篇, 产线跑一遍, 从头做一篇, 今天的稿子, daily draft。
---

# ai4s-xhs-pipeline — BioSpark 生物资讯 → 公众号(+小红书) 日更产线

## 用途

一键从一个生物/生命科学主题，到一份**待人工审核的草稿包**（公众号 + 小红书双产出）：

- **输入**：一个生物主题（中/英文均可），或不提供主题（自动搜索最近 7 天热点）
- **输出**：`drafts/<date>_<slug>/` 完整草稿包
  - **公众号**：`gongzhonghao.html`（全内联样式，可粘贴）+ `gongzhonghao.md`（md 备份）+ `cover_gzh.png`（900×383 封面）
  - **小红书**：`card-1.png` ~ `card-6.png`（1080×1440 @2x，3:4 竖版）+ `caption.txt`
  - **共用**：`article.md`（中文长文）+ `images/figures/fig-*.jpg`（配图）+ `sources.json`（溯源）+ `REVIEW.md`（审核清单）
- **关键**：产线在阶段 6 **停下来等人工审核**，绝不自动发布。

## 触发条件

满足任一即使用：

1. 用户要求做生物/生命科学相关的公众号或小红书内容
2. 提到关键词：`ai4s-xhs`、生物产线、BioSpark、公众号、小红书产线、做一篇、产线跑一遍、从头做一篇、今天的稿子
3. 用户给出一个生物主题，要求生产内容
4. 由每日定时任务触发（见「日更模式」）

## 选题领域（生物 / 生命科学）

聚焦：分子生物学、结构生物学、基因组学、合成生物学、神经科学、免疫学、AI for biology（蛋白结构预测、单细胞、药物设计）、生态与进化。
**优先信源**：Nature / Science / Cell / bioRxiv / NIH / NEJM / Stanford Medicine / MIT News（生物方向）/ Broad Institute / EMBL。

---

## 产线流程（阶段 1–4 共享，阶段 5 分叉双平台，阶段 6 审核闸）

### 阶段 0：确定输出目录 + 读历史去重

1. 确定今天日期 `<date>`（YYYY-MM-DD）。
2. **读 `state/topic_history.jsonl`**（不存在则视为空、稍后创建）：收集所有历史 `topic_key` 和 `main_url`。
3. 选题时**跳过**历史里已出现的主题（任何 status 都算用过，避免重复）。
4. 选定后生成 `<slug>`（核心发现的英文 kebab-case），输出目录为 `drafts/<date>_<slug>/`。

### 阶段 1：新闻发现

**目标**：找到一篇有深度的生物新闻作为内容源。

1. 用 **WebSearch** 搜索用户给定主题（或搜 `biology breakthrough 2026`、`bioRxiv preprint <子领域>`、`Nature/Cell latest <子领域>`）
2. 搜索策略：用 2-3 个查询变体，优先最近 7 天
3. 选题标准：
   - 有具体研究成果（论文发表、实验数据）的报道优先
   - 有数字、引语、对比数据的优先（这些是去 AI 味的原料）
   - 信源要求：Nature/Science/Cell/bioRxiv/NIH/NEJM 等权威优先
   - **不得与 `topic_history.jsonl` 中已有主题重复**（阶段 0 已读）
4. 确定 1 篇主文章 + 3-5 个同主题报道源（不同网站，用于多源配图）

**产物**：主文章 URL + 同主题多源 URL 列表

### 阶段 2：多源素材抓取

**目标**：从多个新闻源并行抓取文字和图片素材。

**脚本路径**：`scripts/site_scraper.py`

1. 对主文章和各报道源**并行执行** scraper：
   ```bash
   SCRAPER=scripts/site_scraper.py
   python3 "$SCRAPER" "<URL>" --depth 0 --out drafts/<date>_<slug>/scrape/<source-name> --render auto --quiet &
   # ... 并行多个
   wait
   ```
2. 每个源输出到独立子目录，避免文件名冲突
3. scraper 已支持 403 自动回退 playwright 渲染（不需要额外处理）
4. 汇总各源的 `manifest.json`，统计成功/失败/图片数

**产物**：`drafts/<date>_<slug>/scrape/` 下多个素材目录

### 阶段 3：素材筛选与整合

**目标**：从抓取的所有图片中筛选出 3-5 张高质量配图。

1. 用 Python/PIL 扫描所有 `scrape/*/images/` 下的图片
2. 排除规则：
   - 宽 < 300px 或 高 < 200px（太小）
   - 文件 < 10KB（图标/追踪像素）
   - 文件名含 `logo`、`icon`、`avatar`、`brand`、`ad`、`banner`
   - 宽高比 > 5:1 或 < 1:5
3. 选图策略：
   - 优先真实照片（实验室/设备/人物/显微图），而非 AI 生成或示意图
   - 优先高分辨率（>= 1000px 宽）
   - 同一张图的不同尺寸只保留最大的
   - 至少 3 张不同内容的配图
4. 将筛选出的图片复制到 **`drafts/<date>_<slug>/images/figures/`** 并**按正文出现顺序**命名 `fig-1.jpg`、`fig-2.jpg`…（公众号正文占位 `【图N】` 与之对应）
5. 读取主文章 `text/*.txt` 提取完整文章内容

**产物**：`images/figures/fig-1..N` + 主文章全文

### 阶段 4：中文内容生产（共用底稿）

**目标**：基于英文原文写中文稿，供公众号和小红书共用。

#### 4a. 中文长文稿 `article.md`

写作要求：
- 像熟悉这个领域的人在跟朋友讲事
- **开头直接进事件或细节**，禁止「在当今……的时代」式起手
- 用原文的具体事实、数字、人名、引语说话
- 禁用词：赋能、抓手、闭环、底层逻辑、总而言之、综上所述、众所周知、值得注意的是、毫无疑问、干货满满、重新定义
- 不写「首先/其次/最后」三段式
- 结尾留一个具体问题，不写「总结」
- 字数 1500-2500 字

#### 4b. 小红书文案 `caption.txt`

- 3-5 句话概括核心发现
- 带 5-8 个话题标签（#AI4Science #生物 #领域标签 ...）
- 口语化，但有信息量

#### 4c. 数据溯源 `sources.json`

```json
{
  "topic": "主题",
  "topic_key": "核心发现-kebab-case",
  "main_source": {"title": "...", "url": "...", "published": "..."},
  "additional_sources": [...],
  "images": [
    {"file": "fig-1.jpg", "origin_url": "...", "source_site": "...", "license": "..."}
  ],
  "produced_at": "ISO8601"
}
```

**产物**：`article.md` + `caption.txt` + `sources.json`

---

### 阶段 5-GZH：公众号长图文生成 ⭐新增

**目标**：把 `article.md` 转写成一份**可直接粘进公众号后台**的带样式文章。

> **核心约束**：公众号编辑器粘贴时会**剥掉** `<style>` 块、`class`、外部 CSS，**只有内联 `style="..."` 能存活**。
> 所以**必须**严格照 [`templates/gzh_style.md`](templates/gzh_style.md) 的配方，给每个块内联 `style=`。

#### 5G-a. 写 `gongzhonghao.html`

1. **先读 [`templates/gzh_style.md`](templates/gzh_style.md)**，照里面的骨架和每类组件的内联样式配方写。
2. 结构：**顶部「往期精选」行**（gzh_style §0.5，不再放配乐）→ 板块标签 → **编者按/观点**（gzh_style §1.5，融入 BioSpark 自己的理解，推荐每篇都带）→ 导语（可省，被编者按替代）→ 若干分节(H2)小节 + 段落 + 引语/数据卡 + 配图 → **结尾互动话题卡**（gzh_style §9，必带）→ 来源页脚。
3. 每张配图位置放真 `<img src="images/figures/fig-N.jpg" ...>`（API 推送会自动把本地图上传到微信并替换 URL）。数量必须等于 `images/figures/` 里的图数。占位 div 版仅在走「手动粘贴」后备路径时才需要。
3b. **顶部「往期精选」**（已替代配乐，`从此不放歌`）：顶部放一行「往期精选，期待你的关注」+ 占位框；由审核者在编辑器用「超链接→公众号文章」插 2-3 篇**同板块**往期文章卡片（工具介绍配工具介绍…，卡片是微信内链、API/HTML 插不了）。
3c. **结尾互动话题卡**：针对本文抛一个具体、有张力的讨论问题，引导评论。
4. 末尾必带「来源页脚」，列主源（与 sources.json 一致）。
5. 不用 emoji；**统一用青绿 aqua 基准色书写**（`#4ecdc4` 及其浅色调），主题在 5G-e 一步切换。中性色：`#1a1a1a / #333 / #666 / #888 / #f8f9fa`。

#### 5G-b. 写预览版 `gongzhonghao_preview.html`（可选，方便审核看真图）

与上面一份相同，但把占位 div 换成真 `<img src="images/figures/fig-N.jpg" ...>`，仅供本地浏览器预览核对，**不**作粘贴源。

#### 5G-c. 写 `gongzhonghao.md`（纯 md 备份，mdnice/秀米 路径备用）

#### 5G-d. 写封面 `cover_gzh.html`

一个 `<div class="card card-cover-gzh">`，内联或外链 [`templates/gzh_cover.css`](templates/gzh_cover.css)（封面是截图源，可用 class/外链 CSS），含全幅配图 + 中文标题 + 领域标签。同样用 **aqua 基准色**写。

#### 5G-e. 定板块 + 套主题（见 [`templates/gzh_themes.md`](templates/gzh_themes.md)）

先定这篇属于哪个板块，主题色随之确定：
- **前沿科创**（前沿技术/工具/产业突破）→ `aqua`
- **顶刊精读**（单篇顶刊论文深读）→ `orange`
- **人物专访**（以人/团队为主角）→ `indigo`

正文顶部放对应**板块标签**（见 gzh_style.md §1），然后切主题：

```bash
python3 scripts/gzh_theme.py drafts/<date>_<slug>/ --theme <aqua|orange|indigo>
```

（一步把正文 + 封面 HTML 的主色整体换掉；aqua 则原样不变。）

约定：
- **`title.txt` 一律 `板块｜标题` 格式**（如 `前沿科创｜……`），方便订阅者在推送列表分栏。
- 板块名在三处统一出现：**标题前缀 + 封面左上标签（cover_gzh.html 的 `.tag`）+ 正文顶部胶囊**（gzh_style.md §1）。
- **每个分节标题都用新版组件**（序号 + 下划线 + 小导语，见 gzh_style.md §2）。

#### 5G-f. 生成封面 PNG `cover_gzh.png`（900×383 @2x，主题套用之后）

```bash
python3 scripts/screenshot_cards.py \
    drafts/<date>_<slug>/cover_gzh.html \
    --out drafts/<date>_<slug>/ \
    --width 900 --height 383 --name cover_gzh --scale 2
```
产出 `cover_gzh-1.png`，重命名/另存为 `cover_gzh.png`。

#### 5G-g. 校验 + 推草稿箱

```bash
python3 scripts/gzh_publish.py drafts/<date>_<slug>/              # 仅校验
python3 scripts/gzh_publish.py drafts/<date>_<slug>/ --draft-push # 校验通过后推到公众号草稿箱
```
`--draft-push` 走微信 `draft/add`：自动上传封面+正文配图、创建草稿，**只建草稿绝不群发**，落到后台草稿箱等人工审核后手动发布。需 `secrets/weixin.json` + 调用方 IP 在白名单内。

**产物**：`gongzhonghao.html` + `gongzhonghao.md` + `cover_gzh.png`（+ 可选 preview）+ 后台一条草稿

---

### 阶段 5-XHS：小红书卡片生成（保持原样）

**目标**：生成 6 张图文并茂的小红书卡片。**此路径与旧版完全一致，未改动。**

#### 5X-a. 卡片结构（固定 6 张）

| 卡片 | 类型 | CSS class | 内容 |
|---|---|---|---|
| card-1 | 封面 | `card-cover` | 全幅配图 + 标题 + 标签 + 来源 |
| card-2 | 内容 | `card-white` | 编号 01 + 背景/问题 + 配图 |
| card-3 | 内容 | `card-white` | 编号 02 + 核心方法/发现 + 时间线 |
| card-4 | 数据 | `card-white` | 编号 03 + 关键数字 + 对比表 |
| card-5 | 内容 | `card-white` | 编号 04 + 意义/影响 + 引语 |
| card-6 | 总结 | `card-dark` | 5 条要点 + 标签 + 来源 |

#### 5X-b. 编写 `_cards.html`

1. 引入 [`templates/xhs_cards.css`](templates/xhs_cards.css)（建议内联到 `<style>`，确保 file:// 加载）
2. 每张卡片是一个 `<div class="card card-xxx">`
3. 配图用 `images/figures/fig-N.jpg`
4. 可用组件：`.qbox`、`.data-row`、`.ctable`、`.timeline`
5. 避免 emoji；主色 `#4ecdc4`

#### 5X-c. 截图

```bash
python3 scripts/screenshot_cards.py drafts/<date>_<slug>/_cards.html --out drafts/<date>_<slug>/
```
（默认 1080×1440 @2x，行为与旧版一致。）

#### 5X-d. 质量检查

用 Read 查看至少 card-1 和 card-4：图片正常、中文渲染正确、尺寸 2160×2880。

**产物**：`card-1.png` ~ `card-6.png` + `_cards.html`

---

### 阶段 6：人工审核闸 ⭐新增（必须停在这里）

**目标**：产线在此**停下**，把草稿包交给人工审核，**绝不自动发布、绝不移动到 `published/`、绝不调用任何发布 API**。

#### 6a. 生成 `REVIEW.md`

在 `drafts/<date>_<slug>/REVIEW.md` 写审核清单（模板见下「REVIEW.md 模板」）。

#### 6b. 追加历史

向 `state/topic_history.jsonl` 追加一行（**append，不要重写整个文件**）：
```json
{"date":"<date>","topic_key":"<key>","topic":"<中文主题>","main_url":"<主源URL>","source_site":"<域名>","status":"drafted","slug":"<slug>"}
```

#### 6c. 向用户呈现（轻量，一屏内）

1. 一句话摘要：选题 + 为何选它 + 主源 URL + 日期
2. 用 Read 内联预览 `cover_gzh.png`、`card-1.png`、`card-4.png`
3. 公众号正文前 ~200 字 + 小红书 caption
4. 打开提示：在浏览器打开 `drafts/<date>_<slug>/gongzhonghao_preview.html`（看真图）
5. `REVIEW.md` 路径
6. 末尾一句：**回复「approve」发布 / 「edit: …」修改 / 「skip」放弃今天这条**

#### 6d. 审核循环

- **approve** → ① **立即自动推草稿箱**：`python3 scripts/gzh_publish.py <draft> --draft-push`（默认动作，别问、别让用户复制粘贴、别打印手动清单；梯子保持原样直推，见 memory [[never-touch-proxy]]）；成功后把返回的 draft media_id 报给用户；② 向 `state/review_log.md` 追加一行（日期/slug/approved/备注）；③ 向 `topic_history.jsonl` 追加 `status:"published"` 一行；④ 提醒用户：草稿箱已就绪，去后台核对后手动点「发布」；顶部「往期精选」占位框需在编辑器手动插同板块往期文章卡片；发布后把目录移到 `published/`。仅当 `--draft-push` 报错（如 IP 白名单/凭证）才如实报告、把本地草稿留着，**绝不**擅自关梯子、**绝不**回退成「让用户复制粘贴」当默认。
- **edit: <说明>** → 只就地重生成受影响产物（如只改标题就只改 html/cover），更新 `REVIEW.md`，重新呈现 6c。向 `review_log.md` 记 `edit`。
- **skip** → 草稿留在 `drafts/`；向 `topic_history.jsonl` 追加 `status:"skipped"`（明天不再选它）。

#### REVIEW.md 模板

```markdown
# 审核清单 — <date> <中文主题>

## 公众号
- [ ] 标题准确、不标题党
- [ ] 正文 1500-2500 字，无 AI 味禁用词
- [ ] 数字/人名/引语与原文一致（核对 sources.json）
- [ ] 配图 fig-1..N 已就绪，来源标注正确
- [ ] cover_gzh.png 主题相符、文字清晰
- [ ] 结尾互动话题卡：问题具体、能引发讨论
- [ ] **顶部「往期精选，期待你的关注」下，在编辑器用「超链接→公众号文章」插 2-3 篇同板块往期文章卡片**（微信内链，API 插不了，唯一手动步骤；已不再放配乐）
- [ ] 浏览器打开 gongzhonghao.html，全选复制粘贴样式正常

## 小红书
- [ ] card-1 封面正常、标题准确
- [ ] card-4 数据正确
- [ ] 6 张卡片中文渲染无方块
- [ ] caption 话题标签合适

## 溯源
- [ ] 主源与各配图来源 URL 在 sources.json 可追溯
- [ ] 与历史选题无重复（topic_history.jsonl）

回复「approve」发布 / 「edit: …」修改 / 「skip」放弃今天这条
```

---

## 日更模式（一天一篇）

由定时任务每天触发，**自包含**地跑一遍阶段 0–6，产出一份草稿后**停在阶段 6**，发通知给用户。
**定时跑只产草稿 + 通知，永不发布**——发布永远是用户审核后的独立人工动作。

定时任务提示词要点（详见 `scripts/setup_daily_task.md` 若存在，或下方）：
1. 读 `state/topic_history.jsonl` 去重
2. 生物信源搜近 7 天，选一个**新**主题
3. 跑阶段 1–4 + 5-GZH + 5-XHS 写进 `drafts/<today>_<slug>/`
4. 追加历史 `status: drafted`
5. **停在审核闸**，生成 `REVIEW.md`，不发布、不移 published、不调 API
6. 通知用户：选题 + 一句为何 + 草稿路径 + 审核清单

---

## 关键约束

### 网络环境
本机 curl/openssl 无法直接访问部分外网（TLS 指纹过滤），但 playwright/Chromium 可以。scraper 的 `--render auto` 已处理（静态 403 自动回退渲染）。

### 公众号发布（当前模式：approve 后自动直推草稿箱）
- **凭证已配齐**（`secrets/weixin.json` 有 appId/appSecret，用户已把真实/节点 IP 加进公众号白名单、并把 `api.weixin.qq.com` 设为 FlClash 直连）。所以 **approve 的默认动作就是自动 `gzh_publish.py --draft-push`**，一步把封面+正文配图上传、创建草稿，落到后台草稿箱。**不要**再让用户复制粘贴 HTML、也不要打印手动清单——那是旧模式，已废弃。
- `--draft-push` 会自动上传图片，正文里的 `【图N】` 占位在推送时由脚本处理；用户无需手动逐张传图。
- **绝不碰梯子**：直推靠 FlClash 直连规则，梯子开着就能成，禁用 `scripts/push_wechat.sh`（它会关梯子）。见 memory [[never-touch-proxy]]。
- **唯一仍需人工在编辑器做的**：顶部「往期精选」占位框，用「超链接→公众号文章」插同板块往期文章卡片（微信内链，API 插不了）。
- 后备：仅当 `--draft-push` 失败（IP 白名单/凭证/网络）才如实报告，把本地草稿留着让用户定夺；手动复制粘贴只作应急后备，**不作默认**。

### 图片质量
优先真实照片/显微图/实验图，拒绝明显 AI 生成图；每图需标来源；封面必须有全幅配图。

### 文风
不端着、不汇报腔、不 AI 味；用原文数据说话；引语保留原文含义、用中文重新表达。

---

## 目录结构

```
ai4s_pipeline/
├── SKILL.md                      本文件
├── scripts/
│   ├── site_scraper.py           多源抓取（阶段2）
│   ├── screenshot_cards.py       卡片/封面截图（支持 --width/--height/--name）
│   └── gzh_publish.py            公众号草稿校验 + 手动发布清单（不碰 API）
├── templates/
│   ├── xhs_cards.css             小红书卡片样式
│   ├── gzh_style.md              公众号内联样式契约（粘贴存活）
│   └── gzh_cover.css             公众号封面样式（900×383）
├── state/
│   ├── topic_history.jsonl       选题去重台账
│   └── review_log.md             人工审核日志
├── drafts/                       待审核草稿
│   └── <date>_<slug>/
│       ├── gongzhonghao.html         公众号粘贴源（占位图版）
│       ├── gongzhonghao_preview.html 公众号预览（真图版，可选）
│       ├── gongzhonghao.md           md 备份
│       ├── cover_gzh.png             公众号封面 900×383@2x
│       ├── card-1.png ~ card-6.png   小红书卡片
│       ├── _cards.html               小红书卡片源码
│       ├── caption.txt               小红书文案
│       ├── article.md                中文长文（共用底稿）
│       ├── images/figures/fig-*.jpg  配图
│       ├── sources.json              溯源
│       ├── REVIEW.md                 审核清单
│       └── scrape/                   原始抓取素材
├── published/                    审核通过并发布后移入这里
└── output/                       （旧）手动单跑兼容目录，仍可用
```

## 依赖

- Python 3.9+（脚本兼容），requests, beautifulsoup4, lxml, Pillow
- playwright (chromium)
- 字体：Microsoft YaHei 或 SimHei（中文渲染）

## 示例调用

```
用户: 用 BioSpark 给 AlphaFold3 最新进展做今天的稿子
AI:   [触发 ai4s-xhs-pipeline]
      阶段0: 读 topic_history.jsonl 去重 → 确定 drafts/2026-06-19_alphafold3-xxx/
      阶段1: WebSearch → 找到 Nature 报道 ...
      阶段2: 并行抓取 Nature/Cell/Broad ...
      阶段3: 筛 4 张配图 → images/figures/fig-1..4
      阶段4: 写 article.md + caption + sources.json
      阶段5-GZH: 写 gongzhonghao.html（内联样式）+ 封面 → gzh_publish.py 校验
      阶段5-XHS: 写 _cards.html → 6 张卡片 → 质量检查
      阶段6: 生成 REVIEW.md，追加历史 drafted，呈现预览 → 停下等审核
      用户: approve
      AI:   记 review_log + 历史 published + 打印手动发布清单
```
