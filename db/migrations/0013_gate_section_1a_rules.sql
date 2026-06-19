-- 0013: gate Section 1A (small-entities regime) rules on applies_section_1A.
--
-- FRS 102 Section 1A disclosures apply ONLY to a small entity that prepares its
-- accounts under Section 1A. 86 of the 90 active 1A* rules were ungated, so the
-- small-company disclosures fired and flooded the question queue on medium-sized
-- entities (validation on FC and Teneo). Gate every active 1A* rule on
-- applies_section_1A == true so a non-small entity clears them all at once.

-- ensure the gating fact is registered (activation guard requires it)
insert into fact_registry (key, description, value_type)
values ('applies_section_1A',
        'TRUE if the entity is a small entity preparing its financial statements '
        'under the small entities regime in FRS 102 Section 1A.', 'boolean')
on conflict (key) do nothing;

-- always-on 1A rules -> conditional on applies_section_1A
update requirements
set trigger_type      = 'conditional',
    trigger_condition = 'applies_section_1A == true',
    trigger_facts     = array['applies_section_1A']
where status = 'active' and reference like '1A%' and trigger_type = 'always';

-- already-conditional 1A rules -> AND the gate into the existing condition (once)
update requirements
set trigger_condition = 'applies_section_1A == true AND (' || trigger_condition || ')',
    trigger_facts     = array_append(trigger_facts, 'applies_section_1A')
where status = 'active' and reference like '1A%' and trigger_type = 'conditional'
  and not ('applies_section_1A' = any(trigger_facts));
