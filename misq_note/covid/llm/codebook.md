# Codebook (restaurant v1; used identically by LLM coders and human coders)

For each review return one record:

- `rid`: copy from input.
- `overall`: overall sentiment of the reviewer toward the restaurant visit/order: `neg`, `neu`, `pos`. Judge from the text only.
- Six aspects. Each takes `0` (not mentioned), `-1` (mentioned negatively), `1` (mentioned positively), or `2` (mentioned, neutral or mixed):
  - `safety`: COVID safety, masks, distancing, sanitation, health rules, cleanliness related to infection
  - `takeout`: takeout, to-go, delivery, curbside, drive-through, third-party delivery apps
  - `service`: staff, friendliness, speed of service, waiting time
  - `price`: price, value for money, fees
  - `food`: taste, quality, portion size, freshness
  - `space`: seating, atmosphere, noise, crowding, indoor or outdoor space
