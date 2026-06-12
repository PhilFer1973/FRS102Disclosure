# Section 22 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 22.1 | both | scope_transition | This paragraph introduces the scope of Section 22 by listing the areas covered, establishing boundaries rather than imposing substantive accounting requirements. |
| 22.2 | both | scope_transition | This paragraph defines the scope boundaries and exceptions for the financial instruments section, establishing which items fall within or outside the section's requirements. |
| 22.3 | both | other | This paragraph provides a definition of equity and explains its composition, offering guidance without imposing a specific disclosure, presentation, recognition, or measurement requirement. |
| 22.3A | both | recognition_measurement | This paragraph establishes the conditions under which a financial instrument is classified and recognized as a financial liability, which is a recognition and measurement determination. |
| 22.4 | both | recognition_measurement | This paragraph establishes criteria for classifying certain financial instruments as equity despite meeting the definition of a liability, which is a recognition and classification principle. |
| 22.5 | both | other | This paragraph provides illustrative examples of how instruments are classified but does not itself impose a standalone requirement; the actual classification requirements are stated elsewhere in the standard. |
| 22.6 | both | recognition_measurement | This paragraph establishes the criteria for determining whether members' shares in co-operative entities should be classified as equity, which is a recognition and classification requirement rather than a disclosure or presentation requirement. |
| 22.7 | both | recognition_measurement | This paragraph establishes the recognition criteria for equity instruments, specifying when an entity should recognize the issuance of shares or other equity instruments. |
| 22.8 | pre-PR2024 | recognition_measurement | This paragraph specifies how equity instruments shall be measured initially (fair value of consideration received, net of transaction costs, potentially adjusted for time value of money). |
| 22.8 | PR2024 | recognition_measurement | This paragraph prescribes how equity instruments shall be measured at initial recognition, including the basis (fair value of consideration net of transaction costs) and adjustments for deferred payment timing. |
| 22.8A | both | recognition_measurement | This paragraph establishes a condition that modifies the recognition treatment of transactions involving the extinguishment of financial liabilities through equity instrument issuance. |
| 22.9 | both | recognition_measurement | This paragraph specifies how transaction costs of equity transactions shall be accounted for (as a deduction from equity) and how related income tax is measured, which are recognition and measurement requirements. |
| 22.10 | both | presentation | This paragraph specifies how increases in equity from share issuance should be presented in the statement of financial position, including the separation of par value from amounts paid in excess thereof. |
| 22.11 | both | recognition_measurement | This paragraph prescribes how to account for and measure equity instruments issued through the exercise of options, rights, warrants and similar instruments by referencing the principles that govern recognition and measurement of share-based payments. |
| 22.12 | pre-PR2024 | recognition_measurement | This paragraph establishes that capitalisation issues, bonus issues, and share splits do not change total equity and requires reclassification of amounts within equity, which governs the accounting treatment and measurement of these transactions. |
| 22.12 | PR2024 | other | This paragraph provides definitions of capitalisation issues and share splits without imposing any recognition, measurement, disclosure or presentation requirements. |
| 22.13 | both | recognition_measurement | This paragraph prescribes the accounting treatment for recognizing and measuring the components of compound financial instruments by requiring allocation of proceeds between liability and equity components based on fair value. |
| 22.14 | both | recognition_measurement | This paragraph establishes a requirement that affects how prior allocations are treated in subsequent periods, which is a measurement/accounting treatment rule rather than a disclosure requirement. |
| 22.15 | both | recognition_measurement | This paragraph establishes how an entity shall measure and account for the liability component of compound financial instruments in subsequent periods under the relevant sections of FRS 102. |
| 22.16 | both | recognition_measurement | This paragraph establishes how treasury shares are measured (at fair value of consideration given) and specifies that no gain or loss is recognised in profit or loss upon their reacquisition or subsequent transactions. |
| 22.17 | both | recognition_measurement | This paragraph establishes the recognition and accounting treatment requirement for how distributions to owners affect the measurement and recognition of equity. |
| 22.18 | both | disclosure | The paragraph explicitly requires entities to disclose the fair value of non-cash assets distributed to owners, which is an informational requirement for the notes or financial statements. |
| 22.19 | pre-PR2024 | recognition_measurement | This paragraph establishes how to measure and recognize changes in controlling interests without loss of control, including the treatment of adjustments to non-controlling interests, the non-recognition of gains/losses, and the non-recognition of changes in asset/liability carrying amounts. |
| 22.19 | PR2024 | other | This is an administrative note indicating content relocation and amendment history rather than imposing an independent requirement. |

## Draft checklist rows (2)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 22.10 | both | Present the increase in equity arising on the issue of shares or other equity instruments in the statement of financial position in accordance with applicable laws (e.g. par/nominal value and share premium presented separately where law requires). | conditional | has_share_capital == true | has_share_capital (NEW) | missing | statutory | This is primarily a company law-driven presentation requirement; reviewer should confirm that share capital (nominal value) and share premium are shown as separate line items on the balance sheet where applicable under the Companies Act 2006 and Schedule 1 to the Regulations, and that the total equity split agrees to the allotted/issued share register. |
| 22.18 | both | Disclose the fair value of any non-cash assets distributed to owners during the reporting period. | conditional | has_non_cash_asset_distribution_to_owners == true AND non_cash_distribution_is_common_control == false | has_non_cash_asset_distribution_to_owners (NEW), non_cash_distribution_is_common_control (NEW) | missing | standard-immaterial-candidate | The exception applies where the non-cash assets are ultimately controlled by the same parties before and after distribution (common control); reviewer should confirm whether any dividend-in-specie or distribution in kind falls within this exception, and assess materiality. |

## Proposed fact registry keys (3, all NEW)

| Key | Used by |
|---|---|
| has_non_cash_asset_distribution_to_owners | 22.18 |
| has_share_capital | 22.10 |
| non_cash_distribution_is_common_control | 22.18 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 2 | 4548 | 345 | $0.0188 |
| **total** | 2 | 4548 | 345 | **$0.0188** |
