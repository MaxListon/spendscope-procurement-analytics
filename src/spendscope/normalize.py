"""Conservative record and identity normalization. Never allocate award totals to suppliers."""

import hashlib
import math
import re
import unicodedata
from datetime import datetime, timezone


def normalized_name(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def date(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def supplier_identity(supplier, parties):
    name = normalized_name(supplier.get("name"))
    party = parties.get(supplier.get("id"), {})
    identifier = party.get("identifier") or {}
    scheme, ident = identifier.get("scheme"), identifier.get("id")
    # Local CFS numbers are publication identifiers, not verified company identities.
    if scheme in ("GB-COH", "GB-CHC", "GB-SC") and ident:
        token = str(ident).strip().upper()
        if scheme == "GB-COH" and token.isdigit():
            token = token.zfill(8)
        return f"{scheme}:{token}", "registered", name
    if name:
        return "name:" + digest(name), "name-only", name
    return "unknown:" + digest(str(supplier.get("id", ""))), "unknown", ""


def normalize_awards(record):
    ocid = str(record.get("ocid") or "").strip()
    if not ocid:
        raise ValueError("Process has no ocid")
    tender = record.get("tender") or {}
    buyer = record.get("buyer") or {}
    buyer_name = str(buyer.get("name") or "Unknown buyer")
    buyer_key = digest(str(buyer.get("id") or "") + "|" + normalized_name(buyer_name))
    parties = {x["id"]: x for x in record.get("parties", []) if x.get("id")}
    awards, links = [], []
    seen = set()
    for award in record.get("awards", []):
        aid = str(award.get("id") or "").strip()
        if not aid or aid in seen:
            raise ValueError(f"Missing or repeated award ID in {ocid}")
        seen.add(aid)
        key = digest(ocid + "|" + aid)
        value = award.get("value") or {}
        amount = value.get("amount")
        valid_amount = (
            isinstance(amount, (int, float))
            and not isinstance(amount, bool)
            and math.isfinite(amount)
            and amount > 0
        )
        dt = date(award.get("date"))
        status = award.get("status", "missing")
        reason = (
            "status"
            if status != "active"
            else "amount"
            if not valid_amount
            else "currency"
            if value.get("currency") != "GBP"
            else "award_date"
            if not dt or not 2022 <= dt.year <= 2024
            else ""
        )
        suppliers = award.get("suppliers") or []
        identities = {}
        for supplier in suppliers:
            identity, basis, name = supplier_identity(supplier, parties)
            identities[(identity, name)] = dict(
                supplier_key=identity,
                identity_basis=basis,
                supplier_name=str(supplier.get("name") or "Unknown supplier"),
                normalized_name=name,
            )
        period = award.get("contractPeriod") or {}
        end = date(period.get("endDate"))
        start = date(period.get("startDate"))
        docs = award.get("documents") or []
        url = next(
            (
                x.get("url")
                for x in docs
                if str(x.get("url", "")).startswith(
                    "https://www.contractsfinder.service.gov.uk/Notice/"
                )
            ),
            "",
        )
        row = dict(
            award_key=key,
            ocid=ocid,
            award_id=aid,
            buyer_key=buyer_key,
            buyer_name=buyer_name,
            title=str(tender.get("title") or "Untitled award"),
            year=dt.year if dt else None,
            month=dt.strftime("%Y-%m") if dt else None,
            award_date=dt.date().isoformat() if dt else "",
            amount=float(amount) if valid_amount else None,
            currency=str(value.get("currency") or ""),
            status=status,
            exclusion_reason=reason,
            eligible=not bool(reason),
            category=str(tender.get("mainProcurementCategory") or "unspecified"),
            cpv=str((tender.get("classification") or {}).get("id") or ""),
            supplier_count=len(identities),
            method=str(tender.get("procurementMethod") or "unspecified"),
            end_date=end.date().isoformat() if end else "",
            period_valid=bool(
                start
                and end
                and end >= start
                and 2000 <= start.year <= end.year <= 2100
            ),
            source_url=url,
        )
        awards.append(row)
        for identity in identities.values():
            links.append(dict(award_key=key, **identity))
    return awards, links
