# MarketLens AI Prompt 模板

## 1. 来源证据抽取 Prompt

```text
你是一个竞品情报研究助理，请从给定公开来源中抽取可以追溯的证据行。

请返回以下字段：
- brand_id
- lens
- claim
- source_title
- source_url
- source_type
- source_date
- excerpt，控制在 260 字以内
- confidence，范围 0 到 1
- review_status
- notes

只保留能被原文直接支持的结论。如果来源较弱、信息不完整或来自付费墙摘要，请把 review_status 设为 needs_review。
```

## 2. 证据复核 Prompt

```text
请复核以下 evidence rows 是否适合进入研究简报。

检查：
1. claim 是否能从 excerpt 直接推出？
2. source_type 是否标注正确？
3. confidence 是否过高或过低？
4. review_status 应该是 reviewed、needs_review 还是 rejected？
5. excerpt 是否足够短，能放进证据表？

请返回表格：evidence_id、decision、suggested_confidence、reason。
```

## 3. 研究简报综合 Prompt

```text
你正在为品牌运营/商业分析实习作品写一份竞品情报简报。

只能使用给定 evidence rows，不要加入无法溯源的信息。

请输出：
1. 市场概览
2. 价格压力
3. 扩张模式
4. 加盟运营风险
5. 品牌定位
6. 风险信号

每个章节都要列出 supporting evidence IDs 和 confidence。
```

## 4. 面试解释 Prompt

```text
请帮我用 2 分钟解释 MarketLens AI 这个项目。

重点强调：
- 业务问题
- AI 辅助工作流
- 数据 schema
- 置信度评分
- Dashboard 可视化
- 来源纪律
- 局限和下一步迭代

表达要诚实，不要暗示这是生产级系统、正式实习成果或公司内部项目。
```

## 5. 迁移到新行业 Prompt

```text
请把 MarketLens AI 工作流迁移到一个新行业。

输入：
- 目标行业
- 竞品列表
- 分析维度
- 偏好的公开来源类型

请返回：
1. 调整后的品牌/来源 schema
2. 资料收集 queries
3. 证据抽取规则
4. Dashboard 指标
5. 需要人工复核的风险点
```
