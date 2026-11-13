# Executed R research: process dependence, large-award sensitivity and SQL cross-checks.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Expected reports and dashboard output directories")
reports <- args[1]
web <- args[2]
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(jsonlite))
if (!requireNamespace("svglite", quietly = TRUE)) stop("Install svglite for SVG output")
script_path <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)[1])
source(file.path(dirname(script_path), "bootstrap.R"))
source(file.path(dirname(script_path), "concentration.R"))
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
d <- read.csv(file.path(reports, "statistical_input.csv"), stringsAsFactors = FALSE)
stopifnot(nrow(d) > 0, all(is.finite(d$amount)), all(d$amount > 0),
          !anyDuplicated(d$award_key), !anyNA(d$ocid))
buyer_results <- concentration_analysis(reports)
groups <- split(d, interaction(d$category, d$year, drop = TRUE, lex.order = TRUE))
result <- do.call(rbind, lapply(groups, function(g) {
  g <- g[order(g$award_key, method = "radix"), ]
  x <- g$amount
  seed <- stable_seed(paste(g$category[1], g$year[1]), 20261112)
  set.seed(seed)
  clustered <- replicate(500, weighted_median(x, cluster_weights(g$ocid)))
  set.seed(seed + 1L)
  independent <- replicate(500, median(sample(x, length(x), replace = TRUE)))
  interval <- quantile(clustered, c(.025, .975), names = FALSE, type = 7)
  alternative <- quantile(independent, c(.025, .975), names = FALSE, type = 7)
  cap <- unname(quantile(x, .99, type = 7))
  data.frame(
    category = g$category[1], year = g$year[1], awards = length(x),
    processes = length(unique(g$ocid)), seed = seed, median = median(x),
    median_low = interval[1], median_high = interval[2],
    award_bootstrap_low = alternative[1], award_bootstrap_high = alternative[2],
    total = sum(x), largest_share = max(x) / sum(x), capped_total = sum(pmin(x, cap)),
    excluded_largest_total = sum(x) - max(x), p99 = cap
  )
}))
rownames(result) <- NULL
stopifnot(all(result$median_low <= result$median_high),
          all(result$capped_total <= result$total), sum(result$awards) == nrow(d))
write.csv(result, file.path(reports, "category_sensitivity.csv"), row.names = FALSE)
packages <- c("ggplot2", "jsonlite", "svglite")
write.csv(data.frame(package = c("R", packages), version = c(as.character(getRversion()),
                        vapply(packages, function(p) as.character(packageVersion(p)), character(1)))),
          file.path(reports, "r_environment.csv"), row.names = FALSE)
p <- ggplot(result, aes(x = factor(year), y = median / 1000, group = category, color = category)) +
  geom_line(linewidth = .9) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = median_low / 1000, ymax = median_high / 1000), width = .10) +
  scale_color_manual(values = c("#087f8c", "#d38a22", "#6b5b95", "#cc5a55")) +
  labs(title = "Typical award size varies by category",
       subtitle = "Median recorded award · 500 procurement-process bootstrap resamples",
       x = NULL, y = "Award value (£ thousands)", color = "Category",
       caption = "Selected Contracts Finder snapshots · Descriptive intervals; reporting coverage is incomplete") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", plot.title = element_text(face = "bold"), panel.grid.minor = element_blank())
ggsave(file.path(web, "category-analysis.svg"), p, device = svglite::svglite, width = 10, height = 5.5, bg = "#ffffff")
if (!file.exists(file.path(web, "category-analysis.svg"))) stop("Chart output missing")
output <- list(replicates = 500, unit = "procurement process (ocid)",
               buyer_replicates = 300, random_generator = "Mersenne-Twister / Inversion / Rejection",
               interval = "2.5th–97.5th percentile of process-clustered bootstrap",
               limitations = "Awards within a process stay together. Processes treated as independent within each stratum. Buyer-level dependence across processes and missing reporting are not modeled; no causal or population inference.",
               categories = result, buyers = buyer_results)
write_json(output, file.path(reports, "r_analysis.json"), pretty = TRUE, auto_unbox = TRUE, digits = 15)
writeLines(trimws(capture.output(sessionInfo()), which = "right"), file.path(reports, "R-session.txt"))

escape_html <- function(x) {
  x <- gsub("&", "&amp;", x, fixed = TRUE)
  x <- gsub("<", "&lt;", x, fixed = TRUE)
  gsub(">", "&gt;", x, fixed = TRUE)
}
rows <- paste0("<tr><td>", escape_html(result$category), "</td><td>", result$year,
               "</td><td>", result$awards, " / ", result$processes,
               "</td><td>", format(round(result$median), big.mark = ","),
               "</td><td>", round(result$median_low), "–", round(result$median_high),
               "</td><td>", round(result$largest_share * 100, 1), "%</td></tr>", collapse = "")
buyer_rows <- paste0("<tr><td>", escape_html(buyer_results$buyer_name),
                     "</td><td>", buyer_results$awards, " / ", buyer_results$processes,
                     "</td><td>", round(buyer_results$hhi), "</td><td>", round(buyer_results$hhi_low),
                     "–", round(buyer_results$hhi_high), "</td><td>", round(buyer_results$hhi_without_largest),
                     "</td><td>", round(buyer_results$hhi_capped), "</td></tr>", collapse = "")
html <- paste0('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpendScope | R research note</title><link rel="stylesheet" href="research.css"></head><body><main><a href="index.html">← Dashboard</a><p class="eyebrow">EXECUTED R RESEARCH / v0.2</p><h1>Does the conclusion survive a different assumption?</h1><p class="lead">Procurement processes can contain several related awards. Resampling those awards independently can give a misleading picture of stability.</p><div class="note"><strong>What changed:</strong> the main intervals now resample whole procurement processes (OCIDs), preserving all awards within each selected process. Independent-award intervals remain downloadable as an explicit comparison.</div><img src="category-analysis.svg" alt="Median award values with process-clustered bootstrap intervals"><h2>Category comparisons</h2><p>500 resamples within each category-year. Process counts and per-group random seeds are included in the CSV. These are descriptive sensitivity intervals, not guarantees about all public procurement.</p><div class="table-wrap"><table><tr><th>Category</th><th>Year</th><th>Awards / processes</th><th>Median £</th><th>Clustered interval £</th><th>Largest award share</th></tr>', rows, '</table></div><h2>Buyer concentration sensitivity</h2><p>Top 30 supported buyer identities by attributable value; 300 process resamples per buyer. R independently reproduces SQL HHI before bootstrapping. Capping and removal scenarios change the analytical assumption, not the original records.</p><div class="table-wrap"><table><tr><th>Buyer identity</th><th>Awards / processes</th><th>HHI</th><th>Clustered interval</th><th>Without largest</th><th>Capped HHI</th></tr>', buyer_rows, '</table></div><h2>Remaining limits</h2><p>Processes are treated as independent within each stratum. Repeated buyers across different processes, missing reporting, unobserved links between frameworks and call-offs, inflation and publication changes are not modeled. No causal inference, spending estimate, or procurement savings claim is made.</p><div class="download-links"><a href="reports/category_sensitivity.csv">Category results ↓</a><a href="reports/buyer_sensitivity.csv">Buyer results ↓</a><a href="reports/identity_decisions.csv">Identity evidence ↓</a><a href="reports/notice_checks.json">Notice review ↓</a></div><p class="source">UK Contracts Finder, compiled by Open Contracting Partnership. Contains public sector information licensed under the Open Government Licence v3.0.</p></main></body></html>')
writeLines(html, file.path(web, "research.html"))
