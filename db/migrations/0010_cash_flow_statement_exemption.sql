-- 0010: cash flow statement exemption (reviewer rules, Phil 2026-06-18).
--
-- FRS 102 requires a statement of cash flows (Section 7) UNLESS the entity is
-- exempt by one of two routes:
--   * small entity meeting the CA06 size thresholds  (FRS 102 para 3.1B); or
--   * a qualifying entity included in publicly available group consolidated
--     accounts                                        (FRS 102 para 1.12(b)).
-- FC is a qualifying entity and says so (p18: "qualifying entity ... exempt from
-- preparing a statement of cash flows"), so the always-on Section 7 presentation
-- rules wrongly fired as "missing".
--
-- Gate the always-on Section 7 presentation rules — and the 3.17 "a complete set
-- includes a statement of cash flows" variant — on the entity NOT being exempt.
-- Both facts are already registered. With three-valued logic, an unknown
-- exemption leaves the rule undetermined (a reviewer question), not a finding;
-- and is_qualifying_entity == true alone makes the AND false, so the qualifying-
-- entity route clears the rule even if small-entity status is unknown. A
-- genuinely non-exempt entity that omits the statement is still flagged.

update requirements
set trigger_type      = 'conditional',
    trigger_condition = 'is_small_entity == false AND is_qualifying_entity == false',
    trigger_facts     = array['is_small_entity', 'is_qualifying_entity']
where source = 'FRS102' and trigger_type = 'always' and status = 'active'
  and reference in ('7.3', '7.10', '7.15', '7.17', '7.20');

update requirements
set trigger_type      = 'conditional',
    trigger_condition = 'is_small_entity == false AND is_qualifying_entity == false',
    trigger_facts     = array['is_small_entity', 'is_qualifying_entity']
where source = 'FRS102' and reference = '3.17' and trigger_type = 'always'
  and status = 'active'
  and requirement_text ilike '%statement of cash flows%';
