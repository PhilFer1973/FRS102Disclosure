# Section 8 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 8.1 | both | presentation | This paragraph establishes the structural requirement that entities shall present notes and describes their placement and relationship to primary statements, which is a presentation matter. |
| 8.2 | both | disclosure | This paragraph requires that notes to the financial statements shall contain specified information, establishing a disclosure obligation. |
| 8.5B | PR2024 | disclosure | This paragraph establishes criteria for determining whether accounting policy information must be disclosed in the financial statements, requiring entities to evaluate and present policies related to material transactions and events. |
| 8.5C | PR2024 | other | This paragraph provides guidance on what constitutes useful accounting policy information, establishing a principle to inform policy disclosures without imposing a specific disclosure requirement or measurement rule. |
| 8.5D | PR2024 | disclosure | This paragraph establishes that entities must comply with disclosure requirements specified elsewhere in FRS 102 regardless of materiality judgements about accounting policies. |
| 8.7 | both | disclosure | The paragraph requires entities to disclose in the notes specific information about key assumptions and estimation uncertainties that could materially affect asset and liability carrying amounts. |

## Draft checklist rows (5)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 8.1 | both | Present notes to the financial statements providing narrative descriptions or disaggregations of items in the primary statements and information about items that do not qualify for recognition in those statements. | always | — | — | missing | statutory | This is the overarching requirement to present notes at all; reviewer should confirm that notes are present and that they supplement every primary statement that has been presented, bearing in mind that nearly every other FRS 102 section imposes additional specific note disclosures not governed by this paragraph alone. |
| 8.2 | both | Present notes in a systematic manner, as far as practicable, with each item in the primary statements cross-referenced to related note information | always | — | — | missing | standard-material | 'Systematic manner' and adequacy of cross-referencing involve judgement; reviewer should assess whether the ordering of notes is logical and that primary statement line items are linked to relevant notes. |
| 8.5B | PR2024 | Disclose accounting policy information that is expected to be material, assessed by reference to whether users would need it to understand other material information in the financial statements (including where it relates to material transactions, events or conditions). | always | — | — | missing | standard-material | Paragraph 8.5B sets out a principles-based materiality test for accounting policy disclosures; the reviewer should check whether management has applied genuine judgement about which policies are material rather than including boilerplate or omitting genuinely needed policies. |
| 8.5D | PR2024 | Where accounting policy information is judged immaterial and omitted from the financial statements, still apply all disclosure requirements set out in other sections of FRS 102 that relate to that policy area. | always | — | — | missing | standard-material | Reviewer should check that any decision to omit accounting policy disclosures as immaterial has not been used as a basis to omit other section-specific disclosures (e.g. numerical disclosures, judgements) that remain required regardless of materiality of the policy description itself. |
| 8.7 | both | Disclose in the notes the key assumptions concerning the future and other key sources of estimation uncertainty at the reporting date that have a significant risk of causing a material adjustment to the carrying amounts of assets and liabilities within the next financial year, including details of those assets and liabilities | conditional | has_key_estimation_uncertainties == true | has_key_estimation_uncertainties (NEW) | missing | standard-material | Reviewer should assess whether management has identified all areas of significant estimation uncertainty (e.g. impairment assumptions, useful lives, provisions, fair values) and whether the disclosures are sufficiently specific rather than generic; note that paragraph 8.7 continues with sub-items detailing what 'details' must include, which should be checked separately when the full paragraph is available. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| has_key_estimation_uncertainties | 8.7 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 5 | 8322 | 747 | $0.0362 |
| **total** | 5 | 8322 | 747 | **$0.0362** |
