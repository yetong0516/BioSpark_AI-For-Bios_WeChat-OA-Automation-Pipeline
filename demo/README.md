# Demo · 自动排版演示 / Formatting Showcase

这里放一篇产线**真实产出**的公众号长图文,用来直观展示 BioSpark 的自动排版效果。

This folder holds one **real article** produced by the pipeline, to show what BioSpark's automated WeChat formatting looks like.

## 文件 / Files

| 文件 | 说明 |
| --- | --- |
| [`wechat-article-demo.html`](wechat-article-demo.html) | 公众号长图文源码(内联样式,可直接在浏览器打开)。用浏览器打开即可查看完整排版。 |
| [`wechat-article-demo.png`](wechat-article-demo.png) | 整页渲染截图,GitHub 上直接可看(下方预览)。 |

## 预览 / Preview

![WeChat article formatting demo](wechat-article-demo.png)

## 这篇展示了什么 / What it demonstrates

样例主题:**SpudCell —— 从零造出可生长、可复制、可分裂的化学定义合成细胞**(板块:顶刊精读,主题色 orange `#ec7a26`)。

- **板块主题色系统** —— 标签、分节号、强调色、卡片描边统一走板块色。
- **6 段学术架构** —— 团队 → 背景 → 方法 → 创新点 → 结果讨论 → 专利产业转化(01–06 分节)。
- **内联样式契约** —— 全部样式内联,粘贴进微信公众号编辑器后不掉格式(见 [`../templates/gzh_style.md`](../templates/gzh_style.md))。
- **排版组件** —— 编者按卡、往期精选占位、数据卡(90kbp / 9段 / 36种)、引言卡、留言互动卡、溯源页脚。

The sample topic is a chemically-defined synthetic cell ("SpudCell"). It shows the section-theme color system, the 6-part academic structure (01–06), the inline-style contract that survives pasting into WeChat's editor, and reusable layout components (editor's note, stat tiles, pull quotes, comment prompt, sourced footer).

## ⚠️ 关于配图 / About the figures

正文文字与版式是 BioSpark 产线的产出。原文中的 **3 张配图已替换为占位框**——其中两张是第三方论文原图 / 研究者照片,不随本仓库分发;占位框保留了原始图注与来源,以便你看清配图在版式中的位置。真实运行时,产线会按 `sources.json` 里的授权信息填入实际配图。

The article text and layout are the pipeline's output. The **3 figures are replaced with placeholders** — two were third-party paper figures / a researcher's portrait and are not redistributed here. Captions retain the original sources so you can see where images sit in the layout. In a real run the pipeline fills in the actual sourced figures.
