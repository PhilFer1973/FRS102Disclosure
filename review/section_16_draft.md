# Section 16 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 16.1 | pre-PR2024 | scope_transition | This paragraph defines the scope of Section 16 by specifying which assets are subject to the section's requirements, establishing the boundaries of applicability. |
| 16.1 | PR2024 | scope_transition | This paragraph establishes the scope of the section by identifying which assets (investment property) the section applies to. |
| 16.1A | pre-PR2024 | scope_transition | This paragraph defines the scope boundaries of the section by specifying which transactions are excluded from its application. |
| 16.1A | PR2024 | scope_transition | This paragraph defines the scope of Section 16 by specifying which investment property transactions are excluded from its requirements, establishing a boundary condition for the section's applicability. |
| 16.2 | both | other | A deleted paragraph contains no active requirement and therefore falls into the 'other' category as it is purely a structural notation with no substantive guidance or requirement. |
| 16.2A | PR2024 | scope_transition | This paragraph clarifies the boundary between Section 16 (Investment Property) and Section 19 (Business Combinations), establishing scope rules for determining which accounting framework applies to specific transactions. |
| 16.3 | pre-PR2024 | recognition_measurement | This paragraph establishes the conditions and requirements for how a leasehold property interest must be classified and accounted for as investment property, which determines its recognition and measurement approach. |
| 16.3 | PR2024 | other | A deleted paragraph contains no active requirement or guidance to classify. |
| 16.3A | both | recognition_measurement | This paragraph establishes the classification and accounting treatment for social housing property, determining that it must be classified as property, plant and equipment rather than investment property and therefore measured under Section 17 rather than investment property rules. |
| 16.4 | pre-PR2024 | recognition_measurement | This paragraph specifies conditions for recognizing and classifying mixed-use property between investment property and PPE based on separability and fair value measurability, which governs how items are recognized and measured. |
| 16.4 | PR2024 | recognition_measurement | This paragraph establishes criteria for whether mixed-use property should be separated and specifies how it must be accounted for (as investment property, property, plant and equipment, or right-of-use asset) based on whether components can be sold/leased separately and whether fair value can be reliably measured. |
| 16.4A | pre-PR2024 | recognition_measurement | This paragraph specifies how an entity shall account for investment property rented to another group entity, which is a recognition and measurement requirement governing the treatment of such transactions. |
| 16.4A | PR2024 | recognition_measurement | This paragraph establishes an accounting policy choice for how to measure investment property rented to group entities, which is a fundamental recognition and measurement decision. |
| 16.4B | both | scope_transition | This paragraph defines the scope and application conditions for when paragraph 16.4A applies, specifically limiting it to only the portion of property rented to another group entity. |
| 16.5 | both | recognition_measurement | This paragraph establishes how investment properties shall be measured at initial recognition, including the components and calculation methods for determining cost. |
| 16.6 | pre-PR2024 | recognition_measurement | This paragraph prescribes how to recognise and measure the initial cost of a leasehold investment property, including the asset and liability amounts to be recorded. |
| 16.6 | PR2024 | recognition_measurement | This paragraph specifies how investment properties held by lessees are initially measured (at cost), which is a measurement requirement. |
| 16.7 | pre-PR2024 | recognition_measurement | This paragraph establishes the measurement basis (fair value) for investment properties and prescribes where changes in fair value are recognized (profit or loss). |
| 16.7 | PR2024 | recognition_measurement | This paragraph establishes the measurement basis (fair value at each reporting date) for investment properties and specifies that fair value changes are recognized in profit or loss, which are core recognition and measurement requirements. |
| 16.8 | both | other | This paragraph is marked as deleted and contains no operative requirement or guidance. |
| 16.9 | pre-PR2024 | recognition_measurement | This paragraph establishes the requirements for when a transfer of a property to or from investment property shall occur, which is a recognition/classification matter affecting the timing of when property is recognized as investment property. |
| 16.9 | PR2024 | recognition_measurement | This paragraph specifies when an entity shall transfer property to or from investment property, governing the recognition and timing of reclassification between asset categories. |
| 16.9A | pre-PR2024 | recognition_measurement | This paragraph specifies how to measure property when it transitions from one classification to another (investment property to owner-occupied/inventory), establishing the deemed cost as fair value at the transition date. |
| 16.9A | PR2024 | recognition_measurement | This paragraph establishes how to measure an asset when it transitions from investment property to another asset category, specifying that fair value at the date of change in use becomes the deemed cost for subsequent accounting. |
| 16.9B | pre-PR2024 | recognition_measurement | This paragraph specifies how to measure and recognize the change in an owner-occupied property becoming an investment property, including treatment of the difference between carrying amount and fair value at the transition date. |
| 16.9B | PR2024 | recognition_measurement | This paragraph governs the measurement treatment and accounting method to apply when an owner-occupied property transitions to an investment property, specifically addressing how to account for the difference between carrying amount and fair value at the date of change in use. |
| 16.9C | both | recognition_measurement | This paragraph specifies how to measure the transferred property (fair value) and requires recognition of the measurement difference in profit or loss upon transfer. |
| 16.10 | both | disclosure | The paragraph explicitly requires an entity to disclose specific information in accordance with the directive 'shall disclose the following' |
| 16.11 | both | disclosure | This paragraph requires an entity to provide disclosures about leases as specified in Section 20, which is a direct disclosure requirement. |

## Draft checklist rows (2)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 16.10 | both | Disclose all information required by paragraph 16.10 in respect of investment property (note: paragraph 16.10 sets out the heading but the specific sub-items are listed within it; ensure all sub-disclosures are present). | conditional | has_investment_property == true | has_investment_property (NEW) | missing | standard-material | The paragraph text provided is incomplete (truncated at 'An entity shall disclose the following:') — the reviewer must inspect the full list of sub-items in paragraph 16.10 to verify each individual disclosure requirement is met; this row should be replaced with granular rows once the full text is available. |
| 16.11 | both | Provide all relevant Section 20 lease disclosures for leases that the entity has entered into. | conditional | is_lessee == true | is_lessee (NEW) | missing | standard-material | Paragraph 16.11 cross-refers entirely to Section 20 for the substance of the disclosures; reviewer should confirm that Section 20 rows are separately checked and that 'leases entered into' covers both lessee and any lessor arrangements arising in the context of investment property (e.g. operating leases of investment property). |

## Proposed fact registry keys (2, all NEW)

| Key | Used by |
|---|---|
| has_investment_property | 16.10 |
| is_lessee | 16.11 |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 2 | 3958 | 329 | $0.0168 |
| **total** | 2 | 3958 | 329 | **$0.0168** |
