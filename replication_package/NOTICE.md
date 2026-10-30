# Notice on data, licences and attribution

**Stack Overflow content.** `questions_v2.json`, `questions_windows.json`, `questions.json` and `validity_check.json` contain text of Stack Overflow questions and accepted answers (and, in `validity_check.json`, model answers to them). Stack Overflow content is contributed by its users and distributed under Creative Commons Attribution-ShareAlike (CC BY-SA); see https://stackoverflow.com/help/licensing for the version that applies to each post. Every record carries the question identifier `qid`; the original post and its authors can be found at `https://stackoverflow.com/q/<qid>`. Redistribution of these files must keep this attribution and the same licence.

**Model outputs.** Grades derive from answers produced by commercial and open-weight models through OpenRouter and a self-hosted vLLM server. Use of the outputs is subject to the providers' terms.

**Datasets used but not redistributed.** Stack Exchange data dump (Hugging Face copy `mikex86/stackoverflow-posts`); Stack Overflow Developer Survey 2023-2026 (ODbL 1.0, https://github.com/StackExchange/Survey); Anthropic Economic Index (CC-BY-4.0, https://huggingface.co/datasets/Anthropic/EconomicIndex).

**Code.** Licence to be chosen by the authors before publication (no licence is granted by this notice).

**Credentials.** The package contains no API keys. Keys are read from the environment variables `OPENROUTER_API_KEY` and `SE_KEY`.
