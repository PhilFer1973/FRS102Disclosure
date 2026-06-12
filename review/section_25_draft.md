# Section 25 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 25.1 | both | scope_transition | This paragraph defines the scope of the section and specifies what items are included within the definition of borrowing costs, which is a foundational scope-setting statement. |
| 25.2 | both | recognition_measurement | This paragraph establishes whether borrowing costs are capitalised as part of asset cost or expensed, which is a recognition and measurement policy choice governed by the standard. |
| 25.2A | both | recognition_measurement | This paragraph defines the specific borrowing costs that qualify for capitalization, establishing the measurement principle for determining which costs are directly attributable to qualifying assets. |
| 25.2B | both | recognition_measurement | This paragraph specifies the calculation method for determining the amount of borrowing costs that qualify for capitalization, which is a measurement requirement for recognizing capitalized borrowing costs. |
| 25.2C | pre-PR2024 | recognition_measurement | This paragraph specifies the method for determining which borrowing costs qualify for capitalisation and how to measure the eligible amount, which governs recognition and measurement rather than disclosure or presentation. |
| 25.2C | PR2024 | recognition_measurement | This paragraph establishes the methodology for measuring and determining which borrowing costs are eligible for capitalization to a qualifying asset, including the calculation method using a weighted average capitalisation rate. |
| 25.2D | both | recognition_measurement | This paragraph establishes requirements for when and how entities must recognize or measure items, as indicated by the mandatory language 'shall' combined with the prescriptive nature of the requirements that follow. |
| 25.3 | both | disclosure | The paragraph primarily mandates disclosure of total interest expense for financial liabilities not at fair value through profit or loss, with a secondary reference to presentation requirements in another section. |
| 25.3A | both | disclosure | The paragraph requires an entity to disclose information about its capitalization policy, explicitly using the word 'shall disclose' to identify what must be reported in the financial statements. |

## Draft checklist rows (2)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 25.3 | both | When a policy of capitalising borrowing costs is not adopted, no additional disclosure is required beyond those in paragraphs 5.5 and 11.48(b). | conditional | capitalises_borrowing_costs == false | capitalises_borrowing_costs (NEW) | untriggered | standard-immaterial-candidate | This row is essentially a nil-disclosure note; the reviewer should confirm whether the entity has adopted a borrowing cost capitalisation policy and, if not, ensure no spurious Section 25 disclosures have been included; the actual interest expense disclosure obligation falls under paragraph 11.48(b) rather than Section 25. |
| 25.3A | both | Disclose the accounting policy adopted for borrowing costs capitalisation | conditional | capitalises_borrowing_costs == true | capitalises_borrowing_costs (NEW) | missing | standard-material | Paragraph 25.3A sets out specific disclosure requirements for entities that adopt a capitalisation policy; reviewer should confirm the policy note covers the key elements of the capitalisation approach and cross-check with the accounting policies note. |

## Proposed fact registry keys (1, all NEW)

| Key | Used by |
|---|---|
| capitalises_borrowing_costs | 25.3, 25.3A |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 2 | 4818 | 296 | $0.0189 |
| **total** | 2 | 4818 | 296 | **$0.0189** |
