cd /home/user/fluffy-meme/skipver
for s in study2_bal study3_bal study4_bal study5_bal floor_bal; do python3 run.py $s --workers 20 || echo "FAILED $s"; done
echo ALLDONE
