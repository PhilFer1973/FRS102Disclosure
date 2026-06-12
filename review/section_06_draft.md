# Section 6 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 6.1 | both | presentation | This paragraph governs the format and structure of how changes in equity are presented, specifying whether an entity presents a full statement of changes in equity or an alternative statement of income and retained earnings. |
| 6.1A | pre-PR2024 | scope_transition | This paragraph clarifies the scope of application and provides transitional guidance regarding which entities must comply with Section 6 and which may apply alternative requirements under Section 1A. |
| 6.1A | PR2024 | scope_transition | This paragraph defines the scope of Section 6 by establishing which entities are exempt from its requirements and references transitional/alternative provisions for small entities. |
| 6.2 | both | presentation | This paragraph prescribes the structure and contents that must be presented in the statement of changes in equity, governing what line items and information shall be included on the face of that statement. |
| 6.3 | both | presentation | This paragraph governs the required format and structure of the statement of changes in equity, specifying what components must be presented in that financial statement. |
| 6.3B | PR2024 | disclosure | The paragraph requires entities to provide specific information in the notes to the financial statements about dividends paid, disaggregated by class of share capital. |
| 6.4 | both | presentation | This paragraph governs the permitted alternative format and structure of financial statements by allowing entities to present a combined statement of income and retained earnings instead of separate statements. |
| 6.5 | both | presentation | This paragraph specifies what items must be presented in the statement of income and retained earnings, governing the structure and content of that financial statement. |

## Draft checklist rows (10)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 6.1 | both | Present changes in equity for the reporting period, either in a statement of changes in equity or (if specified conditions are met and the entity chooses) in a statement of income and retained earnings. | always | — | — | missing | standard-material | Reviewer should confirm which presentation route the entity has adopted and that any conditions required to use the statement of income and retained earnings route (addressed in later Section 6 paragraphs) are actually satisfied. |
| 6.2 | both | Present in the statement of changes in equity: profit or loss for the reporting period | always | — | — | missing | standard-material | Check that profit or loss for the period is explicitly presented as a line item or column total within the SOCIE rather than merely cross-referenced from the income statement. |
| 6.2 | both | Present in the statement of changes in equity: other comprehensive income for the period | always | — | — | missing | standard-material | Verify that each component of OCI is shown; where an entity has no OCI in any period this line may be nil but the requirement still applies unless the entity uses the single-statement presentation permitted under Section 6. |
| 6.2 | both | Present in the statement of changes in equity: the effects of changes in accounting policies and corrections of material errors recognised in the period | conditional | has_accounting_policy_changes == true | has_accounting_policy_changes (NEW) | missing | standard-material | 'has_accounting_policy_changes' should also cover material error corrections; reviewer should confirm that retrospective restatements are reflected here consistently with Section 10 disclosures. |
| 6.2 | both | Present in the statement of changes in equity: amounts of investments by equity investors during the period | always | — | — | missing | standard-material | Check that all capital contributions and share issues are included; where there are none a nil or absent movement is acceptable but the reviewer should confirm no transactions have been omitted. |
| 6.2 | both | Present in the statement of changes in equity: dividends and other distributions to equity investors during the period | always | — | — | missing | standard-material | Confirm all distributions (including non-cash distributions and interim dividends) are captured; reviewer should cross-check against the directors' report and any interim dividend approvals. |
| 6.3 | both | Present a statement of changes in equity as a primary statement | always | — | — | missing | standard-material | Section 6 as a whole must be read with s.3 true-and-fair override; confirm whether entity instead uses statement of income and retained earnings under Section 6.4 (which substitutes for SOCIE) — if so, this requirement is replaced by that alternative. |
| 6.3B | PR2024 | When more than one class of share capital exists, disclose dividends paid both in aggregate and per share separately for each class of share capital. | conditional | has_share_capital == true AND has_multiple_share_capital_classes == true | has_share_capital (NEW), has_multiple_share_capital_classes (NEW) | missing | standard-material | Reviewer should confirm the number of distinct share classes and verify that both aggregate and per-share dividend figures are presented for each class; also consider whether any class paid no dividend (disclosure may still be needed for completeness). |
| 6.4 | both | Present a statement of income and retained earnings (in place of a statement of comprehensive income and a statement of changes in equity) only when the only changes to equity during the periods presented arise from: profit or loss, payment of dividends, corrections of prior period material errors, and changes in accounting policy. | conditional | presents_statement_of_income_and_retained_earnings == true | presents_statement_of_income_and_retained_earnings (NEW) | both | standard-material | Reviewer should confirm that no other equity movements exist (e.g. share issues, revaluations, other comprehensive income) that would disqualify use of this combined statement; if any such movements are present the entity must instead present a full statement of comprehensive income and a separate statement of changes in equity. |
| 6.5 | both | Present the following items in the statement of income and retained earnings in addition to the information required by Section 5: (items specified in paragraph 6.5(a)–(d) as applicable) | conditional | presents_statement_of_income_and_retained_earnings == true | presents_statement_of_income_and_retained_earnings (NEW) | missing | standard-material | Paragraph 6.5 sets out the additional line items required in the SIRE; reviewer should confirm all sub-items (retained earnings opening balance, dividends, restatements and closing balance) are present since this paragraph appears to be introductory — cross-check with paragraph 6.5(a)–(d) for the exhaustive list. |

## Proposed fact registry keys (4, all NEW)

| Key | Used by |
|---|---|
| has_accounting_policy_changes | 6.2 |
| has_multiple_share_capital_classes | 6.3B |
| has_share_capital | 6.3B |
| presents_statement_of_income_and_retained_earnings | 6.4, 6.5 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 6 | 8865 | 1296 | $0.0460 |
| **total** | 6 | 8865 | 1296 | **$0.0460** |
