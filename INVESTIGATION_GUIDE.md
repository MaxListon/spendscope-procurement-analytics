# Supplier investigation workspace

The workspace turns concentration analysis into a reproducible evidence review. It is a static portfolio tool, not a shared production case-management service.

## Exact identities and denominators

Open `workspace.html`. The queue includes all 12,751 publication identities with at least one attributable award, including limited-coverage cases. Buyer names are not unique: URLs and exports use the 24-character publication key. The default £10 million eligible-value filter controls materiality, not statistical support. Buyer identities with zero attributable awards stay in headline totals but have no supplier concentration profile; the queue states how many are excluded.

Each profile shows eligible commitments, attributable commitments, identity evidence, supplier shares, original eligible award records, and concentration sensitivity. Shares reconcile to attributable value; award rows reconcile to eligible value without supplier-join multiplication. Records are paged in the browser, and CSV downloads contain the full selected buyer portfolio. Joint or unresolved awards stay visible without invented supplier shares.

The largest-award alternative removes one attributed award and recomputes shares across the remaining supplier amounts. It does not delete an entire supplier. If there is no residual portfolio, HHI is undefined, not zero. Process/quarter R intervals are shown only for the 30 researched supported identities; no intervals are inferred for other buyers.

## Review-priority rules

| Observed condition | Points |
|---|---:|
| Attributable-value coverage below 80% | 30 |
| Registration evidence below 50% of attributable value | 20 |
| Largest eligible award at least £10 million | 15 |
| Largest supplier at least 50% of attributable value | 15 |
| Removing largest attributed award changes HHI by at least 500 points, or leaves no residual portfolio | 20 |

Points are additive, maximum 100. Ties sort by largest eligible award, then buyer key. These are explicit operational heuristics for allocating evidence-review effort, not validated predictors of risk, fraud, performance, competition harm or savings. A high score with low coverage is a question to investigate, not a trustworthy ranking of operational dependency. Registration format/name agreement alone does not verify the source supplier assignment.

## Decision history

A new case starts Open. Begin In review, then move to Awaiting evidence or Closed with decision. Reopen a closed case through In review. Notes can be appended within a state. Closure requires an HTTPS evidence URL, a substantive note and no unresolved questions in the form. The form cannot establish that a human actually resolved a question or that a submitted claim is true.

Entries are stored in IndexedDB on this browser/device. They are not uploaded to GitHub or the public dashboard. No reviews are prepopulated. Export all history before changing devices or clearing site data. JSON restore validates entries, evidence URLs, parent chains, status transitions and duplicate IDs. Altered entries, missing parents and conflicting branches are rejected as one transaction. Concurrent tabs recheck the latest parent inside a write transaction; stale writes are refused and text is retained. History is append-only through this interface, not authenticated or tamper-proof.

The index and profile fetches bypass browser caches, and profiles carry the same data/rule ID as the index; a mismatch blocks review. Data/rule versions derive from pinned source hashes and analysis/evidence inputs. Old-version entries remain archived and exportable but do not mark a current case reviewed. Browser storage can be unavailable or cleared; analytics remains available and saving reports its failure. No server, authentication, team synchronization, service-level guarantee or external stakeholder sign-off is claimed. For real organizational deployment those capabilities and access controls would need a separate backend design.

## Independent registry review remains outstanding

`reports/independent_registry_review.csv` contains 160 unfilled worksheets without automated outcomes. `reports/second_registry_review.csv` is a predetermined 40-case subset selected with hash seed `second-review-subset-v1`. Public automated labels exist, so hidden worksheet columns alone do not establish experimental blinding. Reviewer codes are declarations, not identity verification.

Ask real reviewers to record `compatible`, `conflict`, `unresolved` or `not_observed`, along with observed legal name, reviewer code, ISO date and a substantive rationale. Preserve both original label sets before adjudicating disagreements. Do not overwrite the original 40-case audit or combine automated screens with human labels as a 200-case accuracy result.

After genuine submissions exist:

```sh
python scripts/score_registry_review.py /path/to/first-review.csv /path/to/second-review.csv --root . --output /tmp/reviewer-agreement.json
```

The tool reconstructs expected cases from the versioned screen, rejects blank/incomplete submissions, and requires different declared reviewers on overlapping cases. It reports categorical agreement and disagreement IDs, including unresolved/unavailable outcomes. It cannot authenticate independence, estimate general entity-matching precision/recall, or replace substantive adjudication. No completed second review is claimed.

## Complete decision demonstration

Follow the generated business brief and exact Home Office profile: publication key `b49f4c311ff916ace705f91d`, 311 attributable awards, HHI approximately 1,113. Its 35 priority points arise from low registration evidence and a large commitment. It is a researched example, not the highest-scoring queue entry. Inspect sensitivity and notices, collect missing legal/payment/framework evidence, and keep the case awaiting evidence until a reviewer can support a decision. No procurement intervention, stakeholder endorsement or realized savings is asserted.
