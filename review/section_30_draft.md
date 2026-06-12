# Section 30 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 30.1 | both | scope_transition | This paragraph defines the scope and applicability of Section 30, establishing which entities or circumstances fall within this section's requirements. |
| 30.1A | both | scope_transition | This paragraph explicitly defines the scope of Section 30 by stating what is excluded from its application and cross-referencing another section for the relevant requirements. |
| 30.2 | both | recognition_measurement | This paragraph establishes the foundational rule for determining functional currency, which is a core measurement principle that affects how transactions and balances are subsequently recognized and measured in foreign currency accounting. |
| 30.3 | both | recognition_measurement | This paragraph establishes the criteria and factors for determining an entity's functional currency, which is a measurement classification fundamental to how transactions and balances are recorded. |
| 30.4 | both | other | This paragraph provides guidance on factors that may help determine functional currency, but imposes no mandatory requirement itself and serves as explanatory material. |
| 30.5 | both | other | This paragraph provides guidance on factors to consider when determining functional currency for a foreign operation without imposing specific recognition, measurement, disclosure, or presentation requirements. |
| 30.6 | both | other | This paragraph provides a definition of what constitutes a foreign currency transaction without imposing any recognition, measurement, disclosure or presentation requirements. |
| 30.7 | both | recognition_measurement | This paragraph establishes how foreign currency transactions must be initially measured by specifying the application of the spot exchange rate at the transaction date. |
| 30.8 | both | recognition_measurement | The paragraph establishes when a foreign currency transaction is recognized (the transaction date) and how exchange rates should be applied at recognition, which are measurement requirements. |
| 30.9 | both | recognition_measurement | This paragraph establishes what an entity must do at the end of each reporting period, which constitutes a recognition or measurement action rather than disclosure, presentation, or scope requirements. |
| 30.10 | both | recognition_measurement | This paragraph establishes when and how exchange differences on monetary items shall be recognized in profit or loss, which is a recognition and measurement requirement. |
| 30.11 | both | recognition_measurement | This paragraph establishes how and where exchange components of gains or losses on non-monetary items must be recognised (OCI versus profit or loss), which is a measurement and classification requirement. |
| 30.12 | both | recognition_measurement | This paragraph establishes the accounting treatment for monetary items that are part of a net investment in a foreign operation, specifying when such items should be accounted for under paragraph 30.13 rather than as ordinary monetary items. |
| 30.13 | both | recognition_measurement | This paragraph specifies where exchange differences on monetary items that are part of a net investment in a foreign operation must be recognised (profit or loss, OCI, or equity) and when they should not be recognised (disposal), which are recognition and measurement requirements. |
| 30.14 | both | recognition_measurement | This paragraph specifies the accounting treatment and timing for applying translation procedures when an entity's functional currency changes, which is a recognition and measurement requirement rather than a disclosure or presentation requirement. |
| 30.15 | both | other | This paragraph provides guidance on the stability and rationale of functional currency determination rather than imposing a specific disclosure, presentation, recognition, or measurement requirement. |
| 30.16 | both | recognition_measurement | This paragraph specifies how changes in functional currency are measured and accounted for (prospectively, using the exchange rate at the date of change), which is a recognition and measurement requirement. |
| 30.17 | both | presentation | This paragraph prescribes how an entity shall translate and present its financial information when the presentation currency differs from the functional currency, governing the format and structure of financial statement presentation. |
| 30.18 | both | presentation | This paragraph specifies the procedures and methodology for translating financial results and financial position into a presentation currency, which governs the format and structure of how items are presented in the financial statements. |
| 30.19 | both | recognition_measurement | This paragraph establishes the requirement for how foreign currency transactions are measured and translated (using spot rate or approximations), with conditions on when approximations are inappropriate. |
| 30.20 | both | other | This paragraph provides a cross-reference and definitional clarification identifying the source of exchange differences, with no independent disclosure, presentation, recognition or measurement requirement. |
| 30.21 | both | recognition_measurement | This paragraph specifies the procedural order and method for adjusting financial statements in hyperinflationary economies before translation, which governs how items are measured and recognized in such circumstances. |
| 30.22 | both | presentation | This paragraph governs the consolidation procedures and treatment of intragroup balances in the consolidated financial statements, including how exchange differences must be presented and which statement they appear in. |
| 30.23 | both | recognition_measurement | This paragraph establishes how goodwill and fair value adjustments arising from foreign operations are to be measured and accounted for (treated as assets/liabilities of the foreign operation and translated at closing rate), which is a measurement treatment rather than a disclosure requirement. |
| 30.24 | both | other | This paragraph provides a clarifying cross-reference and definition that applies existing requirements to a specific context (groups with parents) but does not itself impose new disclosure, presentation, recognition, or measurement requirements. |
| 30.25 | both | disclosure | The paragraph explicitly requires an entity to disclose specific information, which is a disclosure requirement. |
| 30.26 | both | disclosure | The paragraph requires entities to disclose the presentation currency, functional currency (when different), and reasons for currency choices in the financial statements or notes. |
| 30.27 | both | disclosure | The paragraph requires an entity to disclose the fact of a functional currency change and its reason in the financial statements. |

## Draft checklist rows (8)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 30.17 | both | When the presentation currency differs from the functional currency, translate all items of income and expense and financial position into the presentation currency. | conditional | presentation_currency_differs_from_functional_currency == true | presentation_currency_differs_from_functional_currency (NEW) | missing | standard-material | Reviewer should confirm which translation method (paragraphs 30.18–30.19) has been applied and that the entity has identified its functional currency correctly; the paragraph itself only mandates translation without specifying the mechanics. |
| 30.18 | both | When translating results and financial position into a presentation currency that differs from the functional currency (where the functional currency is not that of a hyperinflationary economy), apply the specific translation procedures set out in paragraph 30.18. | conditional | presentation_currency_differs_from_functional_currency == true AND functional_currency_is_hyperinflationary == false | presentation_currency_differs_from_functional_currency (NEW), functional_currency_is_hyperinflationary (NEW) | both | standard-material | Reviewer should confirm which sub-procedures (closing rate for assets/liabilities, historical/average rate for income/expenses, recognition of exchange differences) have been applied and that the entity's functional currency has been correctly assessed as non-hyperinflationary before applying this paragraph rather than Section 31. |
| 30.22 | both | Apply normal consolidation procedures (including elimination of intragroup balances and transactions) together with the translation procedures in paragraphs 30.17–30.21 when incorporating a foreign operation's assets, liabilities, income and expenses into the consolidated financial statements. | conditional | is_parent_entity == true | is_parent_entity (NEW) | missing | standard-material | Reviewer should confirm that intragroup eliminations have been performed and that the translation procedures of paragraphs 30.17–30.21 have been applied; interaction with Section 9 consolidation requirements should also be checked. |
| 30.22 | both | Do not eliminate an intragroup monetary asset (or liability) against the corresponding intragroup liability (or asset) without recognising the results of currency fluctuations; continue to recognise the resulting exchange difference either in profit or loss or, where paragraph 30.13 conditions are met, in other comprehensive income. | conditional | is_parent_entity == true and has_intragroup_monetary_items_in_foreign_currency == true | is_parent_entity (NEW), has_intragroup_monetary_items_in_foreign_currency (NEW) | both | standard-material | Reviewer should verify whether any intragroup monetary balances denominated in a foreign currency exist and confirm that exchange differences on those items have been routed correctly to profit or loss (or OCI where the paragraph 30.13 criteria for long-term net-investment-type items are satisfied) rather than being eliminated on consolidation. |
| 30.25 | both | Disclose the information required by Section 30 (Foreign Currency Translation) as specified in paragraph 30.25 | always | — | — | missing | standard-material | Paragraph 30.25 as provided is incomplete (truncated after 'the following:'); reviewer should verify the full list of sub-requirements in the published standard and expand this placeholder row into individual checkable items covering each specified disclosure (e.g. functional currency, presentation currency, exchange differences recognised, etc.). |
| 30.26 | both | Disclose the currency in which the financial statements are presented. | always | — | — | missing | standard-material | Verify that the presentation currency is explicitly stated somewhere in the financial statements (e.g. in accounting policies); this is required regardless of what the currency is. |
| 30.26 | both | When the presentation currency differs from the functional currency, state that fact, disclose the functional currency, and explain the reason for using a different presentation currency. | conditional | presentation_currency_differs_from_functional_currency == true | presentation_currency_differs_from_functional_currency (NEW) | both | standard-material | Reviewer should confirm the functional currency has been correctly determined under Section 30 and that the explanation given for adopting a different presentation currency is substantive rather than boilerplate. |
| 30.27 | both | Disclose the fact of and reason for any change in the functional currency of the reporting entity or a significant foreign operation. | conditional | has_functional_currency_change == true | has_functional_currency_change (NEW) | missing | standard-material | Reviewer should confirm whether a change in functional currency has occurred for either the entity itself or any significant foreign operation, and that both the fact and the reason are explicitly stated in the notes. |

## Proposed fact registry keys (5, all NEW)

| Key | Used by |
|---|---|
| functional_currency_is_hyperinflationary | 30.18 |
| has_functional_currency_change | 30.27 |
| has_intragroup_monetary_items_in_foreign_currency | 30.22 |
| is_parent_entity | 30.22 |
| presentation_currency_differs_from_functional_currency | 30.17, 30.18, 30.26 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 6 | 15989 | 1218 | $0.0662 |
| **total** | 6 | 15989 | 1218 | **$0.0662** |
