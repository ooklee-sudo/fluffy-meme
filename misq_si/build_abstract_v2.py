import sys; sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
d = new_doc(spacing=1.3, footer=False)
TITLE(d, "Infrastructure Citizens Hold to Account: Digital Infrastructure in a Society That Won Its Democracy", size=15)
P(d, "Optional abstract v2, MIS Quarterly Special Issue on Indigenous Theory Development  ·  Ook Lee, Hanyang University", indent=False, align="center", size=10, italic=True, after=10, spacing=1.1)
P(d, "**Draft for the author. Items in [brackets] must be verified or filled by the author; nothing here reports findings.**", indent=False, size=10, after=8, spacing=1.1)
ABS = [
"**Phenomenon.** South Korea is commonly described as a country that won its democracy through its own mobilization (the 1987 democratic struggle [verify]) and that later invested heavily in national information infrastructure, including broadband and e-government [verify programs and dates]. In this setting digital infrastructure is not only a technical or commercial asset. Public reactions to major service failures, such as the 2022 data-center fire that disrupted a dominant messaging platform [verify], and the use of petition and complaint channels suggest that citizens may treat infrastructure as something they are entitled to hold to account, as they once held the state to account [to be examined, not assumed].",
"**What we do not claim.** We do not claim that democratization caused economic growth. Most accounts date the high-growth period to the authoritarian developmental state and infrastructure expansion to the democratic period. Our interest is narrower and begins from the phenomenon: how a society with this history makes sense of, and acts on, the reliability and ownership of digital infrastructure.",
"**Why this is an indigenous phenomenon.** IS research on infrastructure, platforms and outages mostly draws on frames of service quality, platform governance and market competition. If accountability for infrastructure in Korea is shaped by collective memory of a struggle for rights, then these frames describe the setting only by importing assumptions about users as customers. We start from practitioners' and citizens' own categories, such as how outages are described, who is said to be responsible, and what remedies are demanded [terms to be gathered from the field].",
"**Research questions.** (1) When major digital services fail, who is held responsible, by whom, and in what language? (2) How do citizens, firms, regulators and the press connect infrastructure to rights and obligations? (3) What concepts, grounded in these accounts, are needed to explain the resulting practices?",
"**Approach.** An inductive, interpretive case study of [selected infrastructure failures and the responses to them], using public documents, regulatory and legislative records, media coverage, petition and complaint data where available, and [N] interviews with operators, regulators, firm staff and affected users [access to be secured by the author]. The categories above are starting points and will be dropped if the evidence does not support them. As a Discovery Short Paper, the contribution is a rich account of the phenomenon and the constructs that emerge from it.",
"**Contribution to theory.** We expect to propose one or more constructs describing how accountability for digital infrastructure is claimed and assigned in this setting [to be induced from data], and to state what they imply for theories of platform governance, infrastructure and the governance of AI-enabled services. We will not assume the constructs generalize, and we will say what the account means for existing theory so that it is more than description.",
]
for t in ABS:
    P(d, t, indent=False, after=6, align="justify", spacing=1.25)
d.save("/home/user/fluffy-meme/misq_si/MISQ_SI_Optional_Abstract_v2_DRAFT.docx")
import re
words = sum(len(re.sub(r"[*\[\]]", "", t).split()) for t in ABS)
print("abstract words:", words)
