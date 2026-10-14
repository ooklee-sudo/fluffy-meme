#!/bin/bash
# usage: fetch_duka2.sh SYMBOL OUTDIR TODOFILE PARALLEL
SYM=$1; OUT=$2; TODO=$3; P=${4:-3}; export SYM OUT
cat "$TODO" | xargs -P "$P" -L 1 bash -c '
y=$0; m=$1; dd=$2; h=$3; tag=$4; f="$OUT/${tag}_${h}.bi5"
if [ -s "$f" ] || [ -e "$f.empty" ]; then exit 0; fi
for i in 1 2 3 4 5; do
  code=$(curl -sS -m 25 -A Mozilla/5.0 -o "$f.tmp" -w "%{http_code}" "https://datafeed.dukascopy.com/datafeed/$SYM/$y/$m/$dd/${h}h_ticks.bi5" 2>/dev/null)
  if [ "$code" = "200" ]; then if [ -s "$f.tmp" ]; then mv "$f.tmp" "$f"; else rm -f "$f.tmp"; touch "$f.empty"; fi; exit 0; fi
  if [ "$code" = "404" ]; then rm -f "$f.tmp"; touch "$f.empty"; exit 0; fi
  sleep $((i*2))
done
rm -f "$f.tmp"; echo "FAIL $f" >> "$OUT/_fail.txt"
'
echo done > "$OUT/_done2"
