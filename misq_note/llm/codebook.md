# Codebook (used identically by LLM coders and human coders)

For each review return one JSON object:

- `rid`: copy from input.
- `overall`: overall sentiment of the reviewer toward the product: `neg`, `neu`, `pos`. Judge from the text only.
- `defect`: `1` if the reviewer reports a product failure, malfunction, defect, or damaged/incorrect item; else `0`.
- Seven aspects. Each takes `0` (not mentioned), `-1` (mentioned negatively), `1` (mentioned positively), or `2` (mentioned, neutral or mixed):
  - `price`: price, cost, value for money
  - `durability`: durability, build quality, longevity, reliability over time
  - `battery`: battery life, power, charging, shelf life of batteries
  - `performance`: how well it works; speed, picture/sound, functionality
  - `ease`: ease of use, setup, interface, learning curve
  - `design`: size, weight, look, screen size, portability
  - `service`: shipping, packaging, seller/customer service, returns, warranty
