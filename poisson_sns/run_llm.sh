set -e
python3 seeding.py --reps 30 --provider llm --out results/seeding_llm.json > /dev/null
python3 seeding.py --reps 30 --provider surrogate-table --out results/seeding_surrogate_table.json > /dev/null
python3 validate.py --reps 5 --provider llm --out results/validate_llm.json > /dev/null
python3 validate.py --reps 5 --provider surrogate-table --out results/validate_surrogate_table.json > /dev/null
touch results/.llm_done
