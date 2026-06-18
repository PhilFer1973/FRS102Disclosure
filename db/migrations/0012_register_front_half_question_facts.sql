-- 0012: register the front-half conditional-question facts.
--
-- The front-half review surfaces two conditional items as reviewer QUESTIONS
-- (dividend recommended? average employees > 250?). questions.fact_key has a
-- NOT NULL foreign key to fact_registry, so these keys must be registered or the
-- run cannot persist its question round. They are genuine boolean review facts.

insert into fact_registry (key, description, value_type) values
    ('dividend_recommended',
     'TRUE if the directors recommend (or have declared) a dividend for the '
     'period; relevant to the CA06 s416(3) directors-report statement.',
     'boolean'),
    ('average_employees_gt_250',
     'TRUE if the company employed on average more than 250 persons in the year; '
     'triggers the SI 2008/410 Sch 7 employee-engagement and disabled-persons '
     'directors-report statements.',
     'boolean')
on conflict (key) do nothing;
