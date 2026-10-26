# Study 4: public-data comparison for the Poisson-SNS manuscript

Implementation of the Study 1 scheduler comparison (IPP / HPP / polling) from the manuscript specification, compared
with public activity data.

| File | Purpose |
| --- | --- |
| `poisson_sns.py` | Event-driven simulator (Section III, Appendix A). The surrogate oracle's form is not specified in the manuscript; its intercept is calibrated by `calibrate.py` (b0 = -2.87) to about 14,830 events per 24 h. |
| `calibrate.py`, `run_sim.py` | Calibration and the 5-replication, 72 h runs for the three schedulers (`sim_study1.pkl`). |
| `extract_bluesky.py` | Decodes TID record keys of the 12.1M-post Bluesky sample (`midwestern-simulation/12.1m_bluesky_posts` on Hugging Face) to creation times and parent creation times. |
| `extract_stackexchange.py` | Hour-of-day and comment-delay references from the Stack Exchange dump (Money, Law, Workplace; `archive.org/details/stackexchange`). |
| `analyze.py`, `make_figure.py` | Metrics (`study1_real_validation.json`) and Fig. 4. |
| `study4_text.py`, `build_manuscript.py`, `build_access_template.py` | Add Study 4 to the manuscript and pour it into the official IEEE Access Word template. |

Raw data are not committed. Paths in the scripts point to a scratch directory and need adjusting.
