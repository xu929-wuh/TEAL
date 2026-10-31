# QEA 证据支持双人独立审计

## 口径

- 数据源：`dataset_release_v14/clean/positives/test_frozen.jsonl`，共 470 条可答 QEA。
- 抽样：固定种子 `20261025`，按作品分层，每部 15 条；共 120 条，四语各 30 条。
- 检查对象：每条 QEA 自带的 `evidence_text` 与 `gold_answer`；该审计不涉及作答系统输出。
- 审阅方式：由两名真人标注者分别独立对照原文证据。三类标签（SUPPORTED/PARTIAL/UNSUPPORTED）一致 **118/120（98.33%）**，Cohen's κ **0.8673**；二元严格支持判定一致 **118/120（98.33%）**，κ **0.8662**；核心支持判定一致 **120/120**，κ **1.0000**。分歧按较严格标签汇总。

## 结果

| 语言 | 严格支持（所有答案细节） | 核心答案支持（回答所需最小信息） | 例外 |
|---|---:|---:|---|
| en | 28/30（93.33%） | 29/30（96.67%） | 1 部分 + 1 不支持 |
| fr | 30/30（100.00%） | 30/30（100.00%） | - |
| ru | 26/30（86.67%） | 30/30（100.00%） | 4 条部分支持 |
| zh | 27/30（90.00%） | 30/30（100.00%） | 3 条部分支持 |
| **合计** | **111/120（92.50%）** | **119/120（99.17%）** | 8 部分 + 1 不支持 |

- 严格支持 Wilson 95% CI：**[0.8636, 0.9600]**。
- 核心答案支持 Wilson 95% CI：**[0.9543, 0.9985]**。
- 两名标注者对严格支持的二元判定一致 **118/120（98.33%）**，Cohen's κ **0.8662**；出现分歧时采用更严格标签。
- “严格支持”要求参考答案的每个事实细节都能在所给证据中找到。
- “核心支持”只要求证据包含回答该问题所需的最小信息；部分支持条目可能多出证据中未出现、但可能来自原文其他段落的细节。

## 例外明细

1. `QEA-018`（en，*Wuthering Heights*，不支持）：证据中的嘲讽由叙述者 Nelly（“I observed aloud”）发出，并是对 Isabella 说的；参考答案却把该行为归到 Mrs. Heathcliff 身上。这是实体归属错误。
2. `QEA-030`（en，*Wuthering Heights*，部分支持）：Nelly 的暗示和 Lockwood 的回答有证据；但“Nelly 问他为什么提到她时显得那么有生气”不在所给证据中，第二审阅者复核后降为部分支持。
3. `QEA-069`（ru，*The Brothers Karamazov*，部分支持）：100/120 卢布的食品采购有证据；“含香槟共约 300 卢布”不在所给证据中。
4. `QEA-078`（ru，*War and Peace*，部分支持）：在 Bogucharovo 建房有证据；但“安德烈大部分时间住在这里”不在所给证据中，第二审阅者复核后降为部分支持。
5. `QEA-083`（ru，*War and Peace*，部分支持）：求婚与拒绝有证据；“午饭后立即离开”不在所给证据中。
6. `QEA-085`（ru，*War and Peace*，部分支持）：两家不和及和解有证据；“Ilagin 提出让出猎场”不在所给证据中。
7. `QEA-098`（zh，《红楼梦》，部分支持）：果品清单和周瑞回话有证据；“贾珍命照账点清并留底”不在所给证据中。
8. `QEA-102`（zh，《红楼梦》，部分支持）：买通知县、证人改口有证据；“仵作验系磕碰伤”不在所给证据中。
9. `QEA-114`（zh，《西游记》，部分支持）：妖怪畏惧、把唐僧绑在后园有证据；“分瓣梅花计调开三兄弟”这一名称与调虎离山细节不在所给证据中。

## 可用于审稿回复的边界

可以回答 Reviewer #5 Q4 与 Reviewer #11 Q1：在 120 条分层抽检中，主指标核心答案支持为 **99.17%**，严格全句支持为 **92.50%**（仅作保守敏感性分析）；剩余问题主要是参考答案夹带证据摘录之外的细节，以及 1 条实体归属错误。

本报告可作为 120 条样本的双人独立人工证据支持审计引用，并报告上述一致率和 κ。样本量有限，结果不代表全数据集的人工标注质量；更大规模评估仍属后续工作。

## 文件

- 抽样清单：`data/qea_reference_audit_120.sample.jsonl`
- 第一审阅者判断：`data/qea_reference_audit_120.annotator_a.csv`；例外：`data/qea_reference_audit_120.adjudications.csv`
- 第二审阅者判断：`data/qea_reference_audit_120.annotator_b.csv`；例外：`data/qea_reference_audit_120.adjudications_second_pass.csv`
- 合并后最终判断：`data/qea_reference_audit_120.final_labels.csv`；两名审阅者比较：`reports/qea_reference_audit_120.REVIEW_COMPARISON.md`、`metadata/qea_reference_audit_120.review_comparison.json`
- 相关脚本：`scripts/build_qea_support_audit_sample.py`、`scripts/summarize_qea_support_audit.py`、`scripts/compare_qea_support_reviews.py`
