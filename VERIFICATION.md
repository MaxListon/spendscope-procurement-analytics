# Verification record — 12 November 2026

Local v0.1.0 verification completed:

- Downloaded three real OCP/Contracts Finder source archives; pinned compressed SHA-256 hashes and byte sizes.
- Rebuilt from all 219,121 process snapshots, normalizing 173,551 award records and retaining 155,350 eligible awards.
- Seven SQL runtime contracts passed, including award-key uniqueness, no orphan supplier links, no joint-award attribution and count/value conservation.
- Installed the Python project and its dependencies in a fresh virtual environment, then completed a full offline source rebuild with executed R analysis.
- 30 Python tests passed, including known-answer HHI, failure-safe staging, malformed inputs, identity conflicts, missing static assets and artifact integrity.
- R concentration regression checks passed. R recomputed SQL HHI for the 30 supported buyer case studies within relative tolerance 1e-8.
- JavaScript syntax check passed. Fingerprint verification passed for 18 analysis inputs and 34 generated outputs; published manifest copies match.
- Browser checks: buyer search narrowed to one matching Hampshire buyer, filtered CSV download completed, R research note displayed both tables and its chart, and layouts at 375/1024/1440 pixels had no document-level horizontal overflow. Wide tables scroll inside their containers.
- Analysis tabs hide the overview hero to keep analytical controls visible.

CI configuration is supplied but has not yet run on GitHub. No public repository or live dashboard deployment is claimed for this release.

Remaining validation includes source-notice review for extreme values, labeled supplier matching evaluation, process-clustered sensitivity analysis, external usability feedback and an actual stakeholder review. The project plan describes proposed future work, not elapsed development time.
