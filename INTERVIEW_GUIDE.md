# Interview preparation

## Explain the problem

A procurement manager wants to understand dependence on suppliers. Raw award records contain multiple suppliers and revised notices, so a naive joined sum can inflate totals and produce misleading concentration rankings. SpendScope keeps the award accounting grain separate and shows the amount of evidence behind each comparison.

## Explain your design choices

- SQL defines shared business metrics; Python handles ingestion, identity normalization and build orchestration; R performs statistical sensitivity analysis and independently verifies HHI.
- A joint award remains one award in totals. Its full value is not attributed to every supplier, and equal allocations are not presented as facts.
- Registered IDs are useful evidence, but source conflicts are visible and excluded from attribution. Exact name matching is provisional; fuzzy matches are not silently accepted.
- A buyer can look concentrated because one large framework dominates. R tests removal and capping scenarios without asserting that the source amount is wrong.
- Good coverage is necessary for comparison but does not prove completeness. The independent-award bootstrap also misses process-level dependence.

## Demonstrate it

Rebuild the warehouse, query one buyer's supplier shares, reproduce its HHI in R, explain the coverage denominator, then open the original largest-award notice. Show a test where a joint award would otherwise double the total.

## Claims to avoid

Do not describe awarded commitments as payments, claim procurement savings, infer wrongdoing, or say name-only identities are verified companies. Do not claim the proposed schedule is actual elapsed work. Use measured counts and results from the current generated reports rather than memorizing unverified estimates.

A resume bullet should be finalized only after reviewing the results and reproducing the project yourself. Scope it to what you can explain.
