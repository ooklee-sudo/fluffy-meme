import os
"""Held-out evaluation of a revised rubric + few-shot prompt.
dev = first 100 rows of the human-coded sample (rubric/examples derived from these only)
test = last 100 rows (never inspected before scoring)."""
import csv, json, os, sys, collections, concurrent.futures as cf
import classify_onet as C
sys.path.insert(0,".")
from agreement import kappa
R=list(csv.DictReader(open("data/human_coding_sample_filled.csv",encoding="utf-8-sig")))
test=[{"id":int(r["id"]),"text":r["task"],"occ":r["occupation"],"h":int(r["score_0_1_2"])} for r in R[100:]]
M={r["id"]:r for r in map(json.loads,open("data/model_labels_sample.jsonl"))}
PROMPT_V2="""You code O*NET task statements for a labor-economics study of how much a task relies on the worker's SIGHT.
Ask: to perform this task as a typical worker in this occupation, how much does the worker have to use their eyes on a concrete physical or visual object, scene, instrument, image, or workpiece?
Score:
2 = Looking is the core of the task: examining, inspecting, observing, diagnosing by sight, reading gauges/instruments, driving or guiding by sight, precise visual positioning/alignment, or designing/laying out physical or visual things.
1 = Hands-on, physical or procedural work where sight is routinely needed but is not the point (operating or repairing machines, installing, cleaning, assembling, handling materials, recording readings, reviewing documents, blueprints or records as part of a larger job).
0 = Abstract, social or administrative work with no concrete visual object: planning, managing, advising, teaching, counselling, negotiating, communicating, scheduling, budgeting, drafting policy, serving on committees, responding to requests.
Use the occupation as context only to imagine what the work physically involves. Judge by the activity, not by single keywords (the word "inspect" in an audit of records or "clean" a room does not by itself make it 2).
Examples (task -> score):
Remove foreign bodies from the eye. -> 2
Start aircraft and observe gauges, meters, and other instruments to detect evidence of malfunctions. -> 2
Diagnose teeth and jaw or other dental-facial abnormalities. -> 2
Inspect parts, equipment, or vehicles for cleanliness, damage, and compliance with standards. -> 2
Observe sets during rehearsals in order to ensure that set elements do not interfere with performance. -> 2
Pull plies from supply racks, and align plies with edges of drums. -> 1
Cut openings and drill holes for fixtures and equipment, using electric drills and routers. -> 1
Overhaul or replace carburetors, blowers, generators, distributors, starters, and pumps. -> 1
Compare information from application to criteria for policy reinstatement, and approve reinstatement when criteria are met. -> 1
Record information, such as the number of products tested, meter readings, or dates and times of product production. -> 1
Clean and clear debris from culverts, catch basins, drop inlets, ditches, and other drain structures. -> 1
Study blueprints, layouts or charts, and job orders for information on specifications and tooling instructions. -> 1
Assist customers by providing information and resolving their complaints. -> 0
Recruit, hire, train, and evaluate primary and supplemental staff. -> 0
Draft contract proposals or counter-proposals for collective bargaining or other labor negotiations. -> 0
Review compiled data on operating costs and revenues to set rates. -> 0
Obtain permits for constructing, upgrading, or operating geothermal power plants. -> 0
Respond to emergency situations, such as emergency medical calls, security calls, or fire alarms. -> 0
Reply with JSON only: {"labels":[{"i":<id>,"s":<0|1|2>}, ...]} covering every id."""
C.PROMPT=PROMPT_V2
key=os.environ["OPENROUTER_API_KEY"]
H=[t["h"] for t in test]
def stats(name,pred):
    b=lambda x:[int(v>0) for v in x]
    print(f"{name:42s} exact {sum(p==h for p,h in zip(pred,H))/len(H):.3f} kappa {kappa(H,pred):.3f} wkappa {kappa(H,pred,1):.3f} bin-kappa {kappa(b(H),b(pred)):.3f} dist {dict(sorted(collections.Counter(pred).items()))}")
print("human test dist",dict(sorted(collections.Counter(H).items())))
for m in [os.environ.get("LLM_MODEL_CHEAP",""),os.environ["LLM_MODEL"]]:
    stats(m+" (v1, held-out)",[M[t["id"]][m] for t in test])
    bs=[test[i:i+20] for i in range(0,100,20)]
    with cf.ThreadPoolExecutor(5) as ex: res=list(ex.map(lambda b:C.call(m,[{"id":t["id"],"text":f'[{t["occ"]}] {t["text"]}'} for t in b],key)[0],bs))
    lab={k:v for r in res for k,v in r.items()}
    pred=[lab[t["id"]] for t in test]; stats(m+" (v2, held-out)",pred)
    json.dump({"model":m,"pred":dict(zip([t["id"] for t in test],pred))},open("data/v2_test_"+m.split("/")[1]+".json","w"))
