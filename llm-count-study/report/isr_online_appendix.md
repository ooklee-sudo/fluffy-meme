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

| Model | Prompt | Outcome | No email | Lift, men's email [95% CI] | Lift, women's email [95% CI] | Gap men minus women [95% CI] | RR men | RR women |
|---|---|---|---|---|---|---|---|---|
| Real (randomized) | | visit | 0.106 | +0.077 [+0.070, +0.083] | +0.045 [+0.039, +0.052] | +0.031 [+0.024, +0.038] | 1.72 | 1.43 |
| Real (randomized) | | purchase | 0.0057 | +0.0068 [+0.0050, +0.0086] | +0.0031 [+0.0015, +0.0047] | +0.0037 [+0.0017, +0.0056] | 2.19 | 1.54 |
| GPT-4o-mini | plain | visit | 0.260 | +0.190 [+0.175, +0.206]\* | +0.215 [+0.199, +0.229]\* | -0.025 [-0.051, +0.003]\* | 1.73 | 1.83\* |
| GPT-4o-mini | anchored | visit | 0.100 | +0.003 [+0.002, +0.004]\* | +0.004 [+0.002, +0.006]\* | -0.001 [-0.003, +0.001]\* | 1.03\* | 1.04\* |
| Llama-3.3-70B | plain | visit | 0.296 | +0.071 [+0.057, +0.084] | +0.064 [+0.050, +0.079]\* | +0.007 [-0.018, +0.030]\* | 1.24\* | 1.22\* |
| Llama-3.3-70B | anchored | visit | 0.100 | +0.035 [+0.032, +0.039]\* | +0.036 [+0.033, +0.039]\* | -0.000 [-0.006, +0.005]\* | 1.36\* | 1.36 |
| Haiku 5.5 | plain | visit | 0.154 | +0.073 [+0.065, +0.081] | +0.091 [+0.082, +0.099]\* | -0.018 [-0.032, -0.004]\* | 1.47\* | 1.59 |
| Haiku 5.5 | anchored | visit | 0.093 | +0.159 [+0.154, +0.164]\* | +0.163 [+0.158, +0.167]\* | -0.004 [-0.011, +0.003]\* | 2.71\* | 2.75\* |
| Sonnet 5 | plain | visit | 0.212 | +0.139 [+0.129, +0.150]\* | +0.152 [+0.143, +0.162]\* | -0.013 [-0.028, +0.003]\* | 1.65 | 1.72\* |
| Sonnet 5 | anchored | visit | 0.195 | +0.027 [+0.019, +0.036]\* | +0.036 [+0.027, +0.045]\* | -0.009 [-0.022, +0.004]\* | 1.14\* | 1.19\* |
| GPT-5.6-terra | plain | visit | 0.277 | +0.049 [+0.038, +0.060]\* | +0.055 [+0.044, +0.066] | -0.006 [-0.021, +0.010]\* | 1.18\* | 1.20\* |
| GPT-5.6-terra | anchored | visit | 0.103 | +0.075 [+0.068, +0.083] | +0.088 [+0.080, +0.096]\* | -0.013 [-0.025, -0.001]\* | 1.73 | 1.86\* |
| DeepSeek-V4-Pro | plain | visit | 0.191 | +0.051 [+0.037, +0.065]\* | +0.044 [+0.030, +0.057] | +0.007 [-0.008, +0.021]\* | 1.27\* | 1.23\* |
| DeepSeek-V4-Pro | anchored | visit | 0.068 | +0.198 [+0.187, +0.208]\* | +0.183 [+0.173, +0.192]\* | +0.015 [+0.002, +0.029]\* | 3.90\* | 3.68\* |
| Gemini 3.1 Flash-Lite | plain | visit | 0.123 | +0.045 [+0.037, +0.052]\* | +0.049 [+0.041, +0.057] | -0.005 [-0.019, +0.008]\* | 1.36\* | 1.40 |
| Gemini 3.1 Flash-Lite | anchored | visit | 0.100 | +0.059 [+0.055, +0.064]\* | +0.058 [+0.053, +0.063]\* | +0.001 [-0.007, +0.009]\* | 1.59\* | 1.58\* |
| Mistral Large 4 | plain | visit | 0.230 | +0.078 [+0.066, +0.089] | +0.089 [+0.078, +0.101]\* | -0.012 [-0.033, +0.008]\* | 1.34\* | 1.39 |
| Mistral Large 4 | anchored | visit | 0.100 | +0.041 [+0.035, +0.047]\* | +0.037 [+0.032, +0.043]\* | +0.004 [-0.007, +0.014]\* | 1.40\* | 1.37 |
| GPT-4o-mini | plain | purchase | 0.155 | +0.169 [+0.155, +0.184]\* | +0.201 [+0.187, +0.214]\* | -0.032 [-0.056, -0.005]\* | 2.09 | 2.30\* |
| GPT-4o-mini | anchored | purchase | 0.064 | +0.026 [+0.021, +0.030]\* | +0.048 [+0.044, +0.053]\* | -0.023 [-0.029, -0.018]\* | 1.40\* | 1.75\* |
| Llama-3.3-70B | plain | purchase | 0.087 | +0.154 [+0.141, +0.168]\* | +0.167 [+0.153, +0.182]\* | -0.013 [-0.039, +0.011] | 2.78\* | 2.93\* |
| Llama-3.3-70B | anchored | purchase | 0.004 | +0.149 [+0.137, +0.162]\* | +0.161 [+0.148, +0.175]\* | -0.012 [-0.034, +0.011] | 43.83\* | 47.87\* |
| Haiku 5.5 | plain | purchase | 0.096 | +0.047 [+0.041, +0.053]\* | +0.054 [+0.049, +0.060]\* | -0.008 [-0.017, +0.002]\* | 1.49\* | 1.57 |
| Haiku 5.5 | anchored | purchase | 0.008 | +0.110 [+0.104, +0.116]\* | +0.120 [+0.113, +0.126]\* | -0.010 [-0.019, -0.000]\* | 15.80\* | 17.02\* |
| Sonnet 5 | plain | purchase | 0.093 | +0.044 [+0.039, +0.050]\* | +0.058 [+0.053, +0.063]\* | -0.013 [-0.022, -0.004]\* | 1.48\* | 1.62 |
| Sonnet 5 | anchored | purchase | 0.045 | +0.002 [-0.001, +0.006]\* | +0.009 [+0.006, +0.012]\* | -0.007 [-0.012, -0.002]\* | 1.05\* | 1.21\* |
| GPT-5.6-terra | plain | purchase | 0.069 | +0.111 [+0.104, +0.118]\* | +0.110 [+0.103, +0.117]\* | +0.001 [-0.010, +0.011] | 2.61\* | 2.60\* |
| GPT-5.6-terra | anchored | purchase | 0.008 | +0.016 [+0.014, +0.018]\* | +0.018 [+0.016, +0.020]\* | -0.002 [-0.005, +0.001]\* | 3.00\* | 3.26\* |
| DeepSeek-V4-Pro | plain | purchase | 0.100 | +0.025 [+0.016, +0.035]\* | +0.025 [+0.016, +0.035]\* | -0.000 [-0.010, +0.010] | 1.25\* | 1.26\* |
| DeepSeek-V4-Pro | anchored | purchase | 0.073 | +0.110 [+0.099, +0.121]\* | +0.107 [+0.096, +0.118]\* | +0.003 [-0.010, +0.015] | 2.52 | 2.47\* |
| Gemini 3.1 Flash-Lite | plain | purchase | 0.072 | +0.029 [+0.025, +0.033]\* | +0.031 [+0.027, +0.035]\* | -0.002 [-0.009, +0.005] | 1.40\* | 1.43 |
| Gemini 3.1 Flash-Lite | anchored | purchase | 0.010 | +0.014 [+0.012, +0.015]\* | +0.014 [+0.012, +0.015]\* | +0.000 [-0.002, +0.003]\* | 2.41 | 2.39\* |
| Mistral Large 4 | plain | purchase | 0.119 | +0.098 [+0.091, +0.105]\* | +0.097 [+0.088, +0.106]\* | +0.001 [-0.012, +0.015] | 1.82\* | 1.81\* |
| Mistral Large 4 | anchored | purchase | 0.009 | +0.078 [+0.074, +0.082]\* | +0.077 [+0.072, +0.081]\* | +0.001 [-0.007, +0.009] | 10.12\* | 10.01\* |

*Table B4. Email experiment, probability-elicitation design (mean elicited probability over 300 simulated customers per seed, three independent calls per customer, pooled over three seeds, 900 customers per model). Lift = probability with the email minus probability without it; gap = lift of the men's email minus lift of the women's email; intervals are 95% paired bootstrap intervals over customers (real values: normal approximation). RR = risk ratio, the mean of the three per-seed ratios; its asterisk is set only if the interval excludes the real ratio in all three seeds. \* the simulated and the real intervals do not overlap.*

| Setting | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|
| Low mean | Reference | 0.49 | 2.49 | 0.74 | 3.05 |
| Low mean | A Direct | 0.00 to 2.10 | 0.00 to 14.72 | 0.00 to 1.00 | -1.00 to 6.54 |
| Low mean | B Daily | 0.00 to 13.56 | 0.24 to 2.95 | 0.00 to 1.00 | -0.86 to 0.62 |
| Low mean | C Describe | 0.37 to 1.30 | 0.97 to 1.61 | 0.32 to 0.71 | -0.06 to 0.80 |
| Low mean | D Hybrid | 0.26 to 0.93 | 1.47 to 3.38 | 0.63 to 0.81 | 1.81 to 3.77 |
| High mean | Reference | 4.84 | 7.85 | 0.19 | 1.42 |
| High mean | A Direct | 3.73 to 11.74 | 0.00 to 2.45 | 0.00 to 0.02 | -0.20 to 0.17 |
| High mean | B Daily | 4.35 to 16.65 | 0.04 to 0.38 | 0.00 to 0.00 | -0.20 to -0.06 |
| High mean | C Describe | 4.23 to 7.95 | 3.65 to 6.44 | 0.01 to 0.15 | 0.41 to 1.00 |
| High mean | D Hybrid | 3.63 to 8.69 | 5.84 to 12.15 | 0.13 to 0.27 | 1.03 to 1.52 |

*Table B5. Low-mean and high-mean settings: range of results across the model-and-prompt cells of each design (sixteen cells in each setting). Reference rows are the real values. For design A in the low-mean setting the variance-to-mean ratio of 1.00 comes from a cell in which practically every simulated customer answered "0" and is uninformative.*

| Design | Mean | Var/mean | Zero | Alpha | Rank correlation with real count |
|---|---|---|---|---|---|
| Reference | 7.83 | 6.52 | 0.03 | 0.71 | |
| A Direct | 5.60 to 10.25 | 0.00 to 1.73 | 0.00 to 0.00 | -0.16 to 0.08 | -0.11 to +0.04 |
| B Daily | 5.92 to 17.21 | 0.06 to 0.30 | 0.00 to 0.00 | -0.12 to -0.05 | -0.08 to +0.04 |
| C Describe | 5.78 to 9.46 | 3.44 to 6.11 | 0.03 to 0.15 | 0.37 to 0.79 | -0.01 to +0.08 |
| D Hybrid | 4.28 to 7.53 | 4.48 to 6.70 | 0.07 to 0.15 | 0.71 to 0.84 | -0.06 to +0.05 |

*Table B6. Persona experiment with real household demographics: range of results across the 16 model-and-prompt cells of each design (600 household-windows per cell). The last column is the range of the Spearman correlation between the simulated count and the household's real count in the same window.*

# Appendix C. Reproducibility {-}

All code, the pilot grid runner, the demographic-ceiling script, the analysis scripts, and the tables and figures used here are in an anonymized project repository (the link will be provided after the review process to preserve double-blind review). Raw model responses are saved with each run. Household-level Complete Journey data are not redistributed; the code reads them from the public package files.

# Appendix D. Proofs of Propositions 1 to 3 {-}

**Proposition 1.**  The first statement is the law of total variance. With $v(X) = 0$, $\text{Var}(N^*) = \text{Var}(m(X))$, and substituting into the definition of $\alpha$ gives $\alpha^* = c^2 - 1/\mu^*$. If $m(X) = E[\Lambda \mid X]$, then $\mu^* = \mu$ and $\text{Var}(m(X)) = \text{Var}(\Lambda) - E[\text{Var}(\Lambda \mid X)]$, which yields the last expression. $\square$

**Proposition 2.**  By independence, $E[\Lambda^2] = E[\lambda(X)^2]\,E[G^2] = \mu^2(1 + c^2)(1 + \alpha_w)$, and $\alpha = E[\Lambda^2]/\mu^2 - 1$. $\square$

**Proposition 3.***Proof.* (a) Let $A$ be any event with $P(A) = q$. Then $E[\Lambda \mathbf{1}_A] = \mu q + \text{Cov}(\Lambda, \mathbf{1}_A)$, and the Cauchy–Schwarz inequality gives $\text{Cov}(\Lambda, \mathbf{1}_A) \le \sqrt{\text{Var}(\Lambda)}\sqrt{q(1-q)} = \mu\sqrt{\alpha q(1-q)}$. This bounds $S_q$ from above. For the lower bound take an event that is independent of $\Lambda$ and has probability $q$ (on a sufficiently rich probability space, or by assigning ties fractionally); it yields $E[\Lambda \mathbf{1}_A] = \mu q$.

(b) Let $\Lambda$ have density $f_{k,\theta}$ with $\mu = k\theta$. Since $\lambda f_{k,\theta}(\lambda) = k\theta\, f_{k+1,\theta}(\lambda)$, we have $E[\Lambda \mathbf{1}\{\Lambda > x\}] = \mu\, P(G_{k+1,\theta} > x)$ for a gamma variable $G_{k+1,\theta}$ with shape $k+1$ and scale $\theta$. The maximum in the definition of $S_q$ is attained by the event $\{\Lambda > x_q\}$ with $P(\Lambda > x_q) = q$, because $E[\Lambda \mathbf{1}_A]$ is largest when $A$ collects the largest values of $\Lambda$. Hence $S_q = P(G_{k+1,\theta} > x_q)$ with $x_q = \theta F_k^{-1}(1-q)$, which is the stated expression.

(c) The limit follows from (a), because the upper bound tends to $q$ as $\alpha \to 0$. For monotonicity let $k_1 < k_2$, so that $\alpha_1 > \alpha_2$, and let $Y_j$ be gamma variables with shape $k_j$ and mean one. By the beta–gamma algebra, if $G \sim \text{Gamma}(k_2, 1)$ and $B \sim \text{Beta}(k_1, k_2 - k_1)$ are independent, then $BG \sim \text{Gamma}(k_1, 1)$. Hence $Y_1$ has the distribution of $M Y_2$ with $Y_2 = G/k_2$ and $M = B k_2/k_1$, where $M$ is independent of $Y_2$, non-degenerate, and has $E[M] = 1$. Let $A^* = \{Y_2 > x^*\}$ be the event with probability $q$ that attains $S_q$ for $Y_2$. Then $S_q(\alpha_1) \ge E[M Y_2 \mathbf{1}_{A^*}] = E[M]\,E[Y_2 \mathbf{1}_{A^*}] = S_q(\alpha_2)$. The inequality is strict, because the maximizing event for $M Y_2$ is $\{M Y_2 > y^*\}$, which differs from $A^*$ with positive probability when $M$ is non-degenerate, and the maximizing event is unique up to null sets.

(d) The argument of (a) uses only the mean and the variance of the nonnegative variable and holds for any event of probability $q$, including events defined by ranking customers on their counts (ties are broken arbitrarily). For a deterministic simulator $\text{Var}(N^*) = \text{Var}(m(X))$, so the squared coefficient of variation of $N^*$ is $c^2$.

 $\square$

# Appendix E. Backtest of the Acceptance Test {-}

The backtest uses the parsed result tables (no new model calls); the script is `backtest.py`. *Email experiment.* For each of the 32 configurations of the probability design (8 models, 2 prompt variants, 2 outcomes), the men's email serves as the past randomized test and the women's email as the new campaign, and the reverse, giving 64 cases. The simulator is accepted for the new campaign if its lift for the past campaign is within a factor of 2 of the measured lift (0.0766 and 0.0452 for visits, 0.0068 and 0.0031 for purchases). The break-even lift is varied on a log scale from one tenth to ten times the measured lift of the new campaign (201 values); a decision is wrong at a break-even value if the simulated and measured lifts fall on different sides of it, and a case is summarized by the share of wrong values. Recalibration multiplies the simulated new lift by the measured-to-simulated ratio of the past campaign. *Transaction settings.* A cell passes the history gate if the reference mean and the reference zero share lie within the simulated 95% intervals (widened by 2% of the reference mean and by 0.02 for the zero share). The held-out statistic is the share of expected purchases made by the top decile implied by the simulated $\alpha$ through Proposition 3(b) (the share is 0.10 when $\alpha \le 0$), and a cell is wrong if this differs from the share implied by the reference $\alpha$ by more than 0.10.

| Outcome | Rule | Cases | Wrong decisions (share of break-even values) | Lift off by more than 2x |
|---|---|---|---|---|
| visit | Trust the simulator | 32 | 0.14 | 0.38 |
| visit | Sign check | 32 | 0.14 | 0.38 |
| visit | Acceptance gate | 20 | 0.09 | 0.20 |
| visit | Recalibrated by past ratio | 32 | 0.13 | 0.19 |
| purchase | Trust the simulator | 32 | 0.43 | 1.00 |
| purchase | Sign check | 32 | 0.43 | 1.00 |
| purchase | Acceptance gate | 0 | n/a | n/a |
| purchase | Recalibrated by past ratio | 32 | 0.21 | 1.00 |
| all | Trust the simulator | 64 | 0.29 | 0.69 |
| all | Sign check | 64 | 0.29 | 0.69 |
| all | Acceptance gate | 20 | 0.09 | 0.20 |
| all | Recalibrated by past ratio | 64 | 0.17 | 0.59 |

*Table E1. Email backtest, by decision rule and outcome.*

| Model | Anchored prompt | Past campaign | Past ratio | New ratio | New lift within 2x |
|---|---|---|---|---|---|
| claude-haiku-5.5 | no | men | 0.95 | 2.01 | no |
| claude-sonnet-5 | no | men | 1.81 | 3.36 | no |
| claude-sonnet-5 | yes | women | 0.80 | 0.35 | no |
| deepseek-v4-pro-0813 | no | men | 0.67 | 0.97 | yes |
| deepseek-v4-pro-0813 | no | women | 0.97 | 0.67 | yes |
| gemini-3.1-flash-lite | no | men | 0.59 | 1.08 | yes |
| gemini-3.1-flash-lite | no | women | 1.08 | 0.59 | yes |
| gemini-3.1-flash-lite | yes | men | 0.77 | 1.28 | yes |
| gemini-3.1-flash-lite | yes | women | 1.28 | 0.77 | yes |
| llama-3.3-70b-instruct | no | men | 0.93 | 1.42 | yes |
| llama-3.3-70b-instruct | no | women | 1.42 | 0.93 | yes |
| llama-3.3-70b-instruct | yes | women | 0.80 | 0.46 | no |
| mistral-large-4-0 | no | men | 1.02 | 1.97 | yes |
| mistral-large-4-0 | no | women | 1.97 | 1.02 | yes |
| mistral-large-4-0 | yes | men | 0.54 | 0.82 | yes |
| mistral-large-4-0 | yes | women | 0.82 | 0.54 | yes |
| gpt-5.6-terra | no | men | 0.64 | 1.22 | yes |
| gpt-5.6-terra | no | women | 1.22 | 0.64 | yes |
| gpt-5.6-terra | yes | men | 0.98 | 1.95 | yes |
| gpt-5.6-terra | yes | women | 1.95 | 0.98 | yes |

*Table E2. Cases admitted by the acceptance gate (all visits). Ratio is simulated lift divided by measured lift.*

| Setting | Design | Cells | Pass sign/mean check | Pass history gate | Wrong (all cells) | Wrong among gate passes |
|---|---|---|---|---|---|---|
| Retail (mean 0.49) | A | 12 | 2 | 0 | 1.00 | n/a |
| Retail (mean 0.49) | B | 15 | 3 | 0 | 1.00 | n/a |
| Retail (mean 0.49) | C | 16 | 12 | 1 | 1.00 | 1.00 |
| Retail (mean 0.49) | D | 16 | 15 | 8 | 0.06 | 0.00 |
| Grocery (4.84) | A | 16 | 8 | 0 | 1.00 | n/a |
| Grocery (4.84) | B | 16 | 3 | 0 | 1.00 | n/a |
| Grocery (4.84) | C | 16 | 14 | 1 | 0.56 | 0.00 |
| Grocery (4.84) | D | 16 | 14 | 6 | 0.00 | 0.00 |
| Demographic households (7.83) | A | 16 | 16 | 0 | 1.00 | n/a |
| Demographic households (7.83) | B | 16 | 14 | 0 | 1.00 | n/a |
| Demographic households (7.83) | C | 16 | 16 | 2 | 0.00 | 0.00 |
| Demographic households (7.83) | D | 16 | 16 | 0 | 0.00 | n/a |

*Table E3. Transaction backtest: held-out top-decile share error above 0.10, by setting and design. Cells with an undefined variance-to-mean ratio are excluded (187 of 192).*

The gate passes only designs that obtain the dispersion from outside the model (D) or from the described distribution (C). Because the hybrid design sets its dispersion from the reference, its low error rate under the gate is partly built in. The two-campaign structure of the email backtest implies that the 64 cases come from 32 configurations, so cases from the same configuration are not independent.
