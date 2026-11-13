# Expanded validation and second-review plan

## Completed evidence versus outstanding review

The original 40-case registry-name audit remains unchanged. The same frozen hash ordering now selects 200 identities; 160 additional official registry profile observations are recorded in `data/review/registry_screen.json`. Selection is reconstructed from the original 11,517-identity frame, and the original 40 must remain its prefix. Pages were observed on 13 November 2026 UTC; each observed record includes its current/former names and response SHA-256. Unavailable pages retain their error. Response fingerprints detect accidental changes to recorded evidence; they do not independently authenticate a page without retained originals.

The automated rule only compares normalized current/former legal names: Unicode normalization, case, punctuation, `&`/`and`, and `Ltd`/`Limited`. It does not infer trading names, parent/subsidiary identity or whether a publisher attached the right company number to an award. A matching name is not a verified supplier assignment. No automatic attribution change follows from the screen.

Results: 134 name agreements, 21 cases requiring review, 5 unavailable pages. These are screening outcomes, not human validation labels. Do not combine them with the original 40 as a 200-case accuracy estimate.

## Next human review

An actual reviewer should inspect all 26 follow-up cases and label the remaining sample before reporting an expanded agreement estimate. Use compatible, conflict, unresolved and unavailable labels; record company number, published name, registry name, original award notice, observation date and rationale. Two reviewers should independently label a predetermined subset before reconciling disagreements. Do not force ambiguous trading names into conflict.

For independent labeling, withhold automated outcomes from the worksheet. Select the second-review subset before reviewing labels; retain both original labels and adjudication. Measure raw agreement and report class counts; a chance-corrected statistic may be useful but does not replace inspection of the disagreement cases. Reviewers can access public outcomes, so do not claim experimental blinding merely because worksheet columns were hidden.

Name-only identities require a separate frame and sampling design. There is no reliable registry key to screen automatically. Do not extend registration-based results to that population or claim precision/recall without an independently defined truth set.

## Refresh evidence deliberately

`python scripts/collect_registry_screen.py --root . --output /tmp/registry-screen-candidate.json` makes explicit live requests using three workers and verifies the profile number. It writes a candidate only; inspect it before replacing the versioned observations. CI never re-queries registry pages, so builds remain reproducible and do not silently rewrite historical labels.

A changed source snapshot invalidates the frozen frame unless deliberately revalidated. The pipeline refuses a frame mismatch. Keep the old observations and audit result for comparison rather than silently relabeling the original sample.
