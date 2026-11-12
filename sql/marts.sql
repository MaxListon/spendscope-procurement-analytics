-- Award grain remains one row per process + award ID. No supplier fan-out of totals.
CREATE TABLE eligible AS SELECT * FROM awards WHERE eligible;
CREATE TABLE annual AS
SELECT year, count(*) awards, sum(amount) award_value, median(amount) median_award,
       count(DISTINCT buyer_key) buyers,
       sum(CASE WHEN supplier_count=1 THEN amount ELSE 0 END)/sum(amount) sole_supplier_value_share
FROM eligible GROUP BY year ORDER BY year;
CREATE TABLE categories AS
SELECT category, year, count(*) awards, sum(amount) award_value, median(amount) median_award
FROM eligible GROUP BY category,year ORDER BY category,year;
-- Attribution restricted to sole-supplier awards with a named, non-colliding identity.
CREATE TABLE attributed AS
SELECT a.*, s.supplier_key,s.supplier_name,s.identity_basis
FROM eligible a JOIN suppliers s USING(award_key)
WHERE a.supplier_count=1 AND s.identity_basis IN ('registered','name-only') AND s.normalized_name<>'';
CREATE TABLE buyer_supplier AS
SELECT buyer_key, max(buyer_name) buyer_name, supplier_key, max(supplier_name) supplier_name,
       count(*) awards, sum(amount) award_value
FROM attributed GROUP BY buyer_key,supplier_key;
CREATE TABLE buyer_concentration AS
WITH shares AS (
 SELECT *, award_value/sum(award_value) OVER(PARTITION BY buyer_key) share,
 row_number() OVER(PARTITION BY buyer_key ORDER BY award_value DESC,supplier_key) rank
 FROM buyer_supplier
), metrics AS (
 SELECT buyer_key,max(buyer_name) buyer_name,count(*) suppliers,sum(awards) attributed_awards,
 sum(award_value) attributed_value, sum(share*share)*10000 hhi, max(share) top1_share,
 sum(CASE WHEN rank<=5 THEN share ELSE 0 END) top5_share
 FROM shares GROUP BY buyer_key
), totals AS (
 SELECT buyer_key,count(*) total_awards,sum(amount) total_value FROM eligible GROUP BY buyer_key
)
SELECT m.*,t.total_awards,t.total_value,m.attributed_value/t.total_value value_coverage,
 m.attributed_awards>=30 AND m.attributed_value/t.total_value>=0.8 AS supported
FROM metrics m JOIN totals t USING(buyer_key) ORDER BY attributed_value DESC,buyer_key;
CREATE TABLE supplier_summary AS
SELECT supplier_key,max(supplier_name) supplier_name,max(identity_basis) identity_basis,
 count(*) awards,count(DISTINCT buyer_key) buyers,sum(amount) award_value
FROM attributed GROUP BY supplier_key ORDER BY award_value DESC,supplier_key;
CREATE TABLE identity_review AS
SELECT supplier_key,count(DISTINCT normalized_name) names, count(*) award_links
FROM suppliers WHERE identity_basis='collision'
GROUP BY supplier_key ORDER BY award_links DESC;
