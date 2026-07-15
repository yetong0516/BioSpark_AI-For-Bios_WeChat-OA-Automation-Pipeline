# state/ — 产线状态文件

- **topic_history.jsonl** — 选题去重台账（append-only，每行一条 JSON）。
  选题前读它、跳过已出现的 `topic_key` / `main_url`；选完追加 `status: drafted`，
  审核 `approve` 后追加 `status: published`，`skip` 后追加 `status: skipped`。
  字段：`date / topic_key / topic / main_url / source_site / status / slug`。

  示例行：
  ```json
  {"date":"2026-06-19","topic_key":"alphafold3-rna-binding","topic":"AlphaFold3 预测 RNA 结合位点","main_url":"https://www.nature.com/articles/xxx","source_site":"nature.com","status":"drafted","slug":"alphafold3-rna-binding"}
  ```

- **review_log.md** — 人工审核审计日志（approve/edit/skip 各记一行）。

> 这两个文件是产线的「记忆」。定时任务每天读 topic_history 避免重复选题。
