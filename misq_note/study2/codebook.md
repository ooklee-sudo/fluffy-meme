# Codebook v2 (appliances; used identically by LLM coders and human coders)

For each review return one record:

- `rid`: copy from input.
- `overall`: overall sentiment of the reviewer toward the product: `neg`, `neu`, `pos`. Judge from the text only.
- `defect`: `1` if the reviewer reports a product failure, malfunction, defect, or damaged/incorrect/wrong item; else `0`.
- Seven aspects. Each takes `0` (not mentioned), `-1` (mentioned negatively), `1` (mentioned positively), or `2` (mentioned, neutral or mixed):
  - `price`: price, cost, value for money
  - `durability`: durability, build quality, longevity, reliability over time
  - `performance`: how well it works; does the job, power, effectiveness, noise level
  - `fit`: fit, compatibility, size match, matches the model/part number or description
  - `ease`: ease of installation or use, instructions, learning curve
  - `design`: look, finish, size, weight, portability
  - `service`: shipping, packaging, seller/customer service, returns, warranty
