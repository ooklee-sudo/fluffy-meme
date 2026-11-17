# Data source and license

This project uses **Customer Support on Twitter** (TWCS) by Thought Vector (Stuart Axelbrooke), published on
Kaggle in 2017: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter

The dataset is licensed under **CC BY-NC-SA 4.0** (https://creativecommons.org/licenses/by-nc-sa/4.0/), as
stated on its Kaggle page (checked 2026-11-17).

The copy used here is `twcs.csv` (516,508,641 bytes; SHA-256
`cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0`; 2,811,774 tweets), obtained from the
Hugging Face mirror `SunidhiSriram/twcs`. Its structure matches the Kaggle description (7 columns, unique tweet
IDs, anonymized customer IDs, masked e-mail and card numbers).

## Material derived from TWCS in this repository

Some files under `tt_entropy/results/` (for example `h5_gen/`) contain excerpts of TWCS tweets (customer
messages and brand replies) and model replies generated from them. Those excerpts and derived files are shared
under the same license, **CC BY-NC-SA 4.0**, with attribution to the source above. Changes: tweets were paired
into customer-message / brand-reply pairs, grouped by brand, split into training and evaluation sets, and used
as model inputs.

Use is limited to non-commercial purposes. Tweet text also remains subject to the rights of its authors and
X/Twitter's terms; for redistribution beyond research, use the tweet IDs and rebuild the data from the Kaggle
original with `tt_entropy/data.py`.

The project's code is separate from the data and is not covered by this notice. `tt_entropy/adapters.py`
contains a port of QuanTA (https://github.com/quanta-fine-tuning/quanta, Apache-2.0).
