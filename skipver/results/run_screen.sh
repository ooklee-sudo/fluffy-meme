cd /home/user/fluffy-meme/skipver
for m in ministral8b llama31_8b gemini31fl gemma3_12b gpt5nano qwen3_14b opus55; do
  python3 run.py screen_bal --only $m --workers 6 > results/screen_$m.log 2>&1 &
done
wait; echo ALLDONE
