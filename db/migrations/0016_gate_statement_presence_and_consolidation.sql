-- 0016: stop statement-presence / recognition rules false-flagging when the tool
-- can plainly see the statement is there (Phil's verdicts on the FC findings).
-- All general, keyed on computed presence facts — not entity-specific.

-- Register the computed presence facts these gates reference (trigger enforces
-- that every trigger fact is in fact_registry). All read deterministically from
-- the extraction, never asked.
insert into fact_registry (key, description, value_type) values
    ('presents_income_statement',
     'TRUE if the accounts present an income statement / profit and loss account '
     '/ statement of comprehensive income.', 'boolean'),
    ('presents_balance_sheet',
     'TRUE if the accounts present a balance sheet / statement of financial '
     'position.', 'boolean'),
    ('presents_statement_of_changes_in_equity',
     'TRUE if the accounts present a statement of changes in equity.', 'boolean'),
    ('presents_notes',
     'TRUE if the accounts include notes to the financial statements.', 'boolean'),
    ('prepares_consolidated_financial_statements',
     'TRUE if the entity prepares consolidated (group) financial statements.',
     'boolean')
on conflict (key) do nothing;

-- 9.8 recognition principle ("do not exclude a subsidiary from consolidation
-- solely because...") is an ALWAYS rule, so it fires on every set. It is only
-- relevant to an entity that actually prepares consolidated statements. Gate it.
update requirements
set trigger_type      = 'conditional',
    trigger_condition = 'prepares_consolidated_financial_statements == true',
    trigger_facts     = array_append(trigger_facts, 'prepares_consolidated_financial_statements')
where status = 'active' and source = 'FRS102' and reference = '9.8'
  and trigger_type = 'always'
  and not ('prepares_consolidated_financial_statements' = any(trigger_facts));

-- 3.17 complete-set components are ALWAYS rules, so each component is flagged
-- "missing" even when it is present. Gate each on its own presence fact, so it
-- only fires when that statement is genuinely absent.
update requirements set trigger_type='conditional',
    trigger_condition='presents_statement_of_changes_in_equity == false',
    trigger_facts=array_append(trigger_facts,'presents_statement_of_changes_in_equity')
where status='active' and source='FRS102' and reference='3.17' and trigger_type='always'
  and requirement_text ilike '%statement of changes in equity%';

update requirements set trigger_type='conditional',
    trigger_condition='presents_balance_sheet == false',
    trigger_facts=array_append(trigger_facts,'presents_balance_sheet')
where status='active' and source='FRS102' and reference='3.17' and trigger_type='always'
  and requirement_text ilike '%statement of financial position%';

update requirements set trigger_type='conditional',
    trigger_condition='presents_income_statement == false',
    trigger_facts=array_append(trigger_facts,'presents_income_statement')
where status='active' and source='FRS102' and reference='3.17' and trigger_type='always'
  and requirement_text ilike '%statement of comprehensive income%';

update requirements set trigger_type='conditional',
    trigger_condition='presents_notes == false',
    trigger_facts=array_append(trigger_facts,'presents_notes')
where status='active' and source='FRS102' and reference='3.17' and trigger_type='always'
  and requirement_text ilike '%notes comprising%';

-- 3.17 catch-all ("all of the required components") and the duplicate always-on
-- cash-flow component (the exemption-aware 3.17 row already covers cash flow) are
-- redundant noise — reject them.
update requirements set status='rejected'
where status='active' and source='FRS102' and reference='3.17' and trigger_type='always'
  and (requirement_text ilike '%required components%'
       or requirement_text ilike '%statement of cash flows%');

-- 3.21 equal-prominence is a presentation principle the tool cannot verify from
-- the layout; only surface it if a primary statement is actually missing.
update requirements set trigger_type='conditional',
    trigger_condition='presents_balance_sheet == false OR presents_income_statement == false',
    trigger_facts=array_cat(trigger_facts,
        array['presents_balance_sheet','presents_income_statement'])
where status='active' and source='FRS102' and reference='3.21' and trigger_type='always';

-- 6.2 SOCE-content rules can't be verified line-by-line from the statement table,
-- so they false-flag when a SOCE exists. Gate them all on the SOCE being absent —
-- i.e. only flag when there is no statement of changes in equity at all.
update requirements set trigger_type='conditional',
    trigger_condition = case
        when trigger_condition is null or trigger_condition=''
            then 'presents_statement_of_changes_in_equity == false'
        else '(' || trigger_condition || ') AND presents_statement_of_changes_in_equity == false'
    end,
    trigger_facts=array_append(trigger_facts,'presents_statement_of_changes_in_equity')
where status='active' and source='FRS102' and reference='6.2'
  and not ('presents_statement_of_changes_in_equity' = any(trigger_facts));
