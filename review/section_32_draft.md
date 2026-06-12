# Section 32 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 32.1 | both | scope_transition | This paragraph defines the scope of the section and the matters it applies to (recognition, measurement and disclosure of events after the reporting period), rather than imposing specific disclosure, presentation, or measurement requirements. |
| 32.2 | both | other | This paragraph provides a definition of events after the end of the reporting period and identifies two types without imposing substantive recognition, measurement, presentation or disclosure requirements. |
| 32.3 | both | other | This paragraph provides a definition of what constitutes events after the end of the reporting period, establishing the scope and boundary conditions without imposing a specific recognition, measurement, disclosure, or presentation requirement. |
| 32.4 | both | recognition_measurement | This paragraph establishes the requirement for entities to adjust recognised amounts in their financial statements based on whether events after the reporting period are adjusting events, which is a recognition and measurement principle rather than a disclosure or presentation requirement. |
| 32.5 | both | recognition_measurement | This paragraph specifies which post-balance-sheet events require adjustment to recognized amounts or recognition of previously unrecognized items, which is a recognition and measurement determination. |
| 32.6 | both | recognition_measurement | This paragraph prescribes that amounts in financial statements shall not be adjusted for non-adjusting post-balance sheet events, governing the measurement treatment of items recognised. |
| 32.7 | both | other | This paragraph introduces examples of non-adjusting events and provides guidance on classification rather than imposing a specific requirement for disclosure, presentation, or recognition. |
| 32.7A | both | recognition_measurement | This paragraph specifies a condition that determines whether an entity recognizes its financial statements on a going concern basis, which is a fundamental measurement assumption. |
| 32.7B | pre-PR2024 | disclosure | The paragraph requires disclosure of the effect of post-reporting-period deterioration on going concern status, with specific reference to paragraph 3.9 disclosure requirements. |
| 32.7B | PR2024 | disclosure | The paragraph requires disclosure of going concern issues and fundamental changes in accounting basis through reference to the disclosure requirements in paragraph 3.9. |
| 32.8 | both | recognition_measurement | This paragraph establishes that dividends declared after the reporting period should not be recognised as a liability, which is a recognition rule determining when an obligation exists. |
| 32.9 | both | disclosure | The paragraph explicitly requires an entity to disclose specific information (the date of authorisation and the authorising party) in the financial statements. |

## Draft checklist rows (3)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 32.7B | pre-PR2024 | If a post-period deterioration in operating results or financial position causes the going concern assumption to be no longer appropriate, apply the disclosure requirements of paragraph 3.9 (fundamental change in basis of accounting) rather than merely adjusting amounts within the original basis. | conditional | not_going_concern == true | not_going_concern (NEW) | missing | statutory | Reviewer should confirm whether any post-period deterioration has been evaluated by management and, if going concern is no longer appropriate, that paragraph 3.9 disclosures (not just adjustments to line items) have been made; interaction with company law going concern disclosure requirements in CA 2006 s.393 should also be considered. |
| 32.7B | PR2024 | If a post-balance-sheet deterioration in operating results or financial position causes the going concern assumption to no longer be appropriate, apply a fundamental change in the basis of accounting (not merely an adjustment to existing amounts) and make the disclosures required by paragraph 3.9. | conditional | not_going_concern == true | not_going_concern (NEW) | missing | statutory | Reviewer should confirm whether any post-period deterioration has been identified and assessed by management; the trigger arises specifically where going concern is no longer appropriate after considering post-period events, and paragraph 3.9 disclosures must be cross-checked as present. |
| 32.9 | both | Disclose the date the financial statements were authorised for issue and who gave that authorisation. | always | — | — | missing | standard-material | Confirm both elements are present (date and the authorising party, e.g. board of directors); also consider whether this overlaps with any Companies Act requirement regarding signing of accounts. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| not_going_concern | 32.7B |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 3 | 8054 | 459 | $0.0310 |
| **total** | 3 | 8054 | 459 | **$0.0310** |
