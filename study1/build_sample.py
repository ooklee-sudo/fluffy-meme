"""Study 1, step 1: build the listing-level analysis frame from Inside Airbnb snapshots.

Usage: python build_sample.py DATA_DIR OUT_CSV
DATA_DIR holds {ams,lon,nyc,tok}_listings.csv.gz as downloaded from insideairbnb.com.
Filters follow Section 5.1 of the manuscript, except that the English-review count is
applied in a later step (needs language detection on review text).
"""
import sys, numpy as np, pandas as pd
from sklearn.neighbors import BallTree

CITIES = {"ams": "Amsterdam", "lon": "London", "nyc": "New York City", "tok": "Tokyo"}
KEEP_ROOMS = {"Entire home/apt", "Private room"}

def load(data_dir, key):
    d = pd.read_csv(f"{data_dir}/{key}_listings.csv.gz", low_memory=False)
    d["city"] = CITIES[key]
    return d

def competitor_density(d, radius_m=500):
    # Count other listings (same city, all room types in the raw snapshot) within radius.
    rad = np.radians(d[["latitude", "longitude"]].to_numpy())
    tree = BallTree(rad, metric="haversine")
    cnt = tree.query_radius(rad, r=radius_m / 6371000.0, count_only=True) - 1
    return cnt

def main(data_dir, out):
    frames, log = [], []
    for key in CITIES:
        d = load(data_dir, key)
        n0 = len(d)
        d["comp_density_500m"] = competitor_density(d)
        d = d[d.room_type.isin(KEEP_ROOMS)]; n1 = len(d)
        d = d[d.picture_url.notna()]; n2 = len(d)
        d = d[d.number_of_reviews >= 5]; n3 = len(d)
        log.append((CITIES[key], n0, n1, n2, n3))
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["price_num"] = pd.to_numeric(df.price_quote_price_per_night, errors="coerce")
    df["is_bookable"] = (df.has_availability == "t") & df.price_num.notna()
    df["superhost"] = (df.host_is_superhost == "t").astype(int)
    df["multi_listing_host"] = (df.calculated_host_listings_count > 1).astype(int)
    df["host_tenure_yrs"] = pd.to_numeric(df.hosts_time_as_host_years, errors="coerce")
    df["ln_reviews"] = np.log(df.number_of_reviews)
    df["ln_comp_density_500m"] = np.log1p(df.comp_density_500m)
    df["ln_price"] = np.log(df.price_num.where(df.price_num > 0))
    cols = ["id", "city", "neighbourhood_cleansed", "room_type", "accommodates", "bedrooms",
            "superhost", "multi_listing_host", "host_tenure_yrs", "number_of_reviews", "ln_reviews",
            "comp_density_500m", "ln_comp_density_500m", "is_bookable", "price_quote_checkin_date",
            "price_num", "ln_price", "review_scores_accuracy", "review_scores_cleanliness",
            "picture_url", "first_review", "last_review"]
    df[cols].to_csv(out, index=False)
    print(pd.DataFrame(log, columns=["city", "raw", "entire/private", "has photo", ">=5 reviews"]).to_string(index=False))
    print("sample", len(df), "bookable", int(df.is_bookable.sum()))
    print("missing price share", round(1 - df.is_bookable.mean(), 3))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
