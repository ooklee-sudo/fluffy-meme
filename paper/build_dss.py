"""Build the numbered-reference manuscript and a Word file from paper/dss_manuscript_src.md.
Usage (from the repository root): python paper/build_dss.py"""
import re
import subprocess

BIB = {
 "naor1969": "P. Naor, The regulation of queue size by levying tolls, Econometrica 37 (1) (1969) 15–24. https://doi.org/10.2307/1909200.",
 "mendelson1985": "H. Mendelson, Pricing computer services: queueing effects, Communications of the ACM 28 (3) (1985) 312–321. https://doi.org/10.1145/3166.3171.",
 "dewanmendelson1990": "S. Dewan, H. Mendelson, User delay costs and internal pricing for a service facility, Management Science 36 (12) (1990) 1502–1517. https://doi.org/10.1287/mnsc.36.12.1502.",
 "mendelsonwhang1990": "H. Mendelson, S. Whang, Optimal incentive-compatible priority pricing for the M/M/1 queue, Operations Research 38 (5) (1990) 870–883. https://doi.org/10.1287/opre.38.5.870.",
 "afeche2004": "P. Afèche, H. Mendelson, Pricing and priority auctions in queueing systems with a generalized delay cost structure, Management Science 50 (7) (2004) 869–882. https://doi.org/10.1287/mnsc.1030.0156.",
 "dewan1996": "S. Dewan, Pricing computer services under alternative control structures: tradeoffs and trends, Information Systems Research 7 (3) (1996) 301–307. https://doi.org/10.1287/isre.7.3.301.",
 "hassinhaviv2003": "R. Hassin, M. Haviv, To Queue or Not to Queue: Equilibrium Behavior in Queueing Systems, Springer, Boston, 2003. https://doi.org/10.1007/978-1-4615-0359-0.",
 "steiner1957": "P.O. Steiner, Peak loads and efficient pricing, Quarterly Journal of Economics 71 (4) (1957) 585–610. https://doi.org/10.2307/1885712.",
 "boiteux1960": "M. Boiteux, Peak-load pricing, Journal of Business 33 (2) (1960) 157–179. https://doi.org/10.1086/294331.",
 "paschalidis2000": "I.Ch. Paschalidis, J.N. Tsitsiklis, Congestion-dependent pricing of network services, IEEE/ACM Transactions on Networking 8 (2) (2000) 171–184. https://doi.org/10.1109/90.842140.",
 "ata2006": "B. Ata, S. Shneorson, Dynamic control of an M/M/1 service system with adjustable arrival and service rates, Management Science 52 (11) (2006) 1778–1791. https://doi.org/10.1287/mnsc.1060.0587.",
 "kim2018": "J. Kim, R.S. Randhawa, The value of dynamic pricing in large queueing systems, Operations Research 66 (2) (2018) 409–425. https://doi.org/10.1287/opre.2017.1668.",
 "bergquist2025": "J. Bergquist, A.N. Elmachtoub, Static pricing guarantees for queueing systems, Stochastic Systems 16 (1) (2026) 1–21. https://doi.org/10.1287/stsy.2023.0057.",
 "bergemann2025": "D. Bergemann, A. Bonatti, A. Smolin, Menu pricing of large language models, arXiv:2502.07736 (2026; first version 2025).",
 "mcdougall2026": "I. McDougall, K. Sankaralingam, Pricing time, not just tokens: latency-aware mechanism design for LLM inference, arXiv:2609.40098 (2026); Proceedings of the 27th ACM Conference on Economics and Computation (EC'26).",
 "lin2026": "R. Lin, Z. Ding, Z. Han, J. Zhang, Large-scale LLM inference with heterogeneous workloads: prefill-decode contention and asymptotically optimal control, arXiv:2602.02987 (2026).",
 "dai2025": "J.G. Dai, T. Deng, Y. Li, T. Peng, Throughput-optimal scheduling algorithms for LLM inference and AI agents, arXiv:2504.07347 (2025).",
 "patel2024": "P. Patel, E. Choukse, C. Zhang, A. Shah, Í. Goiri, S. Maleki, R. Bianchini, Splitwise: efficient generative LLM inference using phase splitting, in: 2024 ACM/IEEE 51st Annual International Symposium on Computer Architecture (ISCA), 2024, pp. 118–132. https://doi.org/10.1109/ISCA59077.2024.00019.",
 "stojkovic2025": "J. Stojkovic, C. Zhang, Í. Goiri, J. Torrellas, E. Choukse, DynamoLLM: designing LLM inference clusters for performance and energy efficiency, in: 2025 IEEE International Symposium on High Performance Computer Architecture (HPCA), 2025, pp. 1348–1362. https://doi.org/10.1109/HPCA61900.2025.00102.",
 "wang2024": "Y. Wang, Y. Chen, Z. Li, X. Kang, Y. Fang, Y. Zhou, Y. Zheng, Z. Tang, X. He, R. Guo, X. Wang, Q. Wang, A.C. Zhou, X. Chu, BurstGPT: a real-world workload dataset to optimize LLM serving systems, in: Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2 (KDD '25), 2025, pp. 5831–5841. https://doi.org/10.1145/3711896.3737413.",
 "heffes1986": "H. Heffes, D.M. Lucantoni, A Markov modulated characterization of packetized voice and data traffic and related statistical multiplexer performance, IEEE Journal on Selected Areas in Communications 4 (6) (1986) 856–868. https://doi.org/10.1109/JSAC.1986.1146393.",
 "fischer1993": "W. Fischer, K. Meier-Hellstern, The Markov-modulated Poisson process (MMPP) cookbook, Performance Evaluation 18 (2) (1993) 149–171. https://doi.org/10.1016/0166-5316(93)90035-S.",
 "harchol2013": "M. Harchol-Balter, Performance Modeling and Design of Computer Systems: Queueing Theory in Action, Cambridge University Press, 2013. https://doi.org/10.1017/CBO9781139226424.",
 "schweitzer1968": "P.J. Schweitzer, Perturbation theory and finite Markov chains, Journal of Applied Probability 5 (2) (1968) 401–413. https://doi.org/10.2307/3212261.",
 "azure2023": "Microsoft Azure, Azure Public Dataset: Azure LLM inference trace 2023, https://github.com/Azure/AzurePublicDataset (accessed 9 October 2026).",
 "azure2024": "Microsoft Azure, Azure Public Dataset: Azure LLM inference trace 2024, https://github.com/Azure/AzurePublicDataset (accessed 9 October 2026).",
 "deepseek": "DeepSeek, Models & pricing, https://api-docs.deepseek.com/quick_start/pricing (accessed 9 October 2026).",
 "openai": "OpenAI, API pricing, https://developers.openai.com/api/docs/pricing (accessed 9 October 2026).",
 "bedrock": "Amazon Web Services, Service tiers for optimizing performance and cost, Amazon Bedrock User Guide, https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html (accessed 9 October 2026).",
}

src = open("paper/dss_manuscript_src.md").read()
head, refs_marker = src.split("## References")[0], "## References"
order = []

def repl(m):
    keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
    nums = []
    for k in keys:
        assert k in BIB, k
        if k not in order:
            order.append(k)
        nums.append(order.index(k) + 1)
    return "[" + ", ".join(str(n) for n in sorted(nums)) + "]"

body = re.sub(r"\[(@[^\]]+)\]", repl, head)
refs = "\n\n".join(f"[{i + 1}] {BIB[k]}" for i, k in enumerate(order))
unused = [k for k in BIB if k not in order]
out = body + "## References\n\n" + refs + "\n"
open("paper/dss_manuscript.md", "w").write(out)
subprocess.run(["pandoc", "paper/dss_manuscript.md", "-o", "paper/dss_manuscript.docx", "--from", "markdown+tex_math_dollars",
                "--resource-path=paper"], check=True)
print("references:", len(order), "unused:", unused)
