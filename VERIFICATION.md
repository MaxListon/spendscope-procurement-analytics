# Verification record — v0.5, 13 November 2026

## Executed checks

- Full rebuild from the three pinned real-source archives: 219,121 processes and 155,350 eligible awards. Ten SQL runtime contracts passed.
- Generated 12,751 exact-ID buyer investigation profiles, 256 on-demand JSON groups and an explainable queue. The 1,556 eligible buyer identities with zero attributable awards remain in headline totals but have no concentration profile.
- Every exported profile reconciles supplier amounts to attributable value and award rows/amounts to eligible value. A known-answer test verifies removing one award rather than its whole supplier; homonymous buyers remain separate.
- Preserved the original 40-case registry audit and separate 160 automated name screens. Generated 160 blank first-review worksheets and a fixed 40-case second-review subset. The scoring tool rejects blank submissions; no outside reviewer labels were invented.
- 106 Python tests passed; eight JavaScript review-model tests passed; R regression checks passed.
- Verified 41 analysis inputs and 326 generated outputs against their fingerprints.
- Browser checks: exact Home Office profile shows 311 awards, HHI 1,113 and 35 evidence-priority points; all eligible award rows are available through pagination/export. Mobile width 375px has no document overflow; 20 award and supplier rows render initially; no browser error logs observed.
- Used explicitly marked synthetic localhost notes to verify save, reload persistence, blocked closure with unresolved questions, export and idempotent restore. Those notes exist only in local browser storage, never in repository artifacts. A clean browser origin starts Open with zero review entries.
- Profile and index version checks, no-store data fetches, transactional parent checks, archive conflict validation and separate archived data/rule versions are implemented. These do not authenticate a reviewer or create a tamper-proof audit log.

## Release and limitations

Public GitHub and dashboard publication are authorized. Verify the exact release commit's cloud Checks and Dashboard runs before reporting deployment success. Cloud CI installs the wheel, rebuilds original-source/R analysis and compares both analytical JSON and the investigation index against the committed results.

This is a static research and investigation portfolio tool. Review history is local to a browser/device, with export and restore; no shared backend, authentication, team synchronization or service-level guarantee is claimed. Independent professional review, completed participant testing, general matching precision/recall, actual payments and realized organizational impact remain outstanding.
