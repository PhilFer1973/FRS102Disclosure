# Section 34A — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 34A.1 | both | other | This paragraph provides definitional and explanatory guidance about liabilities and commitments without imposing a specific recognition, measurement, disclosure, or presentation requirement. |
| 34A.2 | both | recognition_measurement | This paragraph establishes the conditions under which general statements of intent or conditional promises do or do not create liabilities, thereby governing whether recognition should occur. |
| 34A.3 | both | recognition_measurement | This paragraph specifies the conditions for recognising a liability (commitment communicated to recipient, creating valid expectation), which is a recognition criterion rather than a disclosure, presentation, or measurement requirement. |
| 34A.4 | both | recognition_measurement | This paragraph specifies when commitments subject to performance-related conditions are not recognised as liabilities and the timing of liability recognition when conditions are met. |
| 34A.5 | both | recognition_measurement | This paragraph provides guidance on how to distinguish performance-related conditions from non-performance conditions in order to determine when a commitment should be recognized as a liability or contingent liability. |
| 34A.6 | both | disclosure | The paragraph requires entities to make full and informative disclosures about the existence of unrecognised funding commitments and their sources of funding in the notes to the financial statements. |

## Draft checklist rows (1)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 34A.6 | both | Disclose the existence of funding commitments that are not recognised and the sources of funding for those unrecognised commitments. | conditional | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies == true | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies (NEW) | missing | standard-material | The paragraph is aspirational in tone ('it is important that … disclosures are made') rather than a strict mandatory 'shall'; reviewer should assess whether this rises to a hard requirement or is best treated as strongly encouraged best practice, and whether the existing fact key adequately captures unrecognised funding commitments specifically (as distinct from guarantees or contingencies). |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| has_off_balance_sheet_financial_commitments_guarantees_or_contingencies | 34A.6 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 1 | 3153 | 191 | $0.0123 |
| **total** | 1 | 3153 | 191 | **$0.0123** |
