-- 0009: reviewer-driven rule fixes (Phil, 2026-06-18) on the FC.pdf register.
--
-- (a) FRS 102 34.40 was promoted as an 'always' rule, so the retirement-benefit-
--     plan disclosure fired on EVERY entity. Its siblings (34.41-34.48) are all
--     correctly conditional on is_retirement_benefit_plan; 34.40 should be too.
--     (Reviewer note #3: "this entity is not a retirement benefit plan".)
--
-- (b) Add the Companies Act 2006 s411 average-number-of-employees note. No
--     existing rule covers it (28.42/28.44 are long-term/termination benefits).
--     Reviewer note #11/#12: "the number of employees should be stated in a note".
--     Signed off by Phil to add as a new requirement.

update requirements
set trigger_type      = 'conditional',
    trigger_condition = 'is_retirement_benefit_plan == true',
    trigger_facts     = array['is_retirement_benefit_plan']
where source = 'FRS102' and reference = '34.40' and trigger_type = 'always';

insert into requirements (source, reference, edition, applies_to, requirement_text,
    trigger_type, trigger_condition, trigger_facts, direction, severity,
    review_notes, status)
select 'CA06', 's411', 'both', 'all',
       'The notes to the accounts must state the average number of persons '
       'employed by the company in the financial year, determined as the monthly '
       'average (Companies Act 2006 s411). Medium and large companies must also '
       'analyse it by category of employee.',
       'always', null, '{}', 'missing', 'statutory',
       '[added 2026-06-18 per reviewer sign-off (Phil): CA06 s411 average number '
       'of employees note — new requirement, no prior coverage]',
       'active'
where not exists (
    select 1 from requirements where source = 'CA06' and reference = 's411');
