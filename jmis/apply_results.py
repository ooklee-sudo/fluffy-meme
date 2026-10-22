"""Build jmis_draft_v4.docx from jmis_draft_v3.docx: Sections 6-7, abstract and Section 8 from the analysis outputs."""
import pickle, re, shutil, subprocess, sys, os, tempfile
from xml.sax.saxutils import escape
SRC, DST = "jmis_draft_v3.docx", "jmis_draft_v4.docx"
built = pickle.load(open("results/_built_sections.pkl", "rb"))["section"]
tmp = tempfile.mkdtemp(); subprocess.run(["unzip", "-q", SRC, "-d", tmp], check=True)
subprocess.run("find %s -type l -delete" % tmp, shell=True)
SK = [d for d in subprocess.run("ls -d /root/.claude/skills/synced/*/docx", shell=True, capture_output=True, text=True).stdout.split()][0]
subprocess.run([sys.executable, f"{SK}/scripts/merge_runs.py", tmp + "/"], check=True, capture_output=True)
p = tmp + "/word/document.xml"; x = open(p, encoding="utf8").read()
paras = [(m.start(), m.end(), re.sub(r"<[^>]+>", "", m.group(0))) for m in re.finditer(r"<w:p[ >].*?</w:p>", x, flags=re.S)]
i0 = [k for k, q in enumerate(paras) if q[2].startswith("6. Results")][0]; i1 = [k for k, q in enumerate(paras) if q[2].startswith("Implications for IS research")][0]
x = x[:paras[i0][0]] + built + x[paras[i1][1]:]
def sub(o, n):
    global x
    eo, en = escape(o), escape(n); assert x.count(eo) == 1, (o[:50], x.count(eo)); x = x.replace(eo, en)
sub("Across fourteen language models, [PENDING: share of raw deference that survives correction; whether the gradients indicate deference or evidence-weighing].",
    "Across fourteen language models and 176,400 answers, correction removes a median 9% of raw deference but 21% to 75% for the five least stable models; stance-following responds to claimed evidence, no model shows pure deference, and larger models are not reliably less deferential.")
sub("and in the requester’s disclosed accuracy, and we show how", "and the requester’s disclosed accuracy, and show how")
sub("We offer an audit protocol that a firm can run on its own decisions and state what it cannot establish.", "We offer an audit protocol and state its limits.")
sub("which s_mix addresses [PENDING: report the difference between the two].", "which s_mix addresses; s_mix exceeds s* by up to 0.15 (Llama-3.1 8B, 0.29 and 0.44) and by at most 0.08 for models with ρ of 0.1 or less.")
sub("Hosted inference does not allow control of", "Ten of the fourteen models answer only about a third to a half of the items correctly, and for three of them (Gemma-3 4B, Ministral 3B, Qwen2.5 7B) ability is indistinguishable from guessing, so their conditional set is partly a product of luck and their conditional measures should be read with the stance-free baseline. Model-level estimates average over serving providers that do not behave alike, and the stance-following rate under rotated letters differs for four models, so part of the measured following is a position effect. The H3 rule labels a model with no stance effect as deference-consistent, which is a limitation of the rule, and the classification of several models changes when one domain is dropped. Stem-level deference is estimated from one draw per stem, which limits the test of Proposition 5. The results describe the model versions and providers available in October 2026. Hosted inference does not allow control of")
open(p, "w", encoding="utf8").write(x)
if os.path.exists(DST): os.remove(DST)
subprocess.run(f"cd {tmp} && zip -qXr {os.path.abspath(DST)} .", shell=True, check=True)
print("wrote", DST)
