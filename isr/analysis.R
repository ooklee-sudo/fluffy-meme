## =====================================================================
## Analysis script for the blanks in Section 7 of
## "Who Profits from Large Language Models?"
##
## The script assumes four CSV files with the columns listed below.
## Rename columns in the "Load data" block if yours differ.
##
## lab_month.csv    : lab, month (YYYY-MM-DD), log_price, lead, live (0/1)
## model_month.csv  : model, lab, month, log_price, lead_own
##                    (lead_own = model's own quality lead over the best
##                     alternative that month; negative once it is overtaken)
## launch.csv       : model, lab, log_launch_price, lead_at_launch
## adopter.csv      : firm, fy, op_margin, gross_margin, opex_ratio,
##                    ga_year (NA if never), exposure (0/1 pooled API use,
##                    no GA), sic2, size_pre, margin_pre, trend_pre
##
## Packages: fixest, fwildclusterboot, did, MatchIt, dplyr, readr
## =====================================================================
suppressPackageStartupMessages({
  library(dplyr); library(readr); library(fixest)
  library(fwildclusterboot); library(did); library(MatchIt)
})
set.seed(13)
dir.create("output", showWarnings = FALSE)

## ---------------------------- Load data ------------------------------
lab   <- read_csv("lab_month.csv",   show_col_types = FALSE) |>
  mutate(month = as.Date(month), t = as.numeric(month - min(month)) / 30.4)
mm    <- read_csv("model_month.csv", show_col_types = FALSE) |>
  mutate(month = as.Date(month))
lnch  <- read_csv("launch.csv",      show_col_types = FALSE)
ad    <- read_csv("adopter.csv",     show_col_types = FALSE) |>
  mutate(treated = as.integer(!is.na(ga_year)),
         post    = as.integer(treated == 1 & fy >= ga_year),
         event_time = ifelse(treated == 1, fy - ga_year, NA_integer_))

## ===================================================================
## 7.1  Developer side
## ===================================================================

## --- Lab-month association with wild cluster bootstrap (Webb) -------
lab_fit <- function(d) feols(log_price ~ lead + t | lab, data = d, cluster = ~lab)

boot_p <- function(fit, param = "lead", B = 9999) {
  b <- boottest(fit, param = param, clustid = "lab", B = B, type = "webb")
  c(estimate = unname(coef(fit)[param]), p_conventional = pvalue(fit)[param],
    p_wild_webb = b$p_val, ci_lo = b$conf_int[1], ci_hi = b$conf_int[2])
}

res_lab <- rbind(
  "all 171 lab-months" = boot_p(lab_fit(lab)),
  "live endpoints only (102)" = boot_p(lab_fit(filter(lab, live == 1)))
)
print(round(res_lab, 4)); write.csv(res_lab, "output/tab_lab_month.csv")
## NOTE: with very few labs, Webb weights are recommended below ~12 clusters
## (Webb 2023). Report n_clusters = n_distinct(lab$lab) next to the table.

## --- H1a: within-model response to own lead (model + month FE) ------
h1a <- feols(log_price ~ lead_own | model + month, data = mm, cluster = ~lab)
h1a_boot <- boottest(h1a, param = "lead_own", clustid = "lab", B = 9999, type = "webb")
cat("\nH1a: beta =", coef(h1a)["lead_own"], " wild-boot p =", h1a_boot$p_val, "\n")

## --- Catch-up event study: price around the month a model loses lead --
lost <- mm |> group_by(model) |>
  mutate(had_lead = lead_own > 0, lost_now = had_lead & lead(lead_own, default = NA) <= 0) |>
  filter(lost_now) |> summarise(lost_month = first(month), .groups = "drop")
es_dev <- mm |> inner_join(lost, by = "model") |>
  mutate(k = round(as.numeric(difftime(month, lost_month, units = "days")) / 30.4)) |>
  filter(between(k, -6, 6))
h1a_es <- feols(log_price ~ i(k, ref = -1) | model + month, data = es_dev, cluster = ~lab)
png("output/fig_catchup_event_study.png", 1400, 900, res = 200)
iplot(h1a_es, xlab = "Months relative to loss of lead", ylab = "Log price")
dev.off()

## --- H1b: launch price on lead at launch ----------------------------
h1b <- feols(log_launch_price ~ lead_at_launch, data = lnch, cluster = ~lab)
h1b_boot <- boottest(h1b, param = "lead_at_launch", clustid = "lab", B = 9999, type = "webb")
cat("H1b: beta =", coef(h1b)["lead_at_launch"], " wild-boot p =", h1b_boot$p_val, "\n")

## ===================================================================
## 7.2  Adopter side
## ===================================================================

## --- H2: pooled exposure does not predict margin --------------------
h2 <- feols(op_margin ~ exposure | fy + sic2, data = filter(ad, treated == 0),
            cluster = ~firm)
print(summary(h2))   # report coefficient, SE, p-value

## --- H3 baseline: TWFE ----------------------------------------------
twfe <- feols(op_margin ~ post | firm + fy, data = ad, cluster = ~firm)

## --- H3 heterogeneity-robust: Sun & Abraham (fixest) ----------------
ad <- ad |> mutate(cohort = ifelse(treated == 1, ga_year, 10000))  # never-treated = 10000
sa <- feols(op_margin ~ sunab(cohort, fy) | firm + fy, data = ad, cluster = ~firm)
cat("\nSun-Abraham ATT:\n"); print(summary(sa, agg = "att"))

## --- H3 heterogeneity-robust: Callaway & Sant'Anna ------------------
ad_did <- ad |> mutate(id = as.integer(factor(firm)),
                       g  = ifelse(treated == 1, ga_year, 0))
cs_never <- att_gt(yname = "op_margin", tname = "fy", idname = "id", gname = "g",
                   data = as.data.frame(ad_did), control_group = "nevertreated",
                   est_method = "reg", base_period = "universal")
cs_nyt   <- att_gt(yname = "op_margin", tname = "fy", idname = "id", gname = "g",
                   data = as.data.frame(ad_did), control_group = "notyettreated",
                   est_method = "reg", base_period = "universal")
cat("\nCS overall ATT (never-treated):\n"); print(aggte(cs_never, type = "simple"))
cat("CS overall ATT (not-yet-treated):\n"); print(aggte(cs_nyt,   type = "simple"))
cs_dyn <- aggte(cs_never, type = "dynamic", min_e = -3, max_e = 3)
png("output/fig_cs_dynamic.png", 1400, 900, res = 200); print(ggdid(cs_dyn)); dev.off()

## --- Alternative controls -------------------------------------------
m_sicyr  <- feols(op_margin ~ post | firm + fy^sic2, data = ad, cluster = ~firm)
m_trend  <- feols(op_margin ~ post | firm + fy + firm[fy], data = ad, cluster = ~firm)

## Matched never-treated controls: exact on sic2, nearest on pre-2023 level/trend/size
firms <- ad |> distinct(firm, treated, sic2, size_pre, margin_pre, trend_pre)
mt <- matchit(treated ~ margin_pre + trend_pre + log(size_pre) + sic2,
              data = firms, method = "nearest", exact = ~sic2, ratio = 2,
              replace = TRUE)
md <- match.data(mt) |> select(firm, weights)
m_match <- feols(op_margin ~ post | firm + fy, data = inner_join(ad, md, by = "firm"),
                 weights = ~weights, cluster = ~firm)

## --- Placebo: GA date moved two years earlier -----------------------
ad_pl <- ad |> mutate(post_pl = as.integer(treated == 1 & fy >= (ga_year - 2)))
m_placebo <- feols(op_margin ~ post_pl | firm + fy,
                   data = filter(ad_pl, is.na(ga_year) | fy < ga_year), cluster = ~firm)
## (sample cut at the true GA year so the placebo is not contaminated by treatment)

## --- Randomization inference: reassign GA years across firms --------
ri_B <- 2000
obs  <- coef(twfe)["post"]
treated_firms <- unique(ad$firm[ad$treated == 1])
all_firms     <- unique(ad$firm)
ga_pool       <- ad |> filter(treated == 1) |> distinct(firm, ga_year)
ri_beta <- replicate(ri_B, {
  new_t <- sample(all_firms, length(treated_firms))
  map   <- data.frame(firm = new_t, ga_new = sample(ga_pool$ga_year))
  d <- ad |> select(-ga_year) |> left_join(map, by = "firm") |>
    mutate(post_ri = as.integer(!is.na(ga_new) & fy >= ga_new))
  coef(feols(op_margin ~ post_ri | firm + fy, data = d))["post_ri"]
})
ri_p <- mean(abs(ri_beta) >= abs(obs))
cat("\nRandomization-inference p =", ri_p, "\n")

## --- Decomposition: gross margin vs. opex ratio; size heterogeneity --
ad <- ad |> mutate(large = as.integer(size_pre >= median(size_pre[treated == 1], na.rm = TRUE)))
dec <- list(
  op_margin    = feols(op_margin    ~ post | firm + fy, data = ad, cluster = ~firm),
  gross_margin = feols(gross_margin ~ post | firm + fy, data = ad, cluster = ~firm),
  opex_ratio   = feols(opex_ratio   ~ post | firm + fy, data = ad, cluster = ~firm))
het <- feols(op_margin ~ post + post:large | firm + fy, data = ad, cluster = ~firm)

## --- Table of H3 robustness ------------------------------------------
etable(twfe, sa, m_sicyr, m_trend, m_match, m_placebo, dec$gross_margin, dec$opex_ratio, het,
       headers = c("TWFE","Sun-Abraham","SIC x year","Firm trends","Matched",
                   "Placebo (-2y)","Gross margin","Opex ratio","By size"),
       file = "output/tab_h3_robustness.tex", replace = TRUE)

## ===================================================================
## H4: event-time path and the direct tests
## ===================================================================
cnt <- ad |> filter(treated == 1) |> count(event_time) |> filter(n >= 8)
keep <- cnt$event_time
es <- feols(op_margin ~ i(event_time, ref = -1) | firm + fy,
            data = filter(ad, treated == 0 | event_time %in% keep), cluster = ~firm)
print(summary(es))
png("output/fig_event_study.png", 1400, 900, res = 200)
iplot(es, xlab = "Event time (years from GA)", ylab = "Operating margin (pp)")
dev.off()

## Joint test of pre-GA coefficients (excluding the omitted t = -1)
print(wald(es, "event_time::-([2-9])$"))   # regex over pre-GA coefficients; skip if none estimated

## Direct test of H4: beta(+1) = beta(last post-GA bin)
post_k <- sort(keep[keep >= 1]); last_k <- max(post_k)
nm1 <- paste0("event_time::", 1); nmL <- paste0("event_time::", last_k)
b <- coef(es); V <- vcov(es)
diff <- b[nm1] - b[nmL]
se   <- sqrt(V[nm1, nm1] + V[nmL, nmL] - 2 * V[nm1, nmL])
cat(sprintf("\nH4: beta(+1) - beta(+%d) = %.3f (se %.3f), p = %.3f\n",
            last_k, diff, se, 2 * pnorm(-abs(diff / se))))
## Under H4 the difference should be positive and significant.
## With few clusters the cluster-robust normal p-value is optimistic;
## cross-check with a wild bootstrap of the contrast (e.g. boottest with R = c(1,-1)).
