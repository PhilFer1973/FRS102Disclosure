# Section 1AB — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 1AB.1 | pre-PR2024 | presentation | This paragraph specifies how small entities must present their profit or loss statement, including the format and alternatives available, which is a matter of presentation structure rather than recognition or measurement. |
| 1AB.1 | PR2024 | presentation | This paragraph specifies how small entities shall present their profit or loss statement, directing them to follow specific formats and structures from regulatory schedules. |
| 1AB.2 | both | disclosure | The paragraph requires small entities to provide additional disclosure in the notes to financial statements, including examples such as disaggregating gross profit or loss and disclosing turnover. |
| 1AB.3 | pre-PR2024 | presentation | This paragraph prescribes the minimum line items that must be presented in the income statement, governing the format and structure of the face-of-statement presentation. |
| 1AB.3 | PR2024 | presentation | This paragraph specifies the minimum line items that must be presented in the income statement format for small entities, governing the structure and content of the face of the financial statement. |
| 1AB.4 | both | presentation | This paragraph governs the format, structure, and ordering of line items on the income statement, permitting small entities to add line items and amend descriptions and ordering when necessary to explain financial performance. |

## Draft checklist rows (6)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 1AB.1 | pre-PR2024 | A small entity shall present its profit or loss for a period in an income statement that complies with either Part 1 General Rules and Formats of Schedule 1 to the Small Companies Regulations or Part 1 General Rules and Formats of Schedule 1 to the Small LLP Regulations. | always | — | — | missing | statutory | Reviewer should confirm which of the three resulting format alternatives the entity has adopted and that it is applied consistently; this requirement is directly underpinned by the Small Companies Regulations / Small LLP Regulations, so it is materiality-blind. |
| 1AB.1 | PR2024 | A small entity shall present its profit or loss for a period in an income statement (profit and loss account) prepared in accordance with the format requirements in Part 1 General Rules and Formats of Schedule 1 to the Small Companies Regulations (or Small LLP Regulations equivalent). | always | — | — | missing | statutory | Paragraph introduces three alternative formats without enumerating them here; reviewer should confirm which format alternative the entity has adopted and that it is consistently applied — the specific format requirements are set out in the referenced Schedule 1 provisions rather than in this paragraph itself. |
| 1AB.2 | both | A small entity applying the abridged profit and loss account must still ensure the financial statements give a true and fair view, and must consider whether additional note disclosures are necessary (e.g. disaggregating gross profit or loss, disclosing turnover) by reference to paragraph 1A.16. | conditional | applies_paragraph_1A1_adapted_balance_sheet_format == true | applies_paragraph_1A1_adapted_balance_sheet_format (NEW) | missing | statutory | Reviewer should check whether the abridged P&L omits turnover or gross profit disclosure and whether the notes contain sufficient disaggregation to satisfy the true and fair view requirement; this is a judgement-based assessment and the examples given (disaggregating gross profit, disclosing turnover) are non-exhaustive. |
| 1AB.3 | pre-PR2024 | When adapting a profit and loss account format under paragraph 1B(2) of Schedule 1 to the Small Companies Regulations, include as a minimum in the income statement line items presenting: turnover, other income, cost of stocks sold and services rendered, staff costs, depreciation and amortisation, other expenses, taxes on profits, and profit or loss — for the period. | conditional | applies_paragraph_1A1_adapted_balance_sheet_format == true | applies_paragraph_1A1_adapted_balance_sheet_format (NEW) | missing | statutory | The paragraph text as provided is incomplete (it ends without listing the required line items); the reviewer should confirm the full list of minimum line items from the authoritative text of FRS 102 paragraph 1AB.3 before relying on this row, and check that each required line item is present in the income statement — the trigger key 'applies_paragraph_1A1_adapted_balance_sheet_format' may need refinement once the fact key for adapting the P&L format specifically (rather than balance sheet format) is confirmed. |
| 1AB.3 | PR2024 | A small entity applying paragraph 1B(2) of Schedule 1 to the Small Companies Regulations to adapt a profit and loss account format must include in its income statement, as a minimum, the line items specified in paragraph 1AB.3 for the period. | conditional | applies_paragraph_1A1_adapted_balance_sheet_format == true | applies_paragraph_1A1_adapted_balance_sheet_format (NEW) | missing | statutory | The paragraph text as reproduced is incomplete (the list of required minimum line items is not shown); reviewer should verify the actual minimum line items required by paragraph 1AB.3 are all present in the income statement, and confirm the entity has indeed elected to apply paragraph 1B(2) of Schedule 1 to the Small Companies Regulations — a separate fact key for this specific election may be warranted if 'applies_paragraph_1A1_adapted_balance_sheet_format' does not precisely capture a profit and loss adaptation election rather than a balance sheet one. |
| 1AB.4 | both | When adapting the income statement, ensure the information given is at least equivalent to that required by the unadapted profit and loss account format. | conditional | applies_paragraph_1A1_adapted_balance_sheet_format == true | applies_paragraph_1A1_adapted_balance_sheet_format (NEW) | missing | statutory | Reviewer should check that any additional line items, amended descriptions or reordering in the income statement do not reduce the information below the minimum required by the statutory profit and loss account format; the equivalence test is a judgement call and directly underpinned by the Companies Act/Regulations format requirements. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| applies_paragraph_1A1_adapted_balance_sheet_format | 1AB.2, 1AB.3, 1AB.4 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 6 | 18074 | 1228 | $0.0726 |
| **total** | 6 | 18074 | 1228 | **$0.0726** |
