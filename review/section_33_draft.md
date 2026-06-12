# Section 33 — draft checklist rows (DRAFT)

Status of every row below: **draft**. Nothing is active until Phil reviews.
All trigger fact keys are **NEW** proposals (fact registry is empty).

## Classification (para_type)

| Reference | Edition | para_type | Rationale |
|---|---|---|---|
| 33.1 | both | disclosure | This paragraph establishes the requirement to include disclosures in financial statements about related parties and their transactions, which is a disclosure requirement rather than a recognition, measurement, or presentation rule. |
| 33.1A | pre-PR2024 | disclosure | This paragraph specifies a condition under which certain transaction disclosures required by the section may be omitted, thereby directly modifying disclosure requirements. |
| 33.2 | both | other | This paragraph provides a definition of 'related party' without imposing any recognition, measurement, disclosure or presentation requirements. |
| 33.3 | both | recognition_measurement | This paragraph prescribes how entities must evaluate related party relationships (by substance rather than legal form), establishing the basis for determining whether recognition or measurement of related party transactions should apply. |
| 33.4 | both | other | This paragraph provides a definition of exclusions from the related parties concept, establishing what entities are not considered related parties, which is definitional guidance rather than imposing a specific disclosure, presentation, or recognition requirement. |
| 33.4A | both | other | This paragraph provides clarifying guidance on the definition of related parties by explaining how subsidiaries of associates and joint ventures are treated, with an illustrative example, but does not impose a standalone disclosure, presentation, or recognition requirement. |
| 33.6 | both | other | This paragraph provides definitions of key management personnel and compensation without imposing any recognition, measurement, presentation, or disclosure requirements. |
| 33.7 | both | disclosure | The paragraph explicitly requires an entity to disclose key management personnel compensation in total, imposing a disclosure requirement for information to be presented in the financial statements. |
| 33.7A | both | disclosure | This paragraph establishes a conditional exemption from disclosing key management personnel compensation when directors' remuneration is already legally required and the two groups are identical, thus modifying disclosure obligations. |
| 33.8 | both | other | This paragraph provides definitions and examples of related party transactions without imposing any disclosure, presentation, or recognition requirement. |
| 33.10 | both | disclosure | This paragraph requires an entity to provide specific disclosures in a particular manner (separately by category), which is a disclosure requirement that governs how information must be presented in the notes. |
| 33.11 | pre-PR2024 | disclosure | This paragraph specifies an exemption from disclosure requirements, which is itself a disclosure-related provision governing what information must or need not be provided. |
| 33.12 | both | disclosure | This paragraph requires specific transactions with related parties to be disclosed in the financial statements, establishing an informational requirement rather than affecting recognition, measurement, or presentation format. |
| 33.13 | both | disclosure | This paragraph requires entities to substantiate claims about arm's length pricing in related party transaction disclosures, establishing a requirement for information to be provided in the notes. |

## Draft checklist rows (8)

| Reference | Edition | Requirement | Trigger type | Trigger condition | Trigger facts | Direction | Severity | Review notes |
|---|---|---|---|---|---|---|---|---|
| 33.1 | both | Include in the financial statements the disclosures necessary to draw attention to the possibility that the entity's financial position and profit or loss have been affected by the existence of related parties and by transactions and outstanding balances with such parties. | always | — | — | missing | standard-material | This is an overarching objective requirement for Section 33; the reviewer should confirm that specific disclosures in subsequent paragraphs (33.2 onwards) are sufficient to satisfy this objective, and should also check against Companies Act related-party disclosure requirements which may impose additional statutory obligations. |
| 33.1A | pre-PR2024 | Omit related party disclosures for intra-group transactions only where every subsidiary party to the transaction is wholly owned by a member of the group. | conditional | is_part_of_group == true AND has_intragroup_related_party_transactions == true | is_part_of_group (NEW), has_intragroup_related_party_transactions (NEW) | both | standard-material | Reviewer must confirm that any subsidiary party to the intra-group transaction is wholly owned; if a partially-owned subsidiary is involved the exemption does not apply and full related party disclosures are required. |
| 33.7 | both | Disclose total key management personnel compensation. | always | — | — | missing | standard-material | Consider whether the entity has identified all key management personnel correctly (including directors) and whether compensation includes all components such as short-term benefits, post-employment benefits, and share-based payments; interactions with Companies Act directors' remuneration disclosures should be checked to avoid gaps. |
| 33.7A | both | Disclose directors' remuneration in accordance with the applicable legal or regulatory requirement (in lieu of paragraph 33.7 key management personnel compensation disclosures) when the entity is legally or regulatorily required to disclose directors' remuneration and the key management personnel and directors are the same persons. | conditional | has_legal_or_regulatory_directors_remuneration_requirement == true AND kmp_and_directors_are_same == true | has_legal_or_regulatory_directors_remuneration_requirement (NEW), kmp_and_directors_are_same (NEW) | missing | statutory | Reviewer should confirm that the entity actually meets both conditions (a legal/regulatory directors' remuneration obligation exists and KMP = directors) before accepting use of this exemption from paragraph 33.7; if either condition fails, full paragraph 33.7 disclosures are required instead. |
| 33.10 | both | Disclose the related party information required by paragraph 33.9 separately for each of the relevant categories of related party (as specified in paragraph 33.10) | always | — | — | missing | standard-material | Paragraph 33.10 lists the specific categories (e.g. parent, subsidiaries, associates, key management, etc.) but does not itself set out what must be disclosed — the reviewer should confirm that 33.9 disclosures are disaggregated by each category for which transactions or balances exist, not aggregated across categories. |
| 33.11 | pre-PR2024 | No disclosure requirement to extract: paragraph 33.11 sets out exemptions from the paragraph 33.9 disclosure requirements and does not itself impose any positive disclosure obligation. | always | — | — | missing | standard-material | This paragraph is deleted in the PR2024 edition; in pre-PR2024 it contains only exemption conditions (e.g. qualifying entity, state-controlled entities) that remove the paragraph 33.9 disclosure duty — reviewer should confirm whether any applicable exemption is being claimed and whether the entity meets the relevant conditions, as no standalone disclosure obligation arises from this paragraph itself. |
| 33.12 | both | Disclose transactions with related parties that fall within the types listed as examples in paragraph 33.12 (including, but not limited to: purchases or sales of goods, property or other assets; rendering or receiving of services; leases; guarantees; settlements of liabilities on behalf of the entity or by the entity on behalf of another party; and participation in arrangements such as partnerships). | conditional | has_related_party_transactions == true | has_related_party_transactions (NEW) | missing | standard-material | Paragraph 33.12 provides examples rather than an exhaustive list; the reviewer should confirm that all material related party transaction types are captured and cross-check against the broader disclosure requirements in paragraphs 33.13–33.14, which prescribe the actual content of disclosures. |
| 33.13 | both | Do not state that related party transactions were made on terms equivalent to those that prevail in arm's length transactions unless such terms can be substantiated. | conditional | has_related_party_transactions == true | has_related_party_transactions (NEW) | untriggered | standard-material | Reviewer should check whether any arm's length assertion made in the accounts is supported by sufficient evidence; this is a prohibition rather than a positive disclosure requirement, so the 'untriggered' direction flags the assertion when it cannot be substantiated. |

## Proposed fact registry keys (5, all NEW)

| Key | Used by |
|---|---|
| has_intragroup_related_party_transactions | 33.1A |
| has_legal_or_regulatory_directors_remuneration_requirement | 33.7A |
| has_related_party_transactions | 33.12, 33.13 |
| is_part_of_group | 33.1A |
| kmp_and_directors_are_same | 33.7A |

## Token usage and cost

| Model | Calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|
| claude-sonnet-4-6 | 8 | 21449 | 1332 | $0.0843 |
| **total** | 8 | 21449 | 1332 | **$0.0843** |
