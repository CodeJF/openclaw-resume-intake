# 写入失败后的回复规则

## 目标
避免 agent 在写入失败后沉默，让飞书用户能立即知道当前卡在哪一步。

## 规则
当多维表格写入失败时：
1. 必须立即回复飞书用户
2. 明确说明失败发生在哪一步
3. 直接给出错误名称或错误摘要
4. 说明下一步会如何处理，或提示需要用户确认什么

## 当前场景下的最小要求
如果 `feishu_bitable_app_table_record.create` 或 `update` 返回错误，例如：
- `NumberFieldConvFail`
- `FieldNameNotFound`
- `AppScopeMissingError`
- 其他写入错误

则不要沉默，不要卡住，不要无限重试。

应立即回复类似：
- 已收到简历，但写入多维表格失败，错误是 `NumberFieldConvFail`。
- 我会按更保守的字段策略重试，或请你确认目标字段类型。

## 重点
失败后先回复用户，再决定是否继续下一步。
