# Section 4 — draft checklist rows (PILOT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 4.1 | both | scope_transition | This paragraph establishes the scope of Section 4 and explains which entities must comply with the statement of financial position requirements under FRS 102. |
| 4.1A | both | scope_transition | This paragraph defines the scope of Section 4 by establishing an exemption for small entities applying Section 1A, which is a scope limitation rather than a disclosure, recognition, or measurement requirement. |
| 4.2 | both | disclosure | This paragraph requires an entity to present a statement of financial position in a specific format, which is a presentation/format requirement for financial statements. |
| 4.2A | both | disclosure | This paragraph requires the entity to include specific line items in the statement of financial position and distinguish between current and non-current items, which is a presentation requirement. |
| 4.2B | both | disclosure | The paragraph explicitly requires an entity to disclose specific sub-classifications of line items either in the statement of financial position or in the notes, which is a disclosure requirement. |
| 4.2C | both | disclosure | This paragraph establishes requirements for how line items should be presented and ordered on the balance sheet, allowing flexibility in descriptions and aggregation while maintaining equivalence to prescribed formats. |
| 4.2D | both | disclosure | This paragraph requires entities to present and distinguish current and non-current classifications separately on the face of the statement of financial position, which is a presentation format requirement. |
| 4.3 | both | disclosure | This requires entities to present additional line items, headings and subtotals in the statement of financial position, which is a presentation/format requirement for financial statements. |
| 4.4 | both | other | This paragraph is deleted and contains no active requirement. |
| 4.4A | both | disclosure | This paragraph requires entities to disclose the amount of debtors due after more than one year either on the face of the statement of financial position or in the notes, depending on materiality considerations. |
| 4.5 | both | other | This paragraph has been deleted and contains no substantive requirement or guidance. |
| 4.6 | both | other | The paragraph is marked as deleted and contains no substantive requirement or content to classify. |
| 4.7 | both | recognition_measurement | This paragraph establishes the classification rule for determining whether a creditor should be recognized as current or non-current based on settlement timing and rights. |
| 4.8 | both | other | This paragraph is deleted and contains no operative requirement. |
| 4.12 | both | disclosure | This paragraph explicitly requires entities to disclose specified information about share capital either on the statement of financial position or in notes. |
| 4.13 | both | disclosure | This paragraph requires entities without share capital to disclose information about changes in equity categories and the rights, preferences and restrictions attaching to each category. |
| 4.14 | both | disclosure | This paragraph requires specific information to be disclosed in the financial statements regarding major disposals covered by binding sale agreements. |

## Draft checklist rows (12)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 4.2 | both | Present a statement of financial position (balance sheet) in accordance with the applicable balance sheet format requirements | always | — | — | missing | statutory | This is a company law requirement as well as FRS 102; reviewer should confirm the balance sheet format adopted (e.g. Companies Act formats) and that it is consistently applied across periods. |
| 4.2A | both | When adapting a Schedule 1 balance sheet format under paragraph 1A(1) of the Regulations, include as a minimum in the statement of financial position line items that present each of the required items, distinguishing between current and non-current classifications. | conditional | applies_paragraph_1A1_adapted_balance_sheet_format == true | applies_paragraph_1A1_adapted_balance_sheet_format (NEW) | missing | statutory | Paragraph 4.2A sets out a minimum line-item list (not reproduced in this excerpt) that must be checked item by item; reviewer should confirm that both the current/non-current split and every required minimum line item are present in the face of the balance sheet, and that the choice to apply paragraph 1A(1) is itself properly disclosed. |
| 4.2B | both | An entity choosing to apply paragraph 1A(1) of Schedule 1 to the Regulations shall disclose, either in the statement of financial position or in the notes, the sub-classifications of the line items presented. | conditional | applies_schedule1_paragraph_1A1 == true | applies_schedule1_paragraph_1A1 (NEW) | missing | statutory | Paragraph 4.2B is a lead-in sentence; the actual sub-classifications required will be enumerated in subsequent sub-paragraphs — reviewer should ensure each specific sub-classification is checked against those follow-on items. Confirm the entity has actively elected paragraph 1A(1) of Schedule 1 to the Regulations and that the sub-classifications appear either on the face of the SoFP or in the notes. |
| 4.2C | both | Ensure that any adaptation of balance sheet line-item descriptions, ordering, or aggregation of similar items provides information at least equivalent to that required by the unadapted balance sheet format. | conditional | balance_sheet_format_adapted == true | balance_sheet_format_adapted (NEW) | missing | standard-material | Reviewer must judge whether the adapted presentation is genuinely equivalent to the standard format; this interacts with company law requirements on the form and content of the balance sheet (CA 2006 / SI 2008/410), so equivalence should be assessed against both the FRS 102 format and applicable statutory format. |
| 4.2D | both | Present current and non-current assets as separate classifications in the statement of financial position to distinguish between current and non-current items. | always | — | — | missing | standard-material | Confirm that the face of the balance sheet explicitly segregates current and non-current assets into labelled classifications rather than relying solely on ordering or notes disclosure. |
| 4.2D | both | Present current and non-current liabilities as separate classifications in the statement of financial position to distinguish between current and non-current items. | always | — | — | missing | standard-material | Confirm that the face of the balance sheet explicitly segregates current and non-current liabilities into labelled classifications; note interaction with the Companies Act formats which use creditors due within/after one year and check these satisfy the FRS 102 requirement. |
| 4.3 | both | Present additional line items, headings and subtotals in the statement of financial position when such presentation is relevant to an understanding of the entity's financial position. | conditional | additional_sofp_line_items_relevant == true | additional_sofp_line_items_relevant (NEW) | missing | standard-material | Requires preparer judgement on what is 'relevant to an understanding'; reviewer should assess whether the current level of aggregation on the face of the balance sheet obscures any material or unusual items that would warrant separate presentation. |
| 4.4A | both | Where the amount of debtors due after more than one year is so material in the context of total net current assets that its absence from the face of the statement of financial position would cause readers to misinterpret the financial statements, disclose that amount on the face of the statement of financial position within current assets. | conditional | has_debtors_due_after_one_year == true AND debtors_after_one_year_material_to_net_current_assets == true AND entity_applies_schedule1_para1A1 == false | has_debtors_due_after_one_year (NEW), debtors_after_one_year_material_to_net_current_assets (NEW), entity_applies_schedule1_para1A1 (NEW) | missing | standard-material | The materiality threshold is explicitly framed relative to total net current assets rather than total assets, requiring a specific judgement; the paragraph also notes that note disclosure will be satisfactory in most cases, so the reviewer should assess whether face-of-SoFP disclosure is genuinely required or whether note disclosure suffices, and confirm whether the entity has elected to apply Schedule 1 paragraph 1A(1) of the Regulations (which disapplies this requirement). |
| 4.12 | both | Disclose, either in the statement of financial position or in the notes, information about the entity's share capital (the specific items required by this paragraph) | conditional | has_share_capital == true | has_share_capital (NEW) | missing | standard-material | Paragraph 4.12 lists specific sub-items to be disclosed (e.g. number of shares authorised, issued, rights, etc.) which are enumerated in the sub-paragraphs; this parent row covers the general trigger — reviewer should ensure each sub-item is checked against the detailed list in 4.12(a)–(f) or equivalent sub-paragraphs. |
| 4.13 | both | An entity without share capital shall disclose information equivalent to paragraph 4.12(a), showing changes during the period in each category of equity | conditional | has_share_capital == false | has_share_capital (NEW) | missing | standard-material | Reviewer should confirm the entity's legal form (e.g. partnership, LLP, trust, unlimited company) to establish whether share capital is absent and this paragraph rather than 4.12(a) applies. |
| 4.13 | both | An entity without share capital shall disclose the rights, preferences and restrictions attaching to each category of equity | conditional | has_share_capital == false | has_share_capital (NEW) | missing | standard-material | Check whether all categories of equity interest (e.g. partners' capital, members' interests) have been identified and that rights, preferences and restrictions for each are adequately described. |
| 4.14 | both | Disclose information about a binding sale agreement for a major disposal of assets or a disposal group when such an agreement exists at the reporting date. | conditional | has_binding_sale_agreement_for_major_disposal == true | has_binding_sale_agreement_for_major_disposal (NEW) | missing | standard-material | The paragraph introduces the disclosure obligation but does not itself list the specific items to be disclosed; the reviewer should ensure the detailed disclosure items (likely in a sub-list following this paragraph) are also checked, and should confirm whether 'major' is assessed on a qualitative or quantitative basis by management. |

## Proposed fact registry keys (9, all NEW)

| Key | Used by |
|---|---|
| additional_sofp_line_items_relevant | 4.3 |
| applies_paragraph_1A1_adapted_balance_sheet_format | 4.2A |
| applies_schedule1_paragraph_1A1 | 4.2B |
| balance_sheet_format_adapted | 4.2C |
| debtors_after_one_year_material_to_net_current_assets | 4.4A |
| entity_applies_schedule1_para1A1 | 4.4A |
| has_binding_sale_agreement_for_major_disposal | 4.14 |
| has_debtors_due_after_one_year | 4.4A |
| has_share_capital | 4.12, 4.13 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-haiku-4-5 | 17 | 7784 | 753 | $0.0115 |
| claude-sonnet-4-6 | 10 | 9977 | 1953 | $0.0592 |
| **total** | 27 | 17761 | 2706 | **$0.0708** |
