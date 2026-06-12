# Section 15 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 15.1 | both | scope_transition | This paragraph defines the scope of the section by specifying which entities or transactions the requirements apply to. |
| 15.2 | both | other | This paragraph provides the definition of joint control, which is a key term used throughout the standard but does not itself impose any recognition, measurement, presentation or disclosure requirement. |
| 15.3 | both | other | This paragraph provides definitions of joint ventures and their forms without imposing specific recognition, measurement, disclosure, or presentation requirements. |
| 15.4 | both | other | This paragraph provides descriptive guidance about the nature and operational structure of certain joint ventures without imposing specific recognition, measurement, disclosure, or presentation requirements. |
| 15.5 | both | recognition_measurement | This paragraph establishes what items a venturer must recognise in its financial statements regarding jointly controlled operations, which is a core recognition requirement. |
| 15.6 | both | other | This paragraph provides descriptive guidance about the nature and characteristics of joint ventures without imposing any specific recognition, measurement, disclosure or presentation requirement. |
| 15.7 | both | recognition_measurement | This paragraph establishes what a venturer must recognise in its financial statements regarding jointly controlled assets, which is a recognition requirement governing how interests in joint arrangements are recorded. |
| 15.8 | both | other | This paragraph provides a definition of a jointly controlled entity without imposing any specific recognition, measurement, presentation, or disclosure requirements. |
| 15.9 | both | recognition_measurement | This paragraph specifies how a venturer shall account for its interests in jointly controlled entities, which is a recognition and measurement requirement. |
| 15.9A | both | recognition_measurement | This paragraph specifies the accounting method (equity method) that must be used to account for investments in jointly controlled entities in consolidated financial statements. |
| 15.9B | both | recognition_measurement | This paragraph establishes how investments in jointly controlled entities must be measured (fair value) and how changes in that measurement are recognised (in profit or loss), which are core recognition and measurement requirements. |
| 15.10 | both | recognition_measurement | This paragraph specifies how investments in jointly controlled entities shall be measured (cost model less impairment), which is a measurement requirement. |
| 15.11 | both | recognition_measurement | This paragraph specifies how distributions from jointly controlled entities should be recognized as income, establishing the measurement treatment regardless of the timing of accumulated profits. |
| 15.12 | both | other | This paragraph has been deleted and therefore contains no substantive requirement or guidance. |
| 15.13 | pre-PR2024 | recognition_measurement | This paragraph specifies how investments in jointly controlled entities shall be measured (by the equity method), which is a measurement requirement rather than a disclosure or presentation requirement. |
| 15.13 | PR2024 | recognition_measurement | This paragraph prescribes the measurement method (equity method) that must be applied to investments in jointly controlled entities. |
| 15.14 | both | recognition_measurement | This paragraph specifies the required measurement basis for initial recognition of investments in jointly controlled entities, establishing when and how they must be measured at transaction price. |
| 15.15 | pre-PR2024 | recognition_measurement | This paragraph establishes how investments in jointly controlled entities shall be measured (fair value) and where changes in fair value shall be recognized in the financial statements. |
| 15.15 | PR2024 | recognition_measurement | This paragraph establishes how investments in jointly controlled entities must be measured (at fair value) and where changes in fair value are recognized (OCI or P&L), which are core recognition and measurement requirements. |
| 15.15A | both | recognition_measurement | The paragraph specifies how and when dividends from jointly controlled entities shall be recognized, determining that distributions are recognized as income regardless of their source period. |
| 15.16 | both | recognition_measurement | This paragraph establishes when and how much of a gain or loss should be recognised when a venturer contributes or sells assets to a joint venture, governing both recognition timing and measurement of the transaction's accounting effect. |
| 15.17 | both | recognition_measurement | This paragraph specifies when venturer profits and losses from joint venture transactions are recognised, establishing the timing and conditions for recognition rather than disclosure requirements. |
| 15.18 | both | recognition_measurement | This paragraph establishes the accounting treatment and measurement basis for investments in joint ventures depending on the level of control or influence held by the investor. |
| 15.19 | pre-PR2024 | disclosure | This paragraph explicitly requires information to be disclosed in the financial statements, setting out what items must be reported in the notes or statements. |
| 15.19 | PR2024 | disclosure | The paragraph explicitly requires the venturer's financial statements to disclose specific information about joint ventures, which is a disclosure requirement. |
| 15.20 | pre-PR2024 | disclosure | The paragraph requires venturers to separately disclose their share of profit/loss and discontinued operations of jointly controlled entities, which is a presentation and narrative requirement within the financial statements. |
| 15.20 | PR2024 | disclosure | The paragraph explicitly requires separate disclosure of the venturer's share of profit/loss and discontinued operations of jointly controlled entities in the notes to the financial statements. |
| 15.21 | both | disclosure | The paragraph requires venturers to make specific disclosures about jointly controlled entities by cross-referencing the disclosure requirements in paragraphs 11.43 and 11.44. |
| 15.21A | both | disclosure | The paragraph requires disclosure of summarised financial information about investments in jointly controlled entities and the effects of equity method accounting in individual financial statements. |

## Draft checklist rows (8)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 15.19 | pre-PR2024 | Disclose the information required by paragraph 15.19 in the financial statements (note: the specific sub-items to be disclosed are set out in the sub-paragraphs of 15.19 which should be checked separately). | always | — | — | missing | standard-material | Paragraph 15.19 is a header requirement amended under pre-PR2024; the actual disclosure items are in its sub-paragraphs — reviewer should ensure each sub-paragraph is checked individually and that any amendments in the edition diff are captured in those rows. |
| 15.19 | PR2024 | Disclose in the financial statements of the venturer the aggregate amounts of the following items relating to its interests in jointly controlled entities: (a) assets (b) liabilities (c) income and (d) expenses | conditional | has_interests_in_jointly_controlled_entities == true | has_interests_in_jointly_controlled_entities (NEW) | missing | standard-material | Paragraph 15.19 was amended in PR2024; reviewer should confirm the full list of required disclosure items matches the revised paragraph text, and check whether the venturer uses proportionate consolidation or equity method as this affects how aggregates are presented. |
| 15.20 | pre-PR2024 | Disclose separately the venturer's share of the profit or loss of jointly controlled entities accounted for under the equity method. | conditional | has_interests_in_jointly_controlled_entities == true and uses_equity_method_for_associates == true | has_interests_in_jointly_controlled_entities (NEW), uses_equity_method_for_associates (NEW) | missing | standard-material | FRS 102 uses 'equity method' as defined in Section 14 applied by analogy; reviewer should confirm the entity has actually applied equity method (not cost or fair value) to jointly controlled entities and that the share of profit or loss is shown separately in the income statement or notes. |
| 15.20 | pre-PR2024 | Disclose separately the venturer's share of any discontinued operations of jointly controlled entities accounted for under the equity method. | conditional | has_interests_in_jointly_controlled_entities == true and uses_equity_method_for_associates == true and has_discontinued_operations_prior_period == true | has_interests_in_jointly_controlled_entities (NEW), uses_equity_method_for_associates (NEW), has_discontinued_operations_prior_period (NEW) | both | standard-material | The trigger fact 'has_discontinued_operations_prior_period' is used as a proxy for discontinued operations existing in the JCE; reviewer should assess whether any JCE has discontinued operations in the current or comparative period and ensure the disclosure is present only when relevant. |
| 15.20 | PR2024 | Disclose separately the venturer's share of the profit or loss of jointly controlled entities accounted for using the equity method. | conditional | has_interests_in_jointly_controlled_entities == true | has_interests_in_jointly_controlled_entities (NEW) | missing | standard-material | Confirm that the equity-method share of profit or loss is presented as a separate line item (not aggregated with other income or expense lines); also check whether the JCE itself has discontinued operations requiring further disaggregation. |
| 15.20 | PR2024 | Disclose separately the venturer's share of any discontinued operations of jointly controlled entities accounted for using the equity method. | conditional | has_interests_in_jointly_controlled_entities == true | has_interests_in_jointly_controlled_entities (NEW) | both | standard-material | Direction is 'both': flag if the entity has JCEs with discontinued operations but omits the disclosure, and also flag if a discontinued-operations share is shown when no such operations exist in any JCE; reviewer should obtain information from the JCE to verify the existence or absence of discontinued operations. |
| 15.21 | both | For jointly controlled entities accounted for using the fair value through profit or loss method (paragraph 15.9(c)), disclose the information required by paragraphs 11.43 and 11.44 (financial instrument disclosures). | conditional | has_interests_in_jointly_controlled_entities == true and investments_in_subsidiaries_associates_jces_at_fvtpl == true | has_interests_in_jointly_controlled_entities (NEW), investments_in_subsidiaries_associates_jces_at_fvtpl (NEW) | missing | standard-material | Reviewer should confirm the entity is accounting for its jointly controlled entities under paragraph 15.9(c) (fair value model) rather than another permitted method, and verify that all disclosures required by paragraphs 11.43 and 11.44 are present; the content of those disclosures (e.g. fair value hierarchy, movements) should be cross-checked against Section 11. |
| 15.21A | both | The individual financial statements of a venturer that is not a parent shall disclose summarised financial information about investments in jointly controlled entities, together with the effect of including those investments as if accounted for using the equity method. | conditional | has_interests_in_jointly_controlled_entities == true and is_individual_financial_statements == true and is_parent_entity == false and uses_consolidation_exemption == false | has_interests_in_jointly_controlled_entities (NEW), is_individual_financial_statements (NEW), is_parent_entity (NEW), uses_consolidation_exemption (NEW) | missing | standard-material | Reviewer should confirm whether the entity qualifies for the consolidation exemption (or would qualify if it had subsidiaries), as such entities are explicitly exempt from this requirement; also check that 'not a parent' status and individual financial statements presentation are correctly established. |

## Proposed fact registry keys (7, all NEW)

| Key | Used by |
|---|---|
| has_discontinued_operations_prior_period | 15.20 |
| has_interests_in_jointly_controlled_entities | 15.19, 15.20, 15.21, 15.21A |
| investments_in_subsidiaries_associates_jces_at_fvtpl | 15.21 |
| is_individual_financial_statements | 15.21A |
| is_parent_entity | 15.21A |
| uses_consolidation_exemption | 15.21A |
| uses_equity_method_for_associates | 15.20 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 6 | 11956 | 1459 | $0.0578 |
| **total** | 6 | 11956 | 1459 | **$0.0578** |
