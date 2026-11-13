source("R/bootstrap.R")
source("R/concentration.R")
stopifnot(hhi(c(75, 25), c("A", "B")) == 6250,
          hhi(c(50, 50), c("A", "A")) == 10000,
          abs(hhi(rep(1, 4), LETTERS[1:4]) - 2500) < 1e-10)
# One resampled process must carry all of its awards with the same multiplicity.
stopifnot(identical(cluster_weights(c("p1", "p1", "p2"), c(1L, 1L)), c(2L, 2L, 0L)))
stopifnot(weighted_median(c(10, 20, 100), c(2, 2, 0)) == 15,
          weighted_median(c(10, 20, 100), c(1, 0, 2)) == 100)
# Weighted implementation equals literal expansion, including even-length medians.
for (weights in list(c(1, 2, 3), c(0, 2, 2), c(3, 0, 0))) {
  stopifnot(weighted_median(c(3, 8, 50), weights) == median(rep(c(3, 8, 50), weights)))
}
# Bootstrap dependence counterexample: a single process with two linked awards cannot split.
stopifnot(identical(cluster_weights(c("p", "p")), c(1L, 1L)))
stopifnot(inherits(try(hhi(c(0, 1), c("A", "B")), silent = TRUE), "try-error"))
x <- c("True", "False", "TRUE", "FALSE")
stopifnot(identical(tolower(x) == "true", c(TRUE, FALSE, TRUE, FALSE)))
cat("R HHI, weighted median and process-cluster regression checks passed.\n")
# Different processes belonging to the same buyer retain a common multiplicity.
buyer_weights <- cluster_weights(c("buyerA", "buyerA", "buyerB"), c(1L, 1L))
stopifnot(identical(buyer_weights, c(2L, 2L, 0L)))
# Calendar grouping never splits records in the same quarter.
stopifnot(identical(cluster_weights(c("2022-Q1", "2022-Q1", "2022-Q2"), c(2L, 2L)), c(0L, 0L, 2L)))
