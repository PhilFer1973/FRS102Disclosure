-- 0015: reject 3.16B — it is the materiality CONCESSION ("an entity need not
-- provide a specific FRS 102 disclosure if the information is immaterial"), a
-- permission, not a required disclosure. As a missing-direction checklist rule it
-- wrongly flags every set of accounts. Reviewer (Phil) rejected it.
update requirements set status = 'rejected'
where source = 'FRS102' and reference = '3.16B' and status = 'active';
