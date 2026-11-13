-- One eligible award remains one row. Attributed is unique by award_key.
CREATE TABLE investigation_awards AS
SELECT a.buyer_key,a.award_key,a.ocid,a.title,a.award_date,a.amount,a.supplier_count,a.source_url,
       a.notice_review_status,a.notice_review_block,
       t.supplier_key,t.supplier_name,t.identity_basis,
       t.award_key IS NOT NULL AS attributed
FROM eligible a LEFT JOIN attributed t USING(award_key);

-- Remove the single largest attributed award, not its entire supplier.
CREATE TABLE investigation_sensitivity AS
WITH ordered AS (
 SELECT buyer_key,supplier_key,amount,
 row_number() OVER(PARTITION BY buyer_key ORDER BY amount DESC,award_key) pos
 FROM attributed
), residual AS (
 SELECT bs.buyer_key,bs.supplier_key,
 bs.award_value - CASE WHEN bs.supplier_key=o.supplier_key THEN o.amount ELSE 0 END amount
 FROM buyer_supplier bs JOIN ordered o ON bs.buyer_key=o.buyer_key AND o.pos=1
)
SELECT buyer_key,sum(amount) residual_value,
 CASE WHEN sum(amount)>0 THEN 10000*sum(amount*amount)/pow(sum(amount),2) END hhi_without_largest
FROM residual GROUP BY buyer_key;

CREATE TABLE investigation_summary AS
WITH largest AS (
 SELECT buyer_key,max(amount) largest_eligible_award FROM eligible GROUP BY buyer_key
)
SELECT b.*,e.registered_awards,e.registered_value_share,
 l.largest_eligible_award,s.hhi_without_largest,s.residual_value
FROM buyer_concentration b JOIN buyer_evidence e USING(buyer_key)
JOIN largest l USING(buyer_key) JOIN investigation_sensitivity s USING(buyer_key);
