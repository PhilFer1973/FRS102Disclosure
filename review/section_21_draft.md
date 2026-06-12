# Section 21 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 21.1 | both | scope_transition | This paragraph defines the scope of the provisions section and specifies which matters fall within and outside its application, establishing boundaries for the section's coverage. |
| 21.1A | both | scope_transition | This paragraph defines the scope of the section by specifying which financial guarantee contracts are subject to the requirements, which is a scope-delimiting provision. |
| 21.1B | both | scope_transition | This paragraph defines the scope of the section by specifying what is excluded from its application. |
| 21.2 | both | scope_transition | This is a cross-reference indicating content relocation within the standard, which is a structural or transitional matter rather than imposing a substantive requirement. |
| 21.3 | both | scope_transition | This paragraph defines the scope of the provisions section by clarifying what items are excluded from its coverage (depreciation, impairment, uncollectible receivables) because they are asset adjustments rather than liability recognition. |
| 21.4 | both | recognition_measurement | This paragraph establishes the conditions and criteria for when a provision must be recognized in the financial statements, which is a recognition requirement. |
| 21.4A | PR2024 | other | This paragraph provides a specific definition of 'liability' for the purposes of Section 21 that differs from the general definition elsewhere in FRS 102, serving as a clarification of scope rather than imposing a disclosure, presentation, or recognition requirement. |
| 21.5 | both | recognition_measurement | This paragraph specifies when a provision shall be recognised as a liability and how the related amount shall be treated (as an expense or as part of asset cost), which are core recognition and measurement requirements. |
| 21.6 | both | recognition_measurement | This paragraph explains the conditions under which an obligation exists and must be recognized, specifically distinguishing between present obligations and future obligations that do not satisfy the recognition criteria for provisions. |
| 21.7 | both | recognition_measurement | This paragraph specifies how provisions are measured (at best estimate of settlement amount), which is a measurement requirement for recognition of liabilities. |
| 21.8 | both | recognition_measurement | This paragraph prescribes how provisions should be measured by specifying that expected gains from asset disposal must be excluded from the measurement calculation. |
| 21.9 | both | recognition_measurement | The paragraph establishes the conditions for recognising reimbursement assets ('virtually certain' criterion) and how to measure them (not exceeding the provision amount), which are recognition and measurement requirements. |
| 21.10 | both | recognition_measurement | This paragraph prescribes how expenditures are to be charged against a provision, which is a measurement and accounting treatment requirement for provisions. |
| 21.11 | both | recognition_measurement | This paragraph specifies when and how provisions are measured and recognised, including the timing of adjustments and the treatment of discount unwinding in profit or loss. |
| 21.11A | both | recognition_measurement | This paragraph establishes when an onerous contract obligation must be recognised and how it shall be measured as a provision. |
| 21.11B | both | recognition_measurement | This paragraph establishes a prohibition on recognising provisions for future operating losses, which is a recognition requirement determining when provision liabilities shall not be recognised. |
| 21.11C | both | recognition_measurement | This paragraph establishes the criteria for when a restructuring obligation is recognised as a constructive obligation, which is a recognition condition. |
| 21.11D | both | recognition_measurement | This paragraph specifies the condition under which a restructuring provision must be recognised (legal or constructive obligation at reporting date), which is a recognition criterion. |
| 21.12 | pre-PR2024 | recognition_measurement | This paragraph establishes that contingent liabilities shall not be recognised as liabilities (with a specified exception), which is a recognition requirement that governs whether items are recorded in the financial statements. |
| 21.12 | PR2024 | disclosure | The paragraph requires disclosure of contingent liabilities in the notes unless the possibility of outflow is remote, which is a disclosure requirement that governs what information must be presented. |
| 21.13 | both | recognition_measurement | The paragraph establishes the criteria for when contingent assets should be recognised as assets versus when they must be disclosed, governing the recognition decision based on probability of economic inflow. |
| 21.14 | pre-PR2024 | disclosure | The paragraph explicitly requires an entity to disclose specific information for each class of provision, which is a disclosure requirement in the financial statements. |
| 21.16 | pre-PR2024 | disclosure | The paragraph requires entities to disclose descriptive information about contingent assets and their estimated financial effects in the notes to the financial statements. |
| 21.17 | pre-PR2024 | disclosure | The paragraph establishes an exception to disclosure requirements for provisions and contingent items, requiring entities to disclose certain minimum information even when full disclosure would prejudice their position in a dispute. |
| 21.17A | pre-PR2024 | disclosure | The paragraph explicitly requires entities to disclose the nature and business purpose of financial guarantee contracts issued, along with reference to additional required disclosures in paragraphs 21.14 and 21.15. |

## Draft checklist rows (9)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 21.12 | PR2024 | Do not recognise a contingent liability as a liability (except for contingent liabilities assumed in a business combination per paragraphs 19.15F and 19.24A). | conditional | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies == true | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies (NEW) | both | standard-material | Reviewer should check that no contingent liability has been recognised on the face of the balance sheet unless it arose from a business combination; the business combination exception interacts with Section 19 and should be verified if has_acquisition_of_subsidiary_or_business_unit is also true. |
| 21.12 | PR2024 | Disclose a contingent liability (as required by paragraph 21.15) unless the possibility of an outflow of resources is remote. | conditional | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies == true | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies (NEW) | missing | standard-material | Reviewer must assess whether management has correctly classified the outflow probability as remote to justify omitting disclosure; the remote threshold is a judgement and should be challenged if evidence of a more-than-remote possibility exists. |
| 21.12 | PR2024 | Where the entity is jointly and severally liable for an obligation, treat the portion expected to be met by other parties as a contingent liability (i.e. do not recognise that portion as a liability, and apply the disclosure requirements accordingly). | conditional | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies == true | has_off_balance_sheet_financial_commitments_guarantees_or_contingencies (NEW) | both | standard-material | Reviewer should confirm that where joint-and-several obligations exist the entity has split recognised liability (its own share) from the contingent liability (other parties' expected share) and has disclosed the contingent element unless remote. |
| 21.14 | pre-PR2024 | For each class of provision, disclose: the carrying amount at the beginning and end of the period; additional provisions made in the period, including increases to existing provisions; amounts used (i.e. incurred and charged against the provision) during the period; unused amounts reversed during the period; and the unwinding of any discount or change in the discount rate. | conditional | has_provisions == true | has_provisions (NEW) | missing | standard-material | Paragraph 21.14 was deleted in the PR2024 edition; confirm the pre-PR2024 edition applies. Reviewer should check that all classes of provision are identified and that each class carries its own roll-forward disclosure rather than being aggregated. |
| 21.16 | pre-PR2024 | Disclose a description of the nature of any contingent assets at the end of the reporting period where an inflow of economic benefits is probable but not virtually certain. | conditional | has_probable_contingent_assets == true | has_probable_contingent_assets (NEW) | missing | standard-material | Reviewer should confirm management has assessed whether any probable inflows exist and that none have been prematurely recognised as assets (which would be a separate error under Section 21). |
| 21.16 | pre-PR2024 | Where practicable, disclose an estimate of the financial effect of contingent assets measured using the principles in paragraphs 21.7 to 21.11; if impracticable to estimate, state that fact. | conditional | has_probable_contingent_assets == true | has_probable_contingent_assets (NEW) | missing | standard-material | Reviewer should assess whether management has genuinely considered whether an estimate is practicable and, if not, whether the impracticability statement is explicitly included in the notes. |
| 21.17 | pre-PR2024 | When omitting detailed provision/contingent liability/contingent asset information on grounds of serious prejudice to a dispute, disclose at minimum: the general nature of the dispute, the fact that information has been omitted, and the reason why it has been omitted. | conditional | has_provisions == true or has_off_balance_sheet_financial_commitments_guarantees_or_contingencies == true or has_probable_contingent_assets == true | has_provisions (NEW), has_off_balance_sheet_financial_commitments_guarantees_or_contingencies (NEW), has_probable_contingent_assets (NEW) | missing | standard-material | This paragraph (21.17) has been deleted in the post-PR2024 edition; reviewer should confirm the reporting edition and assess whether the entity has actually invoked the serious-prejudice exemption, and if so verify that the minimum disclosures (general nature, fact of omission, reason) are present — noting the standard describes this as applicable only in 'extremely rare cases'. |
| 21.17A | pre-PR2024 | Disclose the nature and business purpose of financial guarantee contracts issued by the entity. | conditional | has_issued_financial_guarantee_contracts == true | has_issued_financial_guarantee_contracts (NEW) | missing | standard-material | Reviewer should confirm whether contracts described as guarantees meet the FRS 102 definition of financial guarantee contracts and are not captured under contingent liabilities or financial instruments disclosures instead. |
| 21.17A | pre-PR2024 | Provide the disclosures required by paragraphs 21.14 and 21.15 where applicable in relation to financial guarantee contracts issued. | conditional | has_issued_financial_guarantee_contracts == true | has_issued_financial_guarantee_contracts (NEW) | missing | standard-material | Reviewer should assess whether any financial guarantee contract meets the 21.14/21.15 threshold (i.e. triggers contingent liability or provision recognition/disclosure) and confirm those cross-referenced disclosures are present where applicable; note this paragraph is deleted in PR2024 edition. |

## Proposed fact registry keys (4, all NEW)

| Key | Used by |
|---|---|
| has_issued_financial_guarantee_contracts | 21.17A |
| has_off_balance_sheet_financial_commitments_guarantees_or_contingencies | 21.12, 21.17 |
| has_probable_contingent_assets | 21.16, 21.17 |
| has_provisions | 21.14, 21.17 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 5 | 16013 | 1512 | $0.0707 |
| **total** | 5 | 16013 | 1512 | **$0.0707** |
