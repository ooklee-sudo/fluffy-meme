::: {custom-style="Title"}
Online Appendix to "Synthetic Customers as Decision-Support Artifacts: Design Constraints, Calibration, and Accountability in Generative-AI Marketing Analytics"
:::

# Appendix A. Prompt Templates {-}

Persona text, low-mean setting: "You are a customer of an online giftware retailer. Profile: {segment}, age {age}, based in {country}. You made your first purchase 4 weeks ago." Anchored variant adds: "Context: customers of this retailer make on average about 0.5 purchases per 4 weeks, and most make none."

Persona text, high-mean setting: "You are a household with a loyalty card at a supermarket chain and you do part of your grocery shopping there. Profile: {segment}, head of household aged {age}, {household size} person(s)." Anchored variant adds: "Context: households in this loyalty program make on average about 5 shopping trips to the chain per 4 weeks, and some make none."

Questions. Design A: "How many separate purchases will you make in the next 4 weeks? Answer with ONLY an integer." Design B: "Week {w} of the next 4 weeks: for each of its 7 days decide whether you make a purchase that day. Reply with ONLY 7 comma-separated 0/1 values." Design C: "Give the probabilities of making {bins} purchases in the next 4 weeks. Reply with ONLY JSON like {...} summing to 1." Design D: "What is your expected average number of purchases per 4 weeks (can be fractional, e.g. 0.4)? Reply with ONLY a number." Email experiment: persona from the customer's recency, 12-month spend, merchandise bought, area, new or existing status, and channel, followed by one of three sentences describing the email received, and "What is the probability, from 0 to 100 percent, that you will {visit the retailer's website / make a purchase from the retailer} during the next two weeks? Reply with ONLY a number."

# Appendix B. Full Results {-}

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 0.49 | 2.49 | 0.74 | 3.05 |
| GPT-4o-mini | plain | A Direct | 1.92\* | 0.25\* | 0.00\* | -0.39\* |
| GPT-4o-mini | plain | B Daily | 13.56\* | 0.24\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 1.30\* | 1.21\* | 0.32\* | 0.16\* |
| GPT-4o-mini | plain | D Hybrid | 0.43\* | 2.19 | 0.73 | 2.79 |
| GPT-4o-mini | anchored | A Direct | 1.00\* | 0.00\* | 0.00\* | -1.00\* |
| GPT-4o-mini | anchored | B Daily | 5.07\* | 0.33\* | 0.00\* | -0.13\* |
| GPT-4o-mini | anchored | C Describe | 0.37\* | 1.17\* | 0.71\* | 0.46\* |
| GPT-4o-mini | anchored | D Hybrid | 0.59\* | 2.19\* | 0.70\* | 2.01\* |
| Llama-3.3-70B | plain | A Direct | 0.96\* | 0.56\* | 0.29\* | -0.46\* |
| Llama-3.3-70B | plain | B Daily | 3.13\* | 0.38\* | 0.03\* | -0.20\* |
| Llama-3.3-70B | plain | C Describe | 0.98\* | 1.61\* | 0.47\* | 0.62\* |
| Llama-3.3-70B | plain | D Hybrid | 0.42\* | 2.03\* | 0.75 | 2.43 |
| Llama-3.3-70B | anchored | A Direct | 0.00\* | 1.00\* | 1.00\* | 0.00\* |
| Llama-3.3-70B | anchored | B Daily | 0.59\* | 1.24\* | 0.62\* | 0.41\* |
| Llama-3.3-70B | anchored | C Describe | 0.40\* | 1.08\* | 0.67\* | 0.19\* |
| Llama-3.3-70B | anchored | D Hybrid | 0.93\* | 3.38\* | 0.63\* | 2.57 |
| Haiku 5.5 | plain | A Direct | 1.64\* | 0.19\* | 0.00\* | -0.49\* |
| Haiku 5.5 | plain | B Daily | 5.90\* | 0.89\* | 0.01\* | -0.02\* |
| Haiku 5.5 | plain | C Describe | 0.85\* | 1.60\* | 0.52\* | 0.70\* |
| Haiku 5.5 | plain | D Hybrid | 0.65\* | 2.90 | 0.69\* | 2.95 |
| Haiku 5.5 | anchored | A Direct | 0.74\* | 0.26\* | 0.26\* | -1.00\* |
| Haiku 5.5 | anchored | B Daily | 2.10\* | 1.14\* | 0.27\* | 0.07\* |
| Haiku 5.5 | anchored | C Describe | 0.43 | 1.34\* | 0.69\* | 0.80\* |
| Haiku 5.5 | anchored | D Hybrid | 0.49 | 2.04\* | 0.72 | 2.09\* |
| Sonnet 5 | plain | A Direct | 1.37\* | 0.87\* | 0.29\* | -0.10\* |
| Sonnet 5 | plain | B Daily | 3.13\* | 2.95\* | 0.38\* | 0.62\* |
| Sonnet 5 | plain | C Describe | 0.72\* | 1.57\* | 0.59\* | 0.79\* |
| Sonnet 5 | plain | D Hybrid | 0.47 | 2.37 | 0.72 | 2.93 |
| Sonnet 5 | anchored | A Direct | 0.01\* | 0.99\* | 0.99\* | -0.88\* |
| Sonnet 5 | anchored | B Daily | 0.00\* | n/a | 1.00\* | n/a |
| Sonnet 5 | anchored | C Describe | 0.47 | 1.30\* | 0.67\* | 0.63\* |
| Sonnet 5 | anchored | D Hybrid | 0.39\* | 2.46 | 0.77 | 3.74 |
| GPT-5.6-terra | plain | A Direct | 0.69\* | 0.51\* | 0.38\* | -0.71\* |
| GPT-5.6-terra | plain | B Daily | 1.60\* | 1.15\* | 0.32\* | 0.09\* |
| GPT-5.6-terra | plain | C Describe | 0.51 | 1.25\* | 0.64\* | 0.50\* |
| GPT-5.6-terra | plain | D Hybrid | 0.56 | 3.09 | 0.72 | 3.77 |
| GPT-5.6-terra | anchored | A Direct | 0.26\* | 0.74\* | 0.74 | -1.00\* |
| GPT-5.6-terra | anchored | B Daily | 0.01\* | 0.99\* | 0.99\* | -0.86\* |
| GPT-5.6-terra | anchored | C Describe | 0.48 | 1.03\* | 0.62\* | 0.07\* |
| GPT-5.6-terra | anchored | D Hybrid | 0.56 | 2.37 | 0.71 | 2.42 |
| DeepSeek-V4-Pro | plain | A Direct | 2.10\* | 14.72\* | 0.52\* | 6.54 |
| DeepSeek-V4-Pro | plain | B Daily | 4.73\* | 1.00\* | 0.02\* | 0.00\* |
| DeepSeek-V4-Pro | plain | C Describe | 0.59\* | 1.34\* | 0.60\* | 0.57\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 0.43 | 2.40 | 0.76 | 3.22 |
| DeepSeek-V4-Pro | anchored | A Direct | 0.36\* | 0.95\* | 0.67\* | -0.13\* |
| DeepSeek-V4-Pro | anchored | B Daily | 0.50 | 0.81\* | 0.57\* | -0.37\* |
| DeepSeek-V4-Pro | anchored | C Describe | 0.54 | 1.04\* | 0.59\* | 0.07\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 0.61\* | 2.52 | 0.69\* | 2.49 |
| Gemini 3.1 Flash-Lite | plain | A Direct | 1.05\* | 0.59\* | 0.29\* | -0.39\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 3.51\* | 0.35\* | 0.03\* | -0.18\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 0.49 | 1.26\* | 0.65\* | 0.53\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 0.28\* | 1.62\* | 0.81\* | 2.27 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 0.30\* | 0.70\* | 0.69\* | -1.00\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 1.45\* | 1.15\* | 0.35\* | 0.10\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 0.52 | 0.97\* | 0.59\* | -0.06\* |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 0.59\* | 2.61 | 0.71 | 2.74 |
| Mistral Large 4 | plain | A Direct | 1.04\* | 0.64\* | 0.27\* | -0.35\* |
| Mistral Large 4 | plain | B Daily | 5.06\* | 0.95\* | 0.00\* | -0.01\* |
| Mistral Large 4 | plain | C Describe | 0.96\* | 1.37\* | 0.45\* | 0.39\* |
| Mistral Large 4 | plain | D Hybrid | 0.26\* | 1.47\* | 0.81\* | 1.81\* |
| Mistral Large 4 | anchored | A Direct | 0.01\* | 0.99\* | 0.98\* | -0.89\* |
| Mistral Large 4 | anchored | B Daily | 0.48 | 0.99\* | 0.63\* | -0.03\* |
| Mistral Large 4 | anchored | C Describe | 0.56\* | 1.13\* | 0.59\* | 0.23\* |
| Mistral Large 4 | anchored | D Hybrid | 0.47 | 2.05 | 0.71 | 2.25 |

*Table B1. Low-mean setting, per cell. Reference row: negative binomial with mean 0.49 and alpha 3.05. \* the 95% bootstrap interval excludes the reference value. Temperatures are pooled for GPT-4o-mini and Llama.*

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 4.84 | 7.85 | 0.19 | 1.42 |
| GPT-4o-mini | plain | A Direct | 8.00\* | 0.01\* | 0.00\* | -0.12\* |
| GPT-4o-mini | plain | B Daily | 16.45\* | 0.05\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 5.68\* | 5.37\* | 0.10\* | 0.77\* |
| GPT-4o-mini | plain | D Hybrid | 6.56\* | 9.02 | 0.18 | 1.22 |
| GPT-4o-mini | anchored | A Direct | 5.00\* | 0.00\* | 0.00\* | -0.20\* |
| GPT-4o-mini | anchored | B Daily | 16.65\* | 0.08\* | 0.00\* | -0.06\* |
| GPT-4o-mini | anchored | C Describe | 5.46\* | 6.44\* | 0.13\* | 1.00\* |
| GPT-4o-mini | anchored | D Hybrid | 5.33 | 8.73 | 0.21 | 1.45 |
| Llama-3.3-70B | plain | A Direct | 8.00\* | 0.00\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | plain | B Daily | 9.86\* | 0.23\* | 0.00\* | -0.08\* |
| Llama-3.3-70B | plain | C Describe | 7.32\* | 4.85\* | 0.03\* | 0.53\* |
| Llama-3.3-70B | plain | D Hybrid | 6.06\* | 9.06 | 0.22 | 1.33 |
| Llama-3.3-70B | anchored | A Direct | 3.73\* | 0.27\* | 0.02\* | -0.20\* |
| Llama-3.3-70B | anchored | B Daily | 7.03\* | 0.19\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | anchored | C Describe | 6.49\* | 5.76\* | 0.05\* | 0.73\* |
| Llama-3.3-70B | anchored | D Hybrid | 4.26\* | 5.90 | 0.14\* | 1.15 |
| Haiku 5.5 | plain | A Direct | 7.71\* | 0.24\* | 0.00\* | -0.10\* |
| Haiku 5.5 | plain | B Daily | 9.93\* | 0.25\* | 0.00\* | -0.08\* |
| Haiku 5.5 | plain | C Describe | 6.16\* | 4.13\* | 0.01\* | 0.51\* |
| Haiku 5.5 | plain | D Hybrid | 4.81 | 7.48 | 0.20 | 1.35 |
| Haiku 5.5 | anchored | A Direct | 4.48\* | 0.11\* | 0.00\* | -0.20\* |
| Haiku 5.5 | anchored | B Daily | 9.47\* | 0.19\* | 0.00\* | -0.09\* |
| Haiku 5.5 | anchored | C Describe | 5.66\* | 5.82\* | 0.12\* | 0.85\* |
| Haiku 5.5 | anchored | D Hybrid | 3.66\* | 5.84\* | 0.26\* | 1.32 |
| Sonnet 5 | plain | A Direct | 8.02\* | 0.36\* | 0.00\* | -0.08\* |
| Sonnet 5 | plain | B Daily | 10.30\* | 0.16\* | 0.00\* | -0.08\* |
| Sonnet 5 | plain | C Describe | 7.15\* | 4.57\* | 0.04\* | 0.50\* |
| Sonnet 5 | plain | D Hybrid | 5.58\* | 8.99 | 0.21 | 1.43 |
| Sonnet 5 | anchored | A Direct | 4.99\* | 0.03\* | 0.00\* | -0.19\* |
| Sonnet 5 | anchored | B Daily | 8.21\* | 0.04\* | 0.00\* | -0.12\* |
| Sonnet 5 | anchored | C Describe | 5.04 | 4.42\* | 0.10\* | 0.68\* |
| Sonnet 5 | anchored | D Hybrid | 5.47\* | 8.99 | 0.22 | 1.46 |
| GPT-5.6-terra | plain | A Direct | 7.68\* | 0.15\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | B Daily | 8.37\* | 0.10\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | C Describe | 6.76\* | 4.86\* | 0.05\* | 0.57\* |
| GPT-5.6-terra | plain | D Hybrid | 5.51\* | 8.72 | 0.22 | 1.40 |
| GPT-5.6-terra | anchored | A Direct | 4.88\* | 0.02\* | 0.00\* | -0.20\* |
| GPT-5.6-terra | anchored | B Daily | 4.35\* | 0.12\* | 0.00\* | -0.20\* |
| GPT-5.6-terra | anchored | C Describe | 5.78\* | 4.12\* | 0.08\* | 0.54\* |
| GPT-5.6-terra | anchored | D Hybrid | 5.02 | 8.62 | 0.23\* | 1.52 |
| DeepSeek-V4-Pro | plain | A Direct | 7.77\* | 1.10\* | 0.00\* | 0.01\* |
| DeepSeek-V4-Pro | plain | B Daily | 8.94\* | 0.19\* | 0.00\* | -0.09\* |
| DeepSeek-V4-Pro | plain | C Describe | 5.81\* | 4.28\* | 0.03\* | 0.57\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 7.65\* | 9.43 | 0.13\* | 1.10\* |
| DeepSeek-V4-Pro | anchored | A Direct | 5.22\* | 1.57\* | 0.01\* | 0.11\* |
| DeepSeek-V4-Pro | anchored | B Daily | 6.83\* | 0.38\* | 0.00\* | -0.09\* |
| DeepSeek-V4-Pro | anchored | C Describe | 5.33\* | 4.77\* | 0.06\* | 0.71\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 6.42\* | 7.61 | 0.16\* | 1.03\* |
| Gemini 3.1 Flash-Lite | plain | A Direct | 11.74\* | 0.35\* | 0.00\* | -0.06\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 8.21\* | 0.04\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 6.50\* | 3.65\* | 0.02\* | 0.41\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 8.69\* | 12.15\* | 0.14\* | 1.28 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 5.13\* | 0.06\* | 0.00\* | -0.18\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 7.48\* | 0.09\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 4.23\* | 3.75\* | 0.14\* | 0.65\* |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 4.81 | 6.95 | 0.23\* | 1.24 |
| Mistral Large 4 | plain | A Direct | 8.56\* | 2.45\* | 0.00\* | 0.17\* |
| Mistral Large 4 | plain | B Daily | 8.28\* | 0.05\* | 0.00\* | -0.12\* |
| Mistral Large 4 | plain | C Describe | 7.95\* | 4.75\* | 0.03\* | 0.47\* |
| Mistral Large 4 | plain | D Hybrid | 4.36\* | 6.42\* | 0.22 | 1.24 |
| Mistral Large 4 | anchored | A Direct | 4.90\* | 0.02\* | 0.00\* | -0.20\* |
| Mistral Large 4 | anchored | B Daily | 8.26\* | 0.04\* | 0.00\* | -0.12\* |
| Mistral Large 4 | anchored | C Describe | 4.98 | 4.83\* | 0.15\* | 0.77\* |
| Mistral Large 4 | anchored | D Hybrid | 3.63\* | 6.09\* | 0.27\* | 1.40 |

*Table B2. High-mean setting, 600 customers per cell. Reference row: empirical Complete Journey distribution. \* the 95% bootstrap interval excludes the reference value.*

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 7.83 | 6.52 | 0.03 | 0.71 |
| GPT-4o-mini | plain | A Direct | 7.96\* | 0.02\* | 0.00\* | -0.12\* |
| GPT-4o-mini | plain | B Daily | 16.58\* | 0.07\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 6.02\* | 5.78 | 0.09\* | 0.79 |
| GPT-4o-mini | plain | D Hybrid | 6.46\* | 5.68 | 0.08\* | 0.72 |
| GPT-4o-mini | anchored | A Direct | 8.00\* | 0.00\* | 0.00\* | -0.12\* |
| GPT-4o-mini | anchored | B Daily | 17.21\* | 0.13\* | 0.00\* | -0.05\* |
| GPT-4o-mini | anchored | C Describe | 6.56\* | 5.22\* | 0.10\* | 0.64 |
| GPT-4o-mini | anchored | D Hybrid | 7.53 | 6.35 | 0.07\* | 0.71 |
| Llama-3.3-70B | plain | A Direct | 7.98\* | 0.00\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | plain | B Daily | 9.04\* | 0.18\* | 0.00\* | -0.09\* |
| Llama-3.3-70B | plain | C Describe | 6.80\* | 5.01\* | 0.03 | 0.59\* |
| Llama-3.3-70B | plain | D Hybrid | 4.91\* | 4.60\* | 0.12\* | 0.73 |
| Llama-3.3-70B | anchored | A Direct | 6.05\* | 0.03\* | 0.00\* | -0.16\* |
| Llama-3.3-70B | anchored | B Daily | 8.12\* | 0.13\* | 0.00\* | -0.11\* |
| Llama-3.3-70B | anchored | C Describe | 7.54 | 6.04 | 0.05 | 0.67 |
| Llama-3.3-70B | anchored | D Hybrid | 6.15\* | 5.55 | 0.10\* | 0.74 |
| Haiku 5.5 | plain | A Direct | 8.02\* | 0.37\* | 0.00\* | -0.08\* |
| Haiku 5.5 | plain | B Daily | 11.72\* | 0.16\* | 0.00\* | -0.07\* |
| Haiku 5.5 | plain | C Describe | 6.42\* | 4.11\* | 0.03 | 0.48\* |
| Haiku 5.5 | plain | D Hybrid | 5.14\* | 5.07\* | 0.12\* | 0.79 |
| Haiku 5.5 | anchored | A Direct | 7.13\* | 0.11\* | 0.00\* | -0.12\* |
| Haiku 5.5 | anchored | B Daily | 11.06\* | 0.15\* | 0.00\* | -0.08\* |
| Haiku 5.5 | anchored | C Describe | 7.49 | 6.11 | 0.10\* | 0.68 |
| Haiku 5.5 | anchored | D Hybrid | 5.71\* | 5.79 | 0.11\* | 0.84 |
| Sonnet 5 | plain | A Direct | 5.60\* | 0.17\* | 0.00\* | -0.15\* |
| Sonnet 5 | plain | B Daily | 10.40\* | 0.20\* | 0.00\* | -0.08\* |
| Sonnet 5 | plain | C Describe | 6.64\* | 4.66\* | 0.03 | 0.55\* |
| Sonnet 5 | plain | D Hybrid | 4.80\* | 4.53\* | 0.11\* | 0.74 |
| Sonnet 5 | anchored | A Direct | 6.70\* | 0.16\* | 0.00\* | -0.12\* |
| Sonnet 5 | anchored | B Daily | 10.16\* | 0.22\* | 0.00\* | -0.08\* |
| Sonnet 5 | anchored | C Describe | 7.31\* | 5.04\* | 0.06\* | 0.55\* |
| Sonnet 5 | anchored | D Hybrid | 6.87\* | 6.65 | 0.09\* | 0.82 |
| GPT-5.6-terra | plain | A Direct | 7.89 | 0.14\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | B Daily | 8.37\* | 0.10\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | C Describe | 7.00\* | 4.79\* | 0.05\* | 0.54\* |
| GPT-5.6-terra | plain | D Hybrid | 5.09\* | 4.69\* | 0.11\* | 0.73 |
| GPT-5.6-terra | anchored | A Direct | 7.60\* | 0.16\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | anchored | B Daily | 5.92\* | 0.30\* | 0.00\* | -0.12\* |
| GPT-5.6-terra | anchored | C Describe | 9.46\* | 5.71\* | 0.07\* | 0.50\* |
| GPT-5.6-terra | anchored | D Hybrid | 7.17\* | 6.70 | 0.07\* | 0.79 |
| DeepSeek-V4-Pro | plain | A Direct | 6.98\* | 1.15\* | 0.00\* | 0.02\* |
| DeepSeek-V4-Pro | plain | B Daily | 8.57\* | 0.13\* | 0.00\* | -0.10\* |
| DeepSeek-V4-Pro | plain | C Describe | 5.78\* | 3.53\* | 0.04 | 0.44\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 6.57\* | 5.83 | 0.09\* | 0.73 |
| DeepSeek-V4-Pro | anchored | A Direct | 6.57\* | 0.53\* | 0.00\* | -0.07\* |
| DeepSeek-V4-Pro | anchored | B Daily | 7.06\* | 0.21\* | 0.00\* | -0.11\* |
| DeepSeek-V4-Pro | anchored | C Describe | 7.09\* | 4.77\* | 0.04 | 0.53\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 7.50 | 6.31 | 0.07\* | 0.71 |
| Gemini 3.1 Flash-Lite | plain | A Direct | 10.25\* | 0.41\* | 0.00\* | -0.06\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 7.96\* | 0.06\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 6.62\* | 3.44\* | 0.03 | 0.37\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 7.41 | 6.53 | 0.07\* | 0.75 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 6.88\* | 0.26\* | 0.00\* | -0.11\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 7.18\* | 0.13\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 6.07\* | 5.56\* | 0.12\* | 0.75 |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 6.67\* | 5.80 | 0.09\* | 0.72 |
| Mistral Large 4 | plain | A Direct | 9.24\* | 1.73\* | 0.00\* | 0.08\* |
| Mistral Large 4 | plain | B Daily | 8.39\* | 0.07\* | 0.00\* | -0.11\* |
| Mistral Large 4 | plain | C Describe | 7.04\* | 4.93\* | 0.04 | 0.56\* |
| Mistral Large 4 | plain | D Hybrid | 4.28\* | 4.48\* | 0.15\* | 0.81 |
| Mistral Large 4 | anchored | A Direct | 7.30\* | 0.26\* | 0.00\* | -0.10\* |
| Mistral Large 4 | anchored | B Daily | 8.74\* | 0.11\* | 0.00\* | -0.10\* |
| Mistral Large 4 | anchored | C Describe | 6.18\* | 5.43\* | 0.15\* | 0.72 |
| Mistral Large 4 | anchored | D Hybrid | 5.41\* | 5.11\* | 0.11\* | 0.76 |

*Table B3. Persona experiment with real household demographics, 600 household-windows per cell. Reference row: real distribution of the 801 households (10,413 household-windows). \* the 95% bootstrap interval excludes the reference value.*

# Appendix C. Reproducibility {-}

All code, the pilot grid runner, the demographic-ceiling script, the analysis scripts, and the tables and figures used here are in an anonymized project repository (the link will be provided after the review process to preserve double-blind review). Raw model responses are saved with each run. Household-level Complete Journey data are not redistributed; the code reads them from the public package files.

# Appendix D. Proof of Proposition 3 {-}

*Proof.* (a) Let $A$ be any event with $P(A) = q$. Then $E[\Lambda \mathbf{1}_A] = \mu q + \text{Cov}(\Lambda, \mathbf{1}_A)$, and the Cauchy–Schwarz inequality gives $\text{Cov}(\Lambda, \mathbf{1}_A) \le \sqrt{\text{Var}(\Lambda)}\sqrt{q(1-q)} = \mu\sqrt{\alpha q(1-q)}$. This bounds $S_q$ from above. For the lower bound take an event that is independent of $\Lambda$ and has probability $q$ (on a sufficiently rich probability space, or by assigning ties fractionally); it yields $E[\Lambda \mathbf{1}_A] = \mu q$.

(b) Let $\Lambda$ have density $f_{k,\theta}$ with $\mu = k\theta$. Since $\lambda f_{k,\theta}(\lambda) = k\theta\, f_{k+1,\theta}(\lambda)$, we have $E[\Lambda \mathbf{1}\{\Lambda > x\}] = \mu\, P(G_{k+1,\theta} > x)$ for a gamma variable $G_{k+1,\theta}$ with shape $k+1$ and scale $\theta$. The maximum in the definition of $S_q$ is attained by the event $\{\Lambda > x_q\}$ with $P(\Lambda > x_q) = q$, because $E[\Lambda \mathbf{1}_A]$ is largest when $A$ collects the largest values of $\Lambda$. Hence $S_q = P(G_{k+1,\theta} > x_q)$ with $x_q = \theta F_k^{-1}(1-q)$, which is the stated expression.

(c) The limit follows from (a), because the upper bound tends to $q$ as $\alpha \to 0$. For monotonicity let $k_1 < k_2$, so that $\alpha_1 > \alpha_2$, and let $Y_j$ be gamma variables with shape $k_j$ and mean one. By the beta–gamma algebra, if $G \sim \text{Gamma}(k_2, 1)$ and $B \sim \text{Beta}(k_1, k_2 - k_1)$ are independent, then $BG \sim \text{Gamma}(k_1, 1)$. Hence $Y_1$ has the distribution of $M Y_2$ with $Y_2 = G/k_2$ and $M = B k_2/k_1$, where $M$ is independent of $Y_2$, non-degenerate, and has $E[M] = 1$. Let $A^* = \{Y_2 > x^*\}$ be the event with probability $q$ that attains $S_q$ for $Y_2$. Then $S_q(\alpha_1) \ge E[M Y_2 \mathbf{1}_{A^*}] = E[M]\,E[Y_2 \mathbf{1}_{A^*}] = S_q(\alpha_2)$. The inequality is strict, because the maximizing event for $M Y_2$ is $\{M Y_2 > y^*\}$, which differs from $A^*$ with positive probability when $M$ is non-degenerate, and the maximizing event is unique up to null sets.

(d) The argument of (a) uses only the mean and the variance of the nonnegative variable and holds for any event of probability $q$, including events defined by ranking customers on their counts (ties are broken arbitrarily). For a deterministic simulator $\text{Var}(N^*) = \text{Var}(m(X))$, so the squared coefficient of variation of $N^*$ is $c^2$.

 $\square$
