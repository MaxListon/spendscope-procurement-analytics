# Independently verify SQL, then compare process-clustered and independent-award resampling.
concentration_analysis <- function(reports) {
  a <- read.csv(file.path(reports, "attributed_input.csv"), stringsAsFactors = FALSE)
  sql <- read.csv(file.path(reports, "buyer_concentration.csv"), stringsAsFactors = FALSE)
  sql$supported <- tolower(as.character(sql$supported)) == "true"
  chosen <- head(sql[sql$supported, ], 30)
  if (!nrow(chosen)) stop("No supported buyers for sensitivity analysis")
  result <- do.call(rbind, lapply(seq_len(nrow(chosen)), function(i) {
    buyer <- chosen[i, ]
    g <- a[a$buyer_key == buyer$buyer_key, ]
    g <- g[order(g$award_key, method = "radix"), ]
    x <- g$amount
    supplier <- g$supplier_key
    point <- hhi(x, supplier)
    if (!isTRUE(all.equal(point, buyer$hhi, tolerance = 1e-8))) {
      stop(sprintf("R/SQL HHI disagreement for %s", buyer$buyer_key))
    }
    seed <- stable_seed(buyer$buyer_key, 20261113)
    set.seed(seed)
    clustered <- replicate(300, hhi(x, supplier, cluster_weights(g$ocid)))
    set.seed(seed + 1L)
    independent <- replicate(300, {
      j <- sample.int(length(x), length(x), replace = TRUE)
      hhi(x[j], supplier[j])
    })
    interval <- quantile(clustered, c(.025, .975), names = FALSE, type = 7)
    alternative <- quantile(independent, c(.025, .975), names = FALSE, type = 7)
    largest <- which.max(x)
    cap <- unname(quantile(x, .99, type = 7))
    data.frame(
      buyer_key = buyer$buyer_key, buyer_name = buyer$buyer_name,
      awards = length(x), processes = length(unique(g$ocid)), seed = seed,
      hhi = point, hhi_low = interval[1], hhi_high = interval[2],
      award_bootstrap_low = alternative[1], award_bootstrap_high = alternative[2],
      hhi_without_largest = hhi(x[-largest], supplier[-largest]),
      hhi_capped = hhi(pmin(x, cap), supplier), largest_award_share = max(x) / sum(x),
      registered_value_share = sum(x[g$identity_basis %in% c("registered", "registered-reviewed")]) / sum(x),
      value_coverage = buyer$value_coverage
    )
  }))
  rownames(result) <- NULL
  stopifnot(all(is.finite(result$hhi)), all(result$hhi > 0), all(result$hhi <= 10000.00001),
            all(result$hhi_low <= result$hhi_high))
  write.csv(result, file.path(reports, "buyer_sensitivity.csv"), row.names = FALSE)
  result
}
