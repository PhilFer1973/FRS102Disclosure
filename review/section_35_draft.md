# Section 35 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 35.1 | pre-PR2024 | scope_transition | This paragraph defines the scope of the first-time adoption section by specifying which entities it applies to, which is a scope determination at the transition point to FRS 102. |
| 35.1 | PR2024 | scope_transition | This paragraph defines the scope of the section by specifying which entities are subject to first-time adoption guidance and their previous accounting frameworks. |
| 35.2 | both | scope_transition | This paragraph establishes transitional provisions for entities adopting FRS 102, specifying how prior period accounting treatments should be handled based on previous compliance status. |
| 35.3 | both | scope_transition | This paragraph explicitly defines the scope and applicability of the section to first-time adopters and their first conforming financial statements, establishing a transitional provision. |
| 35.4 | pre-PR2024 | scope_transition | This paragraph defines what constitutes an entity's 'first financial statements' under FRS 102, which is a foundational scope and transitional concept for applying the standard's first-time adoption requirements. |
| 35.4 | PR2024 | scope_transition | This paragraph defines what constitutes an entity's first financial statements under FRS 102, which is a definitional provision relating to the scope and applicability of the standard's transitional rules. |
| 35.5 | both | other | This is a cross-reference to a definition in another section without imposing its own independent requirement. |
| 35.6 | both | scope_transition | This paragraph defines the date of transition to FRS 102 based on the earliest period for which full comparative information is presented, which is a foundational scope and timing concept for the standard's application. |
| 35.7 | both | recognition_measurement | This paragraph governs the timing and conditions for recognizing or adjusting items when an entity transitions to FRS 102, which is a recognition and measurement matter. |
| 35.8 | both | recognition_measurement | This paragraph specifies how to recognize and measure adjustments arising from changes in accounting policies upon transition to FRS 102, requiring direct recognition in retained earnings. |
| 35.8A | PR2024 | scope_transition | This paragraph prescribes transitional provisions that prohibit the inclusion of previously capitalised borrowing costs when an entity changes its accounting policy upon transition to FRS 102. |
| 35.8B | PR2024 | scope_transition | This paragraph addresses the transitional treatment of capitalised development costs when an entity changes its accounting policy upon transition to FRS 102. |
| 35.8C | PR2024 | scope_transition | This paragraph sets out transitional provisions and options available specifically on first-time adoption of FRS 102, governing how entities should transition their accounting policies for financial instruments. |
| 35.9 | both | scope_transition | This paragraph specifies exemptions from retrospective application during first-time adoption of FRS 102, directly addressing transitional provisions for entities moving to the new framework. |
| 35.10 | both | scope_transition | This paragraph describes exemptions available to entities in their first financial statements under FRS 102, which is a transitional provision regarding the application scope and timing of the standard. |
| 35.11 | both | scope_transition | This paragraph addresses transitional provisions for first-time adoption of FRS 102, specifying how to handle impracticable adjustments and the timing of compliance with disclosure requirements. |
| 35.11A | both | scope_transition | This paragraph establishes transitional provisions permitting entities to continue using exemptions from the date of transition to FRS 102 until derecognition of related assets and liabilities. |
| 35.11B | both | recognition_measurement | This paragraph governs when an entity must reassess and potentially reverse an exemption previously applied at transition, affecting whether prior accounting treatments remain valid in subsequent periods. |
| 35.12 | both | disclosure | The entity must provide an explanation of the transition effects, which is narrative information required to be disclosed to users of the financial statements. |
| 35.12A | pre-PR2024 | disclosure | This paragraph requires an entity to disclose information about reverting from FRS 102 to another framework, thereby imposing a disclosure requirement in the notes to the financial statements. |
| 35.12A | PR2024 | disclosure | This paragraph requires an entity to disclose in its financial statements which transitional exemptions it has elected to use when adopting FRS 102. |
| 35.12B | PR2024 | disclosure | This paragraph requires entities to provide explanatory information in the notes regarding material changes to financial position, specifying whether they resulted from error or accounting policy changes. |
| 35.12C | PR2024 | disclosure | This paragraph requires an entity to disclose information about applying FRS 102 in a previous period but not in the most recent financial statements, specifying what information must be provided in the notes. |
| 35.13 | pre-PR2024 | disclosure | This paragraph requires specific information to be included in an entity's first financial statements under FRS 102, which is a disclosure requirement. |
| 35.14 | both | disclosure | The paragraph requires an entity to provide reconciliations that distinguish error corrections from accounting policy changes, which is information that must be presented in the financial statements or notes. |
| 35.15 | both | disclosure | The paragraph requires an entity to disclose in its first financial statements conforming to FRS 102 the fact that no previous period financial statements were presented. |

## Draft checklist rows (8)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 35.12 | both | Disclose an explanation of how the transition from the previous financial reporting framework to FRS 102 affected reported financial position and financial performance. | conditional | is_first_time_adopter_frs102 == true | is_first_time_adopter_frs102 (NEW) | missing | standard-material | Reviewer should check that the explanation covers both financial position and financial performance and is sufficiently specific to the entity's own transition adjustments; consider whether quantitative reconciliations required by other paragraphs in Section 35 (e.g. 35.13–35.14) are also present. |
| 35.12A | pre-PR2024 | A first-time re-adopter (entity that applied FRS 102 in a previous period but not in its most recent annual financial statements) must disclose the fact of, and reason for, re-adoption and the specific disclosures required by paragraph 35.12A for that re-adoption. | conditional | is_first_time_readopter_frs102 == true | is_first_time_readopter_frs102 (NEW) | missing | standard-material | The paragraph heading indicates disclosures are required but the paragraph text as supplied is incomplete (ends with a colon); reviewer should verify the full list of specific sub-disclosures required by 35.12A in the pre-PR2024 edition and check each has been made. |
| 35.12A | PR2024 | Disclose which transitional exemptions described in paragraph 35.10 have been adopted on transition to FRS 102 (stating explicitly if none were adopted). | conditional | is_first_time_adopter_frs102 == true | is_first_time_adopter_frs102 (NEW) | missing | standard-material | Reviewer should confirm that every exemption applied in practice is listed and that no exemptions are claimed beyond those available in paragraph 35.10; also consider whether first-time readopters (35.2(b)) are within scope of this requirement. |
| 35.12B | PR2024 | Provide an explanation of material changes to the reported financial position that are not presented in the reconciliation required by paragraph 35.13, stating whether each identified change arose as a result of error or of a change in accounting policy. | conditional | is_first_time_adopter_frs102 == true | is_first_time_adopter_frs102 (NEW) | missing | standard-material | Reviewer should assess whether there are material changes to reported financial position on transition that fall outside the paragraph 35.13 reconciliation and therefore trigger this supplementary narrative explanation requirement; the boundary between what is captured in the reconciliation and what requires separate explanation here requires judgement. |
| 35.12C | PR2024 | Disclose all information required by Section 35 for a first-time re-adopter as specified under paragraph 35.12C (cross-reference: see sub-paragraphs 35.12C(a)–(d) for the specific disclosures required) | conditional | is_first_time_readopter_frs102 == true | is_first_time_readopter_frs102 (NEW) | missing | standard-material | Paragraph 35.12C sets out the disclosure heading for re-adopters (entities that previously applied FRS 102 but not in their most recent annual financial statements); the specific sub-paragraph disclosures should be checked against 35.12C(a)–(d) — reviewer should confirm the entity meets the re-adoption definition in paragraph 35.2 rather than being a true first-time adopter under 35.12A. |
| 35.13 | pre-PR2024 | The first financial statements prepared using FRS 102 must include all disclosures required by paragraph 35.12 (i.e. the full set of first-time adoption reconciliations and explanations). | conditional | is_first_time_adopter_frs102 == true | is_first_time_adopter_frs102 (NEW) | missing | standard-material | Paragraph 35.13 has been deleted in the post-PR2024 edition; reviewer should confirm which edition applies and whether any transitional disclosures remain outstanding; the specific sub-requirements of 35.12 (e.g. equity reconciliations, profit or loss reconciliation) are the substantive items to check. |
| 35.14 | both | Where errors made under the previous financial reporting framework are corrected on transition, the reconciliations required by paragraphs 35.13(b) and (c) shall, to the extent practicable, distinguish the correction of those errors from changes in accounting policies. | conditional | is_first_time_adopter_frs102 == true && has_material_prior_period_error == true | is_first_time_adopter_frs102 (NEW), has_material_prior_period_error (NEW) | missing | standard-material | Reviewer should confirm whether any adjustments in the transition reconciliations (35.13(b) and (c)) include error corrections that need to be separately identified from policy changes, and assess whether non-distinction is genuinely impracticable rather than merely inconvenient. |
| 35.15 | both | Disclose the fact that no financial statements were presented for previous periods, in the entity's first financial statements that conform to FRS 102. | conditional | is_first_time_adopter_frs102 == true and has_no_prior_period_financial_statements == true | is_first_time_adopter_frs102 (NEW), has_no_prior_period_financial_statements (NEW) | missing | standard-material | Reviewer should confirm whether the entity genuinely has no prior-period financial statements (e.g. newly incorporated entity or entity that has never previously reported) versus one that simply did not previously apply FRS 102; the disclosure is only required where no financial statements at all were presented for prior periods. |

## Proposed fact registry keys (4, all NEW)

| Key | Used by |
|---|---|
| has_material_prior_period_error | 35.14 |
| has_no_prior_period_financial_statements | 35.15 |
| is_first_time_adopter_frs102 | 35.12, 35.12A, 35.12B, 35.13, 35.14, 35.15 |
| is_first_time_readopter_frs102 | 35.12A, 35.12C |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 8 | 23609 | 1534 | $0.0938 |
| **total** | 8 | 23609 | 1534 | **$0.0938** |
