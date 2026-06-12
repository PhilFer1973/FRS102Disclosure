# Section 10 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 10.1 | both | scope_transition | This paragraph introduces the scope of the section by outlining what requirements follow, establishing the boundaries of applicability for inventories accounting. |
| 10.2 | both | other | This paragraph provides a definition of accounting policies without imposing any requirement for recognition, measurement, disclosure, or presentation. |
| 10.3 | both | other | This paragraph provides a general principle governing the application of FRS 102 requirements based on materiality, but does not itself impose a specific recognition, measurement, presentation, or disclosure requirement. |
| 10.4 | both | other | This paragraph provides guidance on the process for developing accounting policies when FRS standards do not specifically address a matter, establishing a principle rather than imposing a specific disclosure, presentation, or recognition requirement. |
| 10.5 | both | other | This paragraph provides guidance on the methodology for making judgements about accounting treatment by establishing a hierarchical referencing framework, but it does not itself impose a specific recognition, measurement, disclosure or presentation requirement. |
| 10.6 | both | other | This paragraph provides guidance on how management may consider IFRS requirements when exercising judgment, and cross-references to other sections without imposing its own substantive requirement. |
| 10.7 | both | recognition_measurement | This paragraph establishes the requirement for consistent application of accounting policies across similar items and conditions, which governs how entities measure and recognise transactions. |
| 10.8 | both | recognition_measurement | This paragraph establishes the conditions under which an entity is permitted to change an accounting policy, which governs the recognition and application of accounting treatments. |
| 10.9 | both | other | This paragraph provides a definition or clarification of what does not constitute a change in accounting policies, without imposing any substantive recognition, measurement, presentation or disclosure requirements. |
| 10.10 | both | other | This paragraph provides a definition of what constitutes a change in accounting policy under FRS 102, establishing a conceptual boundary without imposing a specific disclosure, presentation, or recognition requirement. |
| 10.10A | both | scope_transition | This paragraph clarifies the transitional treatment and scope application of initial revaluation policies under FRS 102, specifying that such changes follow revaluation rules rather than general accounting policy change procedures. |
| 10.10B | PR2024 | scope_transition | This paragraph establishes transitional provisions for how changes in accounting policy for biological assets are to be handled when moving from cost to fair value model under Section 34. |
| 10.11 | both | recognition_measurement | This paragraph establishes the accounting treatment and methodology for how changes in accounting policy should be handled, which is a recognition and measurement requirement rather than a disclosure or presentation requirement. |
| 10.12 | both | recognition_measurement | This paragraph governs how the carrying amounts of assets, liabilities, and equity components are determined when a change in accounting policy is applied retrospectively, which is a measurement requirement. |
| 10.14A | PR2024 | other | This paragraph provides definition and explanatory guidance on accounting estimates and measurement uncertainty without imposing a specific disclosure, presentation, or recognition requirement. |
| 10.14B | PR2024 | other | This paragraph provides definitions of measurement techniques without imposing a specific requirement for recognition, measurement, disclosure, or presentation. |
| 10.14C | PR2024 | other | This paragraph provides a definitional clarification explaining how the term 'estimate' is used in FRS 102, without imposing any requirement for recognition, measurement, presentation or disclosure. |
| 10.14D | PR2024 | other | This paragraph provides explanatory guidance on the circumstances that may prompt changes to accounting estimates, without imposing a specific requirement on recognition, measurement, presentation or disclosure. |
| 10.15 | pre-PR2024 | other | This paragraph provides definitional guidance on what constitutes a change in accounting estimate and distinguishes it from other types of changes, without imposing specific disclosure, presentation, or recognition requirements. |
| 10.15 | PR2024 | recognition_measurement | This paragraph establishes the criteria for distinguishing between changes in accounting estimates versus changes in accounting policies, which fundamentally governs how items are measured and recognized. |
| 10.16 | both | recognition_measurement | This paragraph specifies when and how the effect of a change in accounting estimate shall be recognized (prospectively in profit or loss), which is a recognition and measurement requirement. |
| 10.17 | both | recognition_measurement | This paragraph governs how changes in accounting estimates are recognised and the measurement approach (adjustment of carrying amounts) that must be applied. |
| 10.18 | both | disclosure | The paragraph requires entities to disclose information about changes in accounting estimates including their nature, financial effects in the current period, and estimates for future periods. |
| 10.19 | both | other | This paragraph provides a definition of 'prior period errors' with qualifying criteria, establishing conceptual foundations without imposing specific disclosure, presentation, or recognition requirements. |
| 10.20 | both | other | This paragraph provides a definition and clarification of what constitutes accounting errors, without imposing a requirement for disclosure, presentation, recognition, or measurement. |
| 10.21 | both | presentation | This paragraph specifies how to present the correction of prior period errors in financial statements (through retrospective adjustment), governing the format and treatment of comparative information. |
| 10.22 | both | recognition_measurement | This paragraph specifies how to account for and measure the effects of material errors when retrospective restatement is impracticable, establishing the measurement basis for correction of prior period errors. |

## Draft checklist rows (3)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 10.18 | both | Disclose the nature of any change in an accounting estimate and the effect of the change on assets, liabilities, income and expense for the current period. | conditional | has_accounting_estimate_changes == true | has_accounting_estimate_changes (NEW) | missing | standard-material | Reviewer should confirm that all changes in estimates (e.g. useful lives, provisions, bad debt allowances) are identified and that the quantified effect on each affected line (assets, liabilities, income, expense) is disclosed; immateriality may mean no disclosure is needed in practice. |
| 10.18 | both | If practicable, disclose the estimated effect of the change in accounting estimate on one or more future periods. | conditional | has_accounting_estimate_changes == true && future_period_effect_of_estimate_change_practicable == true | has_accounting_estimate_changes (NEW), future_period_effect_of_estimate_change_practicable (NEW) | missing | standard-material | Reviewer should assess whether management has considered practicability of quantifying future-period effects and documented that judgement where the disclosure is omitted. |
| 10.21 | both | To the extent practicable, correct a material prior period error retrospectively in the first financial statements authorised for issue after its discovery (by restating the comparative amounts for the prior period(s) presented in which the error occurred, or, if the error occurred before the earliest prior period presented, by restating the opening balances of assets, liabilities and equity for that earliest prior period). | conditional | has_material_prior_period_error == true | has_material_prior_period_error (NEW) | missing | standard-material | Reviewer should confirm that management has assessed whether retrospective correction is practicable and, if not, has disclosed why; also check that the earliest period for which restatement is required has been identified correctly and that all affected comparative line items and opening balances have been restated. |

## Proposed fact registry keys (3, all NEW)

| Key | Used by |
|---|---|
| future_period_effect_of_estimate_change_practicable | 10.18 |
| has_accounting_estimate_changes | 10.18 |
| has_material_prior_period_error | 10.21 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 2 | 3515 | 504 | $0.0181 |
| **total** | 2 | 3515 | 504 | **$0.0181** |
