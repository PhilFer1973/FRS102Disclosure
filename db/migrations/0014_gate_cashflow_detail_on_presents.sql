-- 0014: gate Section 7 cash-flow DETAIL rules on whether a cash flow statement
-- exists. The detail rules (indirect method, tax cash flows, reconciliation,
-- net debt, etc.) only apply if the entity actually presents a statement of cash
-- flows. Without this gate they kept asking their trigger facts (uses_indirect_
-- method_cash_flow, ...) even when there is no cash flow statement (e.g. FC, a
-- qualifying entity taking the exemption). 7.3 ("present a statement of cash
-- flows") is deliberately excluded — it is the rule that catches a MISSING
-- statement, so it must not be gated on the statement existing.

update requirements
set trigger_type      = 'conditional',
    trigger_condition = case
        when trigger_condition is null or trigger_condition = ''
            then 'presents_cash_flow_statement == true'
        else 'presents_cash_flow_statement == true AND (' || trigger_condition || ')'
    end,
    trigger_facts     = array_append(trigger_facts, 'presents_cash_flow_statement')
where status = 'active' and source = 'FRS102'
  and reference like '7.%' and reference <> '7.3'
  and not ('presents_cash_flow_statement' = any(trigger_facts));
