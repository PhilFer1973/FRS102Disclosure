# Section 31 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 31.1 | both | scope_transition | This paragraph defines the scope of the section by specifying which entities it applies to (those in hyperinflationary economies) and establishes when the requirement takes effect. |
| 31.2 | both | other | This paragraph provides guidance on how to exercise judgment in identifying hyperinflation without establishing a binding recognition requirement or disclosure obligation, serving as interpretive guidance rather than a mandatory requirement. |
| 31.3 | both | presentation | This paragraph requires the restatement and presentation of all amounts in the financial statements using the measuring unit current at the reporting period end, governing how financial statement items must be formatted and expressed. |
| 31.4 | both | other | This paragraph provides guidance on selecting a general price index for hyperinflationary accounting but does not impose a specific requirement, only noting that entities will follow a recognised index. |
| 31.5 | both | recognition_measurement | This paragraph specifies the measurement method (restatement using a general price index) for statement of financial position amounts in hyperinflationary economies. |
| 31.6 | both | other | This paragraph provides definitions and explanatory guidance about what monetary items are without imposing specific disclosure, presentation, or recognition/measurement requirements. |
| 31.7 | both | presentation | This paragraph specifies how linked assets and liabilities shall be presented in the restated statement of financial position following their adjustment, governing the format and placement of these items on the face of the statement. |
| 31.8 | both | other | This paragraph provides a definitional statement classifying assets and liabilities as non-monetary; it establishes a category without imposing a specific disclosure, presentation, or recognition/measurement requirement. |
| 31.9 | both | recognition_measurement | This paragraph specifies how equity components are measured and restated at the transition to hyperinflation accounting, including the application of a general price index and the treatment of revaluation surpluses. |
| 31.10 | both | presentation | The paragraph specifies how components of owners' equity shall be restated and presented in the statement of changes in equity, governing the structure and ordering of equity movements. |
| 31.11 | both | recognition_measurement | This paragraph specifies how items of income and expenses shall be measured and restated in hyperinflationary economies by applying price index changes from initial recognition to period-end. |
| 31.12 | both | recognition_measurement | This paragraph specifies how items in the cash flow statement shall be measured (in current measuring units at period end), which is a measurement requirement rather than a disclosure or presentation requirement. |
| 31.13 | both | recognition_measurement | This paragraph establishes how to recognize and measure gains or losses on monetary positions during inflation, specifying that gains/losses on net monetary position shall be included in profit or loss (with unrealised gains in OCI) and how to offset price-linked adjustments. |
| 31.14 | both | recognition_measurement | This paragraph specifies how to measure and determine the carrying amounts of assets and liabilities when an entity transitions from hyperinflation accounting to normal accounting, establishing the basis for future measurement. |
| 31.15 | both | disclosure | The paragraph explicitly requires an entity to disclose specified information, which is the hallmark of a disclosure requirement. |

## Draft checklist rows (6)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 31.3 | both | State all amounts in the financial statements in terms of the measuring unit current at the end of the reporting period when the functional currency is the currency of a hyperinflationary economy. | conditional | functional_currency_is_hyperinflationary == true | functional_currency_is_hyperinflationary (NEW) | missing | standard-material | Reviewer should confirm whether the entity's functional currency jurisdiction qualifies as hyperinflationary (e.g. by reference to cumulative inflation rates or other indicators in paragraph 31.2) and that all line items, including equity, have been restated to the closing measuring unit. |
| 31.3 | both | State comparative information for the previous period, and any information presented in respect of earlier periods, in terms of the measuring unit current at the end of the reporting period. | conditional | functional_currency_is_hyperinflationary == true | functional_currency_is_hyperinflationary (NEW) | missing | standard-material | Reviewer should check that prior-period comparatives and any earlier-period information have all been restated to the closing measuring unit, not merely rolled forward at a historical index; interaction with paragraph 3.14 comparative requirements should be confirmed. |
| 31.7 | both | Index-linked or otherwise price-linked assets and liabilities shall be adjusted in accordance with their linking agreement and presented at the resulting adjusted amount in the restated statement of financial position (i.e. the hyperinflationary-restated balance sheet). | conditional | functional_currency_is_hyperinflationary == true | functional_currency_is_hyperinflationary (NEW) | missing | standard-material | Reviewer should confirm that every price-linked instrument (e.g. index-linked bonds, CPI-linked loans) has been remeasured per its contractual linking mechanism rather than by application of the general price index used for other restatements under Section 31. |
| 31.10 | both | Restate all components of owners' equity at the end of the period by applying a general price index from the beginning of the period, or from the date of contribution if later, in hyperinflationary functional currency financial statements. | conditional | functional_currency_is_hyperinflationary == true | functional_currency_is_hyperinflationary (NEW) | missing | standard-material | Reviewer should confirm that the general price index used is appropriate for the economy in question and that the restatement date (beginning of period vs date of contribution) has been correctly determined for each equity component. |
| 31.10 | both | Disclose changes in owners' equity for the period in accordance with Section 6 (Statement of Changes in Equity and Statement of Income and Retained Earnings) in hyperinflationary functional currency financial statements. | conditional | functional_currency_is_hyperinflationary == true | functional_currency_is_hyperinflationary (NEW) | missing | standard-material | Reviewer should check that the statement of changes in equity (or statement of income and retained earnings, if that presentation is adopted) reflects the hyperinflationary restatements and complies with Section 6 requirements. |
| 31.15 | both | Disclose all information required by Section 31 for entities to which that section applies (note: paragraph 31.15 is an incomplete stub — the specific disclosure items it introduces are listed in subsequent sub-paragraphs not reproduced here; flag for manual review of 31.15(a) onwards). | always | — | — | missing | standard-material | Paragraph 31.15 as supplied is a heading-only stub with no enumerated disclosure items; the reviewer must check the full text of 31.15(a)–(x) in the standard to confirm all sub-paragraph requirements are covered by separate checklist rows. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| functional_currency_is_hyperinflationary | 31.10, 31.3, 31.7 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 4 | 10681 | 967 | $0.0465 |
| **total** | 4 | 10681 | 967 | **$0.0465** |
