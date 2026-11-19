Dear Editors,

Please consider the enclosed manuscript, "Mutation Scores Overstate the Fault-Finding Reach of LLM-Written Unit Tests: Evidence from Mutants and Real Faults," for publication as a research paper in *Software Testing, Verification and Reliability*.

Unit tests written by large language models are evaluated mostly by coverage and mutation scores. We measured the fault-finding reach of tests written by three current models on 947 mutants and on 87 real faults from BugsInPy, using the same prompts and targets. On mutants, the generated tests match or exceed developer tests within one or two attempts. On real faults, six attempts reveal only 10% to 15% of the faults. The gap is explained by the oracle problem: 54% to 66% of attempts contain a test that fails on the faulty version, but only 4% to 5% reveal the fault. Mutation analysis rewards tests that pin down current behaviour, and a real fault is already part of that behaviour.

We believe the paper fits the journal's scope in test generation, mutation testing and test oracles, and that its message is directly relevant to both researchers who evaluate LLM-based test generation and practitioners who consider adopting it. All code, prompts and results are available from the author on request.

An earlier version of this manuscript was submitted to *Empirical Software Engineering* (EMSE-D-26-01461) and was returned without review because of that journal's reviewing capacity. The manuscript has since been revised and is not under consideration elsewhere. Use of generative AI is disclosed in the manuscript.

Sincerely,

Ook Lee
Department of Information Systems, Hanyang University, Seoul, Republic of Korea
ooklee@hanyang.ac.kr
