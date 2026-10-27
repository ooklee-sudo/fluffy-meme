# Exposure codebook

**Task.** For each repository (19) and each launch type (4), decide whether the repository is *exposed* to launches of that type: whether the repository's own code or documentation means that a new model of that type would require, enable, or invite a change to the repository.

Fill `exposure_coding_template.csv` (columns `repo`, `launch_type`, `exposed`, `evidence_url`, `evidence_note`). Work alone. Do not discuss the cells with the other coder until both sheets are submitted. Do not look at release histories or at any study results.

## Definition
**exposed = 1** if, as of the coding date, at least one of these is true:
1. The repository has a documented integration that calls, serves, loads, or trains models of this type. Examples: the repository has a client for that provider's API; it includes a model registry or model-loading code for open-weights models; its README or docs list supported models of this type.
2. Its docs say a user is expected to select or configure a model of this type.

**exposed = 0** if the repository has no such integration, or it concerns a provider/type that the repository does not mention anywhere in code or documentation.

## Rules for each type
- `openai` / `anthropic` / `google`: the repository has code or documentation for that provider's API (a client, a provider adapter, or a documented example that calls it). A mention in an unrelated issue does not count.
- `open_weights`: the repository can serve, load, train, fine-tune, evaluate, or convert open-weights models. Client SDKs of a single provider (for example, the OpenAI or Anthropic SDK) are `0` for this type.

## Evidence
For every cell coded `1`, give one URL (file or doc page on the default branch) in `evidence_url`. For cells coded `0`, write "no integration found" in `evidence_note` after searching the repository for the provider name (code search and docs). For ambiguous cells, write what is ambiguous in `evidence_note` and give your best call.

## Process
1. Coder A and coder B each fill a copy of the template independently.
2. `python ../kappa_exposure.py coderA.csv coderB.csv` prints kappa and the list of disagreements (keep columns `repo,launch_type,exposed`).
3. A third person, who has not seen release data, settles each disagreement from the evidence columns.
4. The consensus is saved as `exposure_frozen.csv` and its SHA-256 is recorded. It is not edited again.
5. For the sensitivity check on the prior study's launches, the same exposure table is used; only differences between coders' calls on cells that changed meaning over time (for example, a provider integration added after 2023) are re-coded as of the launch date, with a note.

## Coding date
Record the coding date. Integrations added later are not retroactively used for launches before they existed.
