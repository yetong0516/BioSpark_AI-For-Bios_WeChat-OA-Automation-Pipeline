# 每日定时任务（一天一篇）配置说明

产线本身不内置定时器；定时由 Claude Code 的 scheduled-tasks 机制驱动。
**定时跑只产草稿 + 通知，永不发布。** 发布永远是你审核后的人工动作。

## 任务参数（已定稿 2026-07-02）

- `taskId`: `biospark-daily-draft`
- `cronExpression`: `0 8 * * *`（每天早 8:00 本地时间）
- `notifyOnCompletion`: `true`
- 工作目录：`<PIPELINE_DIR>`（即本产线所在目录的绝对路径）
- **板块策略：不固定轮换，每天按当天热点自选板块**（前沿科创/顶刊精读/工具介绍/人物专访）。

## 自包含任务提示词（定时运行无本会话记忆，必须自包含）

```
你在 BioSpark 生物资讯日更产线，工作目录：
<PIPELINE_DIR>
先读 SKILL.md、templates/gzh_themes.md、templates/gzh_style.md，再按下面为今天产【一篇】草稿。

1. 确定今天日期 <today>。读 state/topic_history.jsonl，收集所有历史 slug / topic_key / main_url。
2. WebSearch 搜近 7 天生物/生命科学热点（Nature/Science/Cell/bioRxiv/NIH/NEJM/Broad/EMBL 等），
   选一个【未在历史里出现过】的主题。若首选与历史重复，换下一个。
3. 【板块自选】给这个主题判定它属于哪个板块，主题色随之：
   - 报道"发生了什么新突破/新进展/新工具问世" → 前沿科创 → aqua
   - 精读一篇具体顶刊论文（走 gzh_themes.md 末尾的 6 段学术架构：
     课题组脉络→背景→方法(深写)→创新点→结果与讨论→专利与产业转化）→ 顶刊精读 → orange
   - 手把手教某个软件/数据库/在线工具怎么上手用 → 工具介绍 → blue
   - 以某个人/团队为主角的访谈故事 → 人物专访 → indigo
   自选时优先"前沿科创 / 顶刊精读 / 工具介绍"这三块（自动选题友好）；
   人物专访仅当确有一位明确人物+足够素材时才选，否则换别的板块。
4. 按 SKILL.md 跑阶段 2–4 + 5-GZH（含套主题 scripts/gzh_theme.py --theme <色>）+ 5-XHS，
   全部写进 drafts/<today>_<slug>/。title.txt 用「板块｜标题」格式。
5. 向 state/topic_history.jsonl 追加一行（append，不重写）：
   {"date":"<today>","slug":"<slug>","section":"<板块>","title":"<标题>","main_url":"<主源>","status":"drafted"}
6. 停在阶段 6 审核闸：生成 REVIEW.md。
   绝对不要发布、不要移动到 published/、不要调用任何微信 API / gzh_publish.py --draft-push。
7. 通知我：今天选题 + 属于哪个板块 + 一句话为什么选它 + 草稿目录路径 + 审核清单要点。
   我会在方便时回复 approve / edit / skip。
```

## 怎么开启

方式一（推荐先演练）：先用一个「近未来一次性」触发（如 5 分钟后）跑一遍，确认能产草稿 + 通知、且确实停在审核闸，再改成每天 cron。

方式二：直接让我用 scheduled-tasks 建上面的每日任务。

> 开启前请确认：① 这台 Mac 在早 8 点处于开机/唤醒状态（睡眠中定时不触发）；
> ② Python 依赖已装（playwright/chromium、beautifulsoup4、lxml、Pillow）；
> ③ 你接受「每天自动生成草稿、等你审核」这个节奏。
```
