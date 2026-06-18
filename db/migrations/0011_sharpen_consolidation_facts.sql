-- 0011: sharpen consolidation / qualifying-entity fact definitions (Phil 2026).
--
-- 9.23 ("disclosures in consolidated financial statements") is already correctly
-- conditional on prepares_consolidated_financial_statements == true. It fired on
-- FC because the fact was MIS-RESOLVED: FC's notes mention the parent's
-- consolidated accounts ("included in the consolidated financial statements of
-- ..."), and the resolver read that as FC preparing its own. The fix is at the
-- fact layer, not the rule: give the resolver a definition that distinguishes
-- "prepares its own group accounts" from "is included in a parent's".
--
-- The same precision underpins the cash-flow exemption gate (0010), which keys
-- on is_qualifying_entity — so that fact's definition is sharpened too.

update fact_registry
set description =
    'TRUE only if the company itself prepares consolidated (group) financial '
    'statements as a parent consolidating its subsidiaries. FALSE if the company '
    'is merely INCLUDED IN a parent''s consolidated accounts, or takes a '
    'consolidation or qualifying-entity exemption from preparing them.'
where key = 'prepares_consolidated_financial_statements';

update fact_registry
set description =
    'TRUE if the company is a qualifying entity: a member of a group where a '
    'parent prepares publicly available consolidated accounts that include this '
    'company (FRS 102 glossary). Typically stated where the company takes '
    'disclosure or cash-flow-statement exemptions "as a qualifying entity".'
where key = 'is_qualifying_entity';
