# Section 24 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 24.1 | both | scope_transition | This paragraph establishes the scope of the section by specifying what transactions it applies to, which is a scope-defining statement. |
| 24.2 | both | other | This paragraph provides a definition and clarification of what constitutes a government grant by specifying exclusions, without imposing a substantive accounting requirement. |
| 24.3 | pre-PR2024 | scope_transition | This paragraph defines the boundaries of the government assistance section by explicitly excluding certain types of government assistance and cross-referencing another section that covers those matters. |
| 24.3 | PR2024 | scope_transition | This paragraph defines the scope boundary of the government assistance section by explicitly stating what is excluded and cross-referencing to the section that covers the excluded items. |
| 24.3A | pre-PR2024 | recognition_measurement | This paragraph specifies the condition ('reasonable assurance') that must be satisfied before government grants are recognised in the financial statements. |
| 24.3A | PR2024 | recognition_measurement | This paragraph specifies the condition that must be satisfied before government grants are recognised in the financial statements, which is a recognition criterion. |
| 24.4 | both | recognition_measurement | This paragraph establishes the timing and method for recognising government grants (performance model vs. accrual model) and thus governs recognition of these items. |
| 24.5 | both | recognition_measurement | This paragraph specifies how grants should be measured (at fair value of the asset received or receivable), which is a measurement requirement. |
| 24.5A | both | recognition_measurement | This paragraph establishes when a grant repayment should be recognised in the financial statements by reference to the definition of a liability. |
| 24.5B | both | recognition_measurement | This paragraph specifies the accounting treatment and recognition of grants under the performance model, which is a fundamental recognition requirement. |
| 24.5C | pre-PR2024 | recognition_measurement | This paragraph specifies how grants must be classified under the accrual model, which is a measurement approach that determines the accounting treatment of different types of grants. |
| 24.5C | PR2024 | recognition_measurement | This paragraph establishes how grants must be classified (as revenue-related or asset-related), which determines their subsequent recognition and measurement treatment. |
| 24.5D | both | recognition_measurement | This paragraph specifies the timing and method for recognising revenue grants in the financial statements, establishing when such grants should be recognised and how they should be matched to related costs. |
| 24.5E | both | recognition_measurement | This paragraph specifies the timing and condition for recognising government grants as income, which is a recognition requirement. |
| 24.5F | pre-PR2024 | recognition_measurement | This paragraph specifies the timing and method for recognizing grant income, determining when and how the gain is measured rather than disclosing or presenting information. |
| 24.5F | PR2024 | recognition_measurement | This paragraph specifies the required method and timing for recognizing the effect of asset grants in income, which is a measurement and recognition requirement rather than a disclosure, presentation, or scope matter. |
| 24.5G | both | recognition_measurement | This paragraph specifies how to treat deferred portions of grants—requiring them to be recognised as deferred income rather than deducted from asset carrying amounts, which is a measurement and classification requirement. |
| 24.6 | both | disclosure | The paragraph explicitly requires an entity to disclose specific information, which is the defining characteristic of a disclosure requirement. |
| 24.7 | pre-PR2024 | other | This paragraph provides a definition and examples of 'government assistance' to support understanding of the disclosure requirement in 24.6(d), but imposes no independent requirement itself. |
| 24.7 | PR2024 | other | This paragraph contains no substantive content as it has been deleted, so it imposes no disclosure, presentation, recognition, measurement, or scope requirement. |

## Draft checklist rows (1)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 24.6 | both | Disclose all information required by paragraph 24.6 in respect of government grants | conditional | has_government_grants == true | has_government_grants (NEW) | missing | standard-material | Paragraph 24.6 lists the specific sub-items to be disclosed but the text provided is incomplete (cut off after the opening sentence); the reviewer should verify all sub-items are present against the full paragraph text and assess materiality. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| has_government_grants | 24.6 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 1 | 2356 | 127 | $0.0090 |
| **total** | 1 | 2356 | 127 | **$0.0090** |
