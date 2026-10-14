#!/bin/bash
# download state series from FRED; usage: fetch2.sh OUTDIR
O=$1; mkdir -p $O
tail -n +2 SERIES_LIST.csv | while IFS=, read ab fips rest nf pov inc; do
 for s in $rest $nf $pov $inc ${ab}POP; do
  f=$O/$s.csv; [ -s $f ] && continue
  for k in 1 2 3 4; do
   curl -sS -m 25 -o $f.tmp "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$s" && head -c 16 $f.tmp | grep -q observation_date && mv $f.tmp $f && break
   rm -f $f.tmp; sleep 2
  done
 done
done
echo FINISHED
