# Sampling units are explicit: draw procurement processes and keep their awards together.
weighted_median <- function(x, weights) {
  stopifnot(length(x) == length(weights), all(is.finite(x)),
            all(is.finite(weights)), all(weights >= 0), all(weights == floor(weights)))
  n <- sum(weights)
  if (n < 1) stop("No observations in resample")
  order <- order(x, method = "radix")
  values <- x[order]
  cumulative <- cumsum(weights[order])
  positions <- c(floor((n + 1) / 2), ceiling((n + 1) / 2))
  mean(vapply(positions, function(k) values[which(cumulative >= k)[1]], numeric(1)))
}

cluster_weights <- function(cluster, draws = NULL) {
  if (anyNA(cluster) || any(!nzchar(cluster))) stop("Cluster IDs must be complete")
  ids <- sort(unique(cluster), method = "radix")
  if (is.null(draws)) draws <- sample.int(length(ids), length(ids), replace = TRUE)
  if (length(draws) != length(ids) || any(draws < 1 | draws > length(ids))) {
    stop("Cluster draw must contain exactly one bootstrap sample of process IDs")
  }
  tabulate(draws, nbins = length(ids))[match(cluster, ids)]
}

hhi <- function(amount, supplier, weights = rep(1, length(amount))) {
  if (!length(amount) || any(!is.finite(amount)) || any(amount <= 0) ||
      length(amount) != length(supplier) || length(weights) != length(amount) ||
      anyNA(supplier) || any(!nzchar(supplier)) || any(weights < 0) || sum(weights) <= 0) {
    stop("HHI requires positive amounts and valid supplier/weight vectors")
  }
  totals <- tapply(amount * weights, supplier, sum)
  sum((totals / sum(totals))^2) * 10000
}

stable_seed <- function(key, base) {
  chars <- utf8ToInt(key)
  as.integer((base + sum(chars * seq_along(chars))) %% .Machine$integer.max)
}
