# Procurement concentration: evidence before prioritization

Use SpendScope to select records and buyer portfolios for review. Headline award value is not spending, and concentration alone is not an operational supplier-risk assessment.

## Findings

- **Coverage limits the comparison.** About 32.9% of eligible award value meets conservative supplier-attribution rules. The default view compares 350 buyer identities with at least 30 attributable awards and 80% value coverage. These are publication identities, not 350 fully resolved organizations; aliases and multiple IDs can split buyers.
- **Framework-sized records dominate totals.** The largest eligible record is a £150 billion award-value entry titled “EEM0056 Property Improvements and Decarbonisation Works Framework,” with 19 suppliers. It is counted once in recorded totals and excluded from supplier attribution. Its published amount is preserved, not assumed to be spending or automatically corrected. [Notice](https://www.contractsfinder.service.gov.uk/Notice/22498071-7872-45a0-ae26-4077553233f5).
- **One commitment can change the interpretation.** For the HAMPSHIRE COUNTY COUNCIL buyer identity, attributable HHI is approximately 7,454. Removing the largest award reduces it to 1,066; applying a buyer-specific 99th-percentile cap reduces it to 852. The largest award contributes 86.2% of attributable value, while only 4.9% of attributable value has registered-identifier evidence. Review the notice and identities before interpreting dependency. [Largest award notice](https://www.contractsfinder.service.gov.uk/Notice/4ab0a212-b807-4efb-a6de-e45622b78064).
- **Typical awards tell a different story from sums.** Overall median eligible awards are approximately £82,841 in 2022, £85,888 in 2023 and £82,000 in 2024. Source coverage, revisions, composition and inflation are not controlled. These are descriptive comparisons, not evidence of improved procurement.

## Recommended next work

Review the 20 largest notices and label framework ceilings, multi-year values, possible overlaps and unresolved anomalies. Notice URLs are supplied, but linked page content has not yet been independently validated in this release.

Manually label supplier matches and registered-ID conflicts before relaxing exclusions. Compare buyer rankings under alternate coverage thresholds and process-clustered resampling. Obtain payment or purchasing-system data before estimating actual spend or realized savings.

Evidence: `reports/annual.csv`, `reports/buyer_concentration.csv`, `reports/buyer_sensitivity.csv`, `reports/category_sensitivity.csv`, `reports/quality.json` and `data/sources.json`.

No external stakeholder validation or measured business impact is claimed.
