# 公众号内联样式契约（gzh_style）

> 这不是 CSS 文件，**不能**用 `<link>`/`<style>`/`class`。
> 微信公众号网页编辑器在「全选复制粘贴」时会**剥掉** `<style>` 块、`<link>`、`class` 和一切外部 CSS，
> **只有写在每个元素上的内联 `style="..."` 能存活**。
> 所以 `gongzhonghao.html` 必须给每一个块都内联 `style=`，照下面的配方抄。
> 品牌色与 [`xhs_cards.css`](xhs_cards.css) 一致，两平台一个观感：主色 `#4ecdc4`、标题 `#1a1a1a`、正文 `#333`、引语/数据卡浅灰底。

---

## 0. 文件骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>公众号草稿</title></head>
<body style="margin:0;background:#f5f5f5;">
<!-- 外层容器：677px 是公众号正文实际宽度 -->
<section style="max-width:677px;margin:0 auto;padding:24px 20px;background:#fff;font-family:-apple-system,'PingFang SC','HarmonyOS Sans SC','Source Han Sans SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif;font-size:16px;line-height:1.75;color:#333;word-break:break-word;">

  <!-- 标题（粘贴进公众号后，公众号标题栏单独填，这里的 h1 仅正文导语用，可选） -->
  <!-- 正文从这里开始，按下面各组件拼 -->

</section>
</body>
</html>
```

> 注意：公众号文章**标题**是在后台单独的标题输入框里填的，不在正文里。
> 正文里可以放一个「导语 / 一句话摘要」，但不要再放一个大 H1 标题（会重复）。

---

## 0.5 顶部「往期精选」位（每篇最前面）⭐已替换配乐

**从此不再放配乐。** 正文最顶部放一行「往期精选，期待你的关注」文字（自带样式），
其下由审核者在公众号编辑器用「超链接 → 公众号文章」插 2-3 篇**同板块**的往期文章卡片
（工具介绍配工具介绍、顶刊精读配顶刊精读，以此类推）。文章卡片是微信内部链接，
**无法由 API/粘贴 HTML 生成**，故 HTML 里只放一行文字 + 一个占位框，卡片人工在编辑器插。

```html
<p style="margin:0 0 12px;text-align:center;font-size:13px;color:#999;letter-spacing:.5px;">「往期精选，期待你的关注」</p>
<figure style="margin:0 0 20px;">
  <div style="border:2px dashed #2563eb;border-radius:8px;padding:22px 16px;text-align:center;background:#eef3fd;color:#1a1a1a;font-size:14px;font-weight:600;line-height:1.6;">【往期精选 · 编辑器插入】用「超链接 → 公众号文章」插 2-3 篇<strong style="color:#1d4ed8;">同板块</strong>往期文章</div>
</figure>
```

> 占位框的边框/文字色随板块主题走（示例为 blue 工具介绍）；卡片本身在编辑器插，主题色不影响。

## 1. 板块标签 + 导语（开头两件套）

正文最顶部放一个**板块标签**（前沿科创 / 顶刊精读 / 人物专访），用描边胶囊（不填色，
跨主题都清晰）。紧接一段灰底导语。

```html
<!-- 板块标签：accent 描边胶囊 -->
<div style="margin:0 0 16px;">
  <span style="display:inline-block;border:1.5px solid #4ecdc4;color:#16a394;font-size:13px;font-weight:700;padding:4px 14px;border-radius:20px;letter-spacing:1px;">前沿科创</span>
</div>

<!-- 导语 -->
<p style="margin:0 0 24px;padding:14px 18px;background:#f8f9fa;border-radius:8px;font-size:15px;color:#666;line-height:1.7;">
  导语：用一句话点出这篇讲的核心发现，给读者一个往下读的理由。
</p>
```

## 1.5 编者按 / 观点（推荐：开头融入 BioSpark 自己的理解）

放在板块标签之后、正文之前，用两三句给出「我们怎么看」——不是复述新闻，而是一个有态度的
判断或框架：为什么值得看、真正的看点在哪、或别人没点破的角度。让号有声音，别打太极。
用 accent 左竖线 + accent_text 小标签，跟灰底导语区分开（可替代导语，也可并存）。

```html
<section style="margin:0 0 24px;padding:16px 18px;background:#f0fbfa;border-left:4px solid #4ecdc4;border-radius:0 8px 8px 0;">
  <div style="font-size:13px;font-weight:700;color:#16a394;letter-spacing:1px;margin-bottom:8px;">编者按 · BioSpark</div>
  <p style="margin:0;font-size:15px;color:#333;line-height:1.8;">两三句我们对这件事的判断/态度，最后可以带一句本文讲什么。有观点，落到具体。</p>
</section>
```

> 左竖线是单边框，按规约该侧不圆角 → `border-radius:0 8px 8px 0`。

## 2. 分节标题（序号 + 标题 + 下划线 + 小导语）⭐重做

旧版只有一条左竖线，分节不明显。新版：上方细分隔线把上一节切断，accent 序号当 kicker，
加粗大标题，下面一条 accent 短下划线，再跟**一句小导语**点出本节看点。序号、下划线只用
accent 当文字色/实色块（不在 accent 上压字），三套主题都清晰。

```html
<section style="margin:40px 0 18px;border-top:1px solid #f0f0f0;padding-top:22px;">
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:14px;font-weight:700;color:#16a394;letter-spacing:1.5px;">01</div>
  <h2 style="font-size:22px;font-weight:800;color:#1a1a1a;line-height:1.3;margin:4px 0 0;letter-spacing:.3px;">小标题文字</h2>
  <div style="width:40px;height:3px;background:#4ecdc4;border-radius:2px;margin:11px 0 0;"></div>
  <p style="margin:11px 0 0;font-size:14px;color:#999;line-height:1.65;">本节小导语：一句话说清这一节要回答什么问题，给读者往下读的钩子。</p>
</section>
```

> 序号用 `01 / 02 / 03…` 顺延。**每个分节标题都要带小导语**（这是新硬性要求）。
> 标题尽量短而有信息量；小导语 ≤ 30 字，口语化、带悬念。

## 3. 正文段落

```html
<p style="margin:0 0 16px;letter-spacing:.3px;text-indent:2em;">
  正文。用 `text-indent:2em` 做整段首行缩进。用原文的具体事实、数字、人名、引语说话。
</p>
```

> **首行缩进用 CSS `text-indent:2em`（写在 `<p>` 样式里），不要用段首全角空格**。
> 原因：这是段落级样式，作者在公众号编辑器里回车另起一段，新段会自动带缩进（全角空格做不到，且显得怪）。
> **注意**：`text-indent` 对"以 `<mark>` 高亮开头"的段落，微信里会渲染得偏一点 → **别让正文段以 `<mark>` 开头**，
> 前面垫一个引导词（如"说白了，""换句话说，"）即可。以 `<strong>` 开头没问题。
> 只加在叙述性正文段；编者按、导语、小导语、图注、要点列表、数据卡、表格、互动卡、页脚**都不加**。
```

### 强调两档（⭐读者反馈：标重点的形式太多，已砍掉荧光高亮）

**① 普通加粗**（中性深色，给人名/术语/机构）：
```html
<strong style="color:#1a1a1a;font-weight:600;">需要强调的关键词</strong>
```

**② 彩色加粗**（主色，给关键数字、核心结论、对比落点 —— 全篇重点统一用它）：
```html
<strong style="color:#16a394;font-weight:700;">35 分钟</strong>
```

> **不再用荧光高亮 `<mark>`。** 一段里标重点的形式只有"普通加粗/彩色加粗"两种，别再叠第三种。
> **想让某句更突出，不靠更多标注，而是换行分段**——把那句单独拎成一段（或用要点列表/引语卡/数据卡打断），比再加一种高亮更清爽。
> 配色用 aqua 基准（`#16a394` 彩色字），主题切换时随主色一起变。
> 节制：通篇②+③加起来别超过 8-10 处，否则等于没重点。数字优先用②，金句用③。

## 4. 引语卡（人物发言 / 原文 quote）

> 用 `<section>` 而非 `<blockquote>`（微信对 blockquote 默认样式有干扰）。
> 大引号 + 虚线分隔 + 青绿署名，比纯左竖线更精致。不要用 emoji 引号。

```html
<section style="margin:26px 0;padding:20px 22px 16px;background:#f4fbfa;border:1px solid #e0f3f1;border-radius:12px;">
  <div style="font-size:46px;line-height:.6;color:#4ecdc4;font-family:Georgia,'Times New Roman',serif;font-weight:700;height:24px;">“</div>
  <p style="margin:0;font-size:16px;color:#1a1a1a;line-height:1.85;">引语正文（中文重新表达，但保留原文含义）。</p>
  <div style="margin-top:14px;padding-top:12px;border-top:1px dashed #cfeae6;text-align:right;line-height:1.5;">
    <span style="font-size:15px;color:#16a394;font-weight:700;">说话人</span>
    <span style="font-size:13px;color:#999;">　身份 / 出处</span>
  </div>
</section>
```

## 5. 配图 figure（关键：半自动手动上传）

复制粘贴**不会**把图片带进公众号（`file://` 跨域），所以这里只放一个**醒目占位**，
告诉审核者「此处手动上传哪张图」。审核者在公众号编辑器里把光标放到这个位置，上传 `images/figures/fig-N.jpg`。

```html
<figure style="margin:24px 0;">
  <div style="border:2px dashed #4ecdc4;border-radius:8px;padding:28px 16px;text-align:center;background:#f0fbfa;color:#1a1a1a;font-size:15px;font-weight:600;">
    【图1：fig-1.jpg — 在此处手动上传】
  </div>
  <figcaption style="font-size:13px;color:#888;text-align:center;margin-top:8px;line-height:1.6;">
    图1说明文字（来源：xxx.com）
  </figcaption>
</figure>
```

> 如果你想在浏览器预览时**看到真图**（方便审核），可以临时把上面的 `<div>` 换成
> `<img src="images/figures/fig-1.jpg" style="width:100%;border-radius:8px;display:block;">`，
> 但记得正式粘贴时图片仍要在公众号后台手动上传——所以**保留占位 div 版本作为粘贴源**最稳妥。
> 推荐做法：`gongzhonghao.html` 用占位 div 版（粘贴源），另存一份 `gongzhonghao_preview.html` 用真图版（仅本地预览）。

## 6. 数据卡（关键数字高亮）

> ⚠️ **不要用 `display:flex` 做多栏**——微信编辑器会剥掉 flex 和 `linear-gradient`，
> 盒子背景和大字号全丢，文字挤成乱折行（实测教训）。**多栏一律用 `<table>`**，实色背景。
> 列宽用 `table-layout:fixed`，列间距用 `border-spacing`，标签尽量短（4 字内）避免折行。

```html
<table style="width:100%;border-collapse:separate;border-spacing:8px 0;margin:24px 0;table-layout:fixed;">
  <tbody><tr>
    <td style="width:33.3%;background:#f0fbfa;border:1px solid #e0f3f1;border-radius:12px;padding:18px 6px;text-align:center;vertical-align:top;">
      <div style="font-size:27px;font-weight:800;color:#4ecdc4;line-height:1.15;">98.5<span style="font-size:14px;font-weight:700;">%</span></div>
      <div style="font-size:12px;color:#666;margin-top:6px;line-height:1.4;">指标名</div>
    </td>
    <td style="width:33.3%;background:#f0fbfa;border:1px solid #e0f3f1;border-radius:12px;padding:18px 6px;text-align:center;vertical-align:top;">
      <div style="font-size:27px;font-weight:800;color:#4ecdc4;line-height:1.15;">3.2<span style="font-size:14px;font-weight:700;">倍</span></div>
      <div style="font-size:12px;color:#666;margin-top:6px;line-height:1.4;">指标名</div>
    </td>
    <td style="width:33.3%;background:#f0fbfa;border:1px solid #e0f3f1;border-radius:12px;padding:18px 6px;text-align:center;vertical-align:top;">
      <div style="font-size:27px;font-weight:800;color:#4ecdc4;line-height:1.15;">35<span style="font-size:14px;font-weight:700;">分钟</span></div>
      <div style="font-size:12px;color:#666;margin-top:6px;line-height:1.4;">指标名</div>
    </td>
  </tr></tbody>
</table>
```

## 7. 对比表

```html
<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;">
  <thead>
    <tr>
      <th style="background:#1a1a1a;color:#fff;padding:10px 12px;text-align:left;border-radius:8px 0 0 0;">项目</th>
      <th style="background:#1a1a1a;color:#fff;padding:10px 12px;text-align:center;">旧方法</th>
      <th style="background:#4ecdc4;color:#1a1a1a;padding:10px 12px;text-align:center;border-radius:0 8px 0 0;">新方法</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:10px 12px;border-bottom:1px solid #eee;color:#666;">准确率</td>
      <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:center;">81%</td>
      <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:center;font-weight:600;color:#16a394;">98%</td>
    </tr>
  </tbody>
</table>
```

## 7.5 要点列表（把并列内容拆成短条，别堆成长段）

并列的事实/步骤/特点，**别写成一长段**，拆成带色点的短条，可读性翻倍：

```html
<section style="margin:20px 0;">
  <p style="margin:0 0 10px;padding-left:14px;border-left:3px solid #4ecdc4;line-height:1.7;">
    <strong style="color:#1a1a1a;font-weight:600;">150 个专业工具</strong>：从 bioRxiv 2500 篇论文里提取、人工核验。
  </p>
  <p style="margin:0 0 10px;padding-left:14px;border-left:3px solid #4ecdc4;line-height:1.7;">
    <strong style="color:#1a1a1a;font-weight:600;">105 个软件包</strong>：覆盖主流生信分析。
  </p>
  <p style="margin:0;padding-left:14px;border-left:3px solid #4ecdc4;line-height:1.7;">
    <strong style="color:#1a1a1a;font-weight:600;">59 个数据库</strong>：一处接入，免去多门户切换。
  </p>
</section>
```

## 8. 来源页脚（必带，溯源）

```html
<section style="margin-top:36px;padding-top:18px;border-top:1px solid #eee;font-size:13px;color:#888;line-height:1.8;">
  <div style="margin-bottom:4px;">参考来源：</div>
  <div>· 主源：<span style="color:#16a394;">Nature, 2026-06-18, 文章标题</span></div>
  <div>· 配图来源见 sources.json</div>
  <div style="margin-top:10px;color:#aaa;">本文由 BioSpark 产线整理，仅作学术科普。</div>
</section>
```

## 8.5 版权签名 / 水印（每篇必带，**程序化默认注入**）⭐新增

**放在「互动话题卡」之后、「来源页脚」之后，或文末最末**。作用：

- 即便截图 / 复制 / 洗稿，**你的品牌署名和仓库链接会跟着走**；
- 提供"原创溯源 + 联系方式 + 举报路径"的三件套；
- 微信粘贴会保留（全是内联样式 + 文字，没有外部依赖）；
- 满足《人工智能生成合成内容标识办法》对 AI 生成内容的显著标识要求。

**文末三件套渲染顺序**：`互动话题卡 → 来源页脚 → 【AI 辅助生成】标识 → 版权签名 / 举报`。  
AI 标识放在版权签名**之前**——AI 提示作为内容级免责，版权签名作为法律级归属，读者先看到合规提示再看品牌归属。

```html
<!-- AI 生成内容显著标识（依《人工智能生成合成内容标识办法》2025-09-01 生效） -->
<!-- 位置：来源页脚之后、版权签名之前 -->
<!-- 颜色：浅暖底 + 深棕字（区别于灰底版权签名，让读者一眼看到 AI 提示） -->
<div style="margin:24px 0 0;padding:12px 16px;background:#fff8e6;border:1px solid #f5e0a0;border-left:4px solid #ec7a26;border-radius:0 8px 8px 0;font-size:13px;color:#7a5a1a;line-height:1.75;">
  <div style="font-weight:700;letter-spacing:.5px;margin-bottom:4px;">【AI 辅助生成】</div>
  <div>本文由 BioSpark 自动化产线辅助生成（选题 / 写作 / 配图 / 排版均含 AI 参与），所有事实性内容已由编辑人工审核。本文为科学传播，<strong style="color:#1a1a1a;">不构成医疗、投资或专业建议</strong>。引用请标注「AI For Bios · BioSpark」。</div>
</div>

<!-- BioSpark 版权签名 / 公众号溯源水印 — 每篇必带 -->
<section style="margin:16px 0 0;padding:18px 20px;background:#f8f9fa;border:1px solid #eee;border-radius:10px;font-size:13px;color:#666;line-height:1.85;">
  <div style="font-weight:700;color:#1a1a1a;font-size:14px;letter-spacing:.5px;margin-bottom:8px;">
    公众号 <span style="color:#16a394;">「AI For Bios · BioSpark」</span> 原创出品
  </div>
  <div style="margin-bottom:4px;">本文由 BioSpark 自动化产线辅助生成 + 人工审核后发布</div>
  <div style="margin-bottom:4px;">源码 / 排版契约 / 卡片系统：
    <span style="color:#16a394;word-break:break-all;">github.com/yetong0516/BioSpark_AI-For-Bios_WeChat-OA-Automation-Pipeline</span>
  </div>
  <div style="color:#999;font-size:12px;margin-top:8px;padding-top:8px;border-top:1px dashed #e5e5e5;">
    转载 / 洗稿 / 未授权使用本产线产出内容均构成侵权。
    举报邮箱：<span style="color:#16a394;">yetong0516@gmail.com</span>
  </div>
</section>
```

**渲染规则**（写进 `SKILL.md` 阶段 5-GZH 的固定注入步骤）：

- 位置：**`互动话题卡 → 来源页脚 → AI 辅助生成标识 → 版权签名`**，四段连成文末固定四件套
- AI 标识样式：浅暖底 + 橙左竖线（用板块主色 `orange` 强调，区别于灰底版权签名）
- 版权签名样式：浅灰底 + accent 标题，跟前文互动话题卡视觉上区分（不抢主色）
- 不可关闭、不可关闭、不可关闭（**默认开启；如要隐藏必须 `gzh_publish.py --no-watermark` 显式声明**）
- 复用：截图洗稿者就算抠图也会被这段背景+水印拖住，**视觉识别成本大增**

---

## 9. 互动话题卡（每篇结尾必带，引导评论）

文章结尾针对本文内容抛一个**可讨论的问题**，用一张醒目卡片包起来，邀请读者留言。
问题要具体、有张力、能站队或能各抒己见，别问空泛的"你怎么看"。

```html
<section style="margin:32px 0 8px;padding:18px 20px;background:#f0fbfa;border:1px solid #e0f3f1;border-radius:12px;">
  <div style="font-size:13px;font-weight:700;color:#16a394;letter-spacing:1px;margin-bottom:8px;">／ 留言区见 ／</div>
  <p style="margin:0;font-size:16px;color:#1a1a1a;line-height:1.75;font-weight:600;">针对本文的讨论问题（一句，具体、有张力、能让人想接话）。</p>
  <p style="margin:8px 0 0;font-size:14px;color:#888;line-height:1.65;">你站哪一边？评论区聊聊。</p>
</section>
```

## 排版规约（写 gongzhonghao.html 时遵守）

- **不用 emoji**（本机无 emoji 字体，且公众号端显示不稳定）。
- 字号：H2 = 20px、正文 = 16px、图注/页脚 = 13px。手机端正文 16px 最舒适。
- 段落之间用 `margin-bottom`，**不要**用空 `<p>` 撑行（公众号会清掉）。
- **段落要短**：每段最多 2-3 句、约 3-5 行手机屏。出现"一段四五句以上"就拆开，或改用「要点列表」「数据卡」打断。手机端长段是可读性头号杀手。
- **每 2-3 段就有一个视觉落点**：彩色加粗 / 配图 / 数据卡 / 引语卡 / 要点列表 / 换行分段，轮着来，别让读者连看四五段纯文字。（**不再用荧光高亮**）
- **重点标注只用「彩色加粗」一种**（读者反馈：形式太多太乱）。要更突出就**换行分段**，不叠更多高亮。
- **微信会剥掉 `display:flex` / `display:grid` / `linear-gradient` / `position:absolute`**：多栏布局一律用 `<table>`，背景用实色，不要靠 flex 或绝对定位排版（否则手机端塌成乱码）。
- 颜色：中性色 `#1a1a1a / #333 / #666 / #888 / #f8f9fa`；强调色用 aqua 基准——**行内文字**重点用深色 `#16a394`（白底可读），**色块/大数字/边框/下划线**用亮色 `#4ecdc4`。主题切换时随主色一起变。
- **自制图/卡片字体要统一**：一张图里字体形式（字号档位 + 粗细 + 字族）尽量收敛，**别在一张卡里堆三种以上**。标题一档、正文一档、辅助说明一档，够了。中英文用同一 font-family 优先级，别中文用系统字、英文又换成 serif。
- **配图必须高清**：优先**下原图高分辨率**再按需裁剪（保留原始画质）；论文图从预印本/期刊取大图，自制图渲染时 `--scale 2` 或视口调大（≥1000px 宽）。低清糊图要么重下原图，**要么 AI 放大修复**后再用，别直接塞进正文。
- **字体不可内嵌**：公众号正文用的是读者手机系统字体（iOS=苹方 PingFang SC，安卓=各自默认），微信会剥掉 @font-face，无法强制统一字体。只能排好 font-family 优先级（已 PingFang SC 优先）。要精确控制字体只能在**封面图**上做（封面是我们渲染的 PNG）。
- 文风规范与小红书一致：开头直接进事件、禁用「赋能/闭环/底层逻辑/总而言之」等 AI 味词、结尾留一个具体问题。
- 字数 1500–2500 字（与 `article.md` 同源，可直接由 article.md 转写为带样式的段落）。
