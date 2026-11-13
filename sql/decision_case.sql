-- Parameter is the exact publication identity from the executed R case.
-- Names alone are not unique; commitments are not payments.
SELECT buyer_key, buyer_name, award_key, ocid, title, amount,
       supplier_key, supplier_name, identity_basis, source_url
FROM attributed
WHERE buyer_key = ?
ORDER BY amount DESC, award_key
LIMIT 20;
