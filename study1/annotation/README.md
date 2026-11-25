# Human annotation kit (Study 1 validation)
Two blind sheets; model outputs are withheld.
- photo_pairs_to_annotate.csv (300 pairs): for each attribute write A or B (which photo shows the HIGHER level; photographic_quality = technical quality). Order is randomized. Open the photo URLs (Airbnb CDN) to view; do not redistribute images.
- reviews_to_annotate.csv (400 reviews): per attribute write 1 (positive), 0 (neutral/mixed), -1 (negative) or leave blank if not mentioned.
Use at least two independent annotators; keep each annotator's sheet separate (suffix _annotatorN). Then compute Krippendorff's alpha vs. the models and use the labels as the validation sample for prediction-powered inference.
