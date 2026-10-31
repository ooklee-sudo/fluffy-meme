#!/usr/bin/env bash
# Full pipeline, run from the package root:  bash run_all.sh [--collect]
# Without --collect, only the analysis steps are run; they need the raw data in data/raw (see README, section 4).
set -e
export PYTHONWARNINGS=ignore
if [ "$1" == "--collect" ]; then
  for s in 01_prices_yahoo 02_sec_alphabet_search_revenue 03_sec_meta_revenue_xbrl 04_build_quarterly \
           05_sec_alphabet_paid_clicks 06_sec_microsoft_search_revenue 06b_sec_microsoft_search_revenue_2026 \
           07_google_trends_states 08_google_trends_chatgpt_by_state 09_google_trends_chatgpt_by_country \
           11_eurostat 12_statcounter 13_worldbank_covariates; do
    echo "== 01_data_collection/$s.py"; python3 01_data_collection/$s.py
  done
  for v in main extra eu; do python3 01_data_collection/10_wikimedia_projectviews_monthly.py $v; done
  # data/trust/hours.csv is distributed; uncomment to rebuild it
  # python3 01_data_collection/14_wikimedia_trust_hours.py
fi
mkdir -p logs
run(){ echo "== $1"; python3 "$@" > "logs/$(basename $1 .py)${2:+_$2}.log" 2>&1; }
run 02_analysis/t04a_test_a_google_trends_states.py
run 02_analysis/t04b_test_b_eurostat_wikipedia.py
run 02_analysis/t04b2_test_b_worldwide_trends.py
bash 02_analysis/run_t04c.sh > logs/t04c_test_c_callaway_santanna.log 2>&1
run 02_analysis/t05_event_study.py
run 02_analysis/t05b_event_study_robustness.py
run 02_analysis/t06_quarterly_regressions.py
run 02_analysis/t07_placebo_breaks.py
run 02_analysis/t08_cpc_regressions.py
run 02_analysis/t09_bing_share.py
run 02_analysis/t09b_bing_revenue_and_events.py
run 02_analysis/t10_engine_formats.py
run 02_analysis/t11_spearman_share_timing.py
run 02_analysis/t12_prop9_regressions.py
run 02_analysis/t13_legacy_revenue.py
run 02_analysis/t14_google_ai_mode_countries.py
run 02_analysis/t15_trust_shock.py
run 02_analysis/t15a_trust_shock_all_editions_prelim.py
for f in f1_aio_event_study f2_quarterly_growth f3_paid_clicks_cpc f4_bing_share f5_trust_shock_gap; do run 02_analysis/$f.py; done
for f in prop8_numerical_check prop9_numerical_example prop10_trust_traps; do run 03_model/$f.py; done
echo "done; see logs/ and output/"
