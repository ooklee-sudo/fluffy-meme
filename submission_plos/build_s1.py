from docx import Document
from docx.shared import Pt
d=Document(); st=d.styles['Normal']; st.font.name='Times New Roman'; st.font.size=Pt(12)
def P(t,b=False):
    p=d.add_paragraph(); r=p.add_run(t); r.bold=b; return p
P("S1 Appendix. Numerical comparative statics of the refresh model",True)
P("Does Release Timing in the LLM Software Ecosystem Respond to Accumulating Degradation? An Empirical Study of Open-Source Repositories and Public Chat Logs")
P("Ook Lee, Yeeun Nam")
P("Purpose",True)
P("The Methods section states that, over a wide range of parameter values, the optimal drift threshold of the refresh model increases with the refresh cost and with the speed of drift and decreases with the discount factor. This appendix gives the values behind that statement. They are numerical regularities from the benchmark model and are not proved results.")
P("Computation",True)
P("The model is the one defined in the Methods section: the drift state x takes integer values from 0 to 80 (capped at 80); each week drift advances by a Poisson(μ) increment; errors arrive at rate λ₀ + γx with unit cost c = 1; a refresh costs RC, resets drift to zero and leaves the error rate at λ₀; and payoffs carry a Type I extreme-value shock, so the refresh probability in state x is logistic in the difference between the values of refreshing and keeping. The value function was found by value iteration (tolerance 10⁻¹⁰). The threshold reported is the smallest drift x at which the probability of a refresh exceeds 0.5. The baseline parameters are γ = 0.5, λ₀ = 5, μ = 1, RC = 40 and discount factor β = 0.95, which give a threshold of 14. In each table one parameter is varied and the others are held at their baseline values.")
def table(cap,header,row):
    P(cap,True)
    t=d.add_table(rows=2,cols=len(header)); t.style='Table Grid'
    for i,h in enumerate(header): t.rows[0].cells[i].text=h
    for i,v in enumerate(row): t.rows[1].cells[i].text=v
    d.add_paragraph()
table("Table A. Threshold by refresh cost",["Refresh cost RC","10","20","40","80","160"],["Optimal drift threshold","7","10","14","21","32"])
table("Table B. Threshold by speed of drift",["Drift speed μ","0.5","1.0","1.5","2.0"],["Optimal drift threshold","11","14","17","19"])
table("Table C. Threshold by discount factor",["Discount factor β","0.90","0.95","0.99"],["Optimal drift threshold","16","14","13"])
P("Reproduction",True)
P("The values are written to the fields cf_RC, cf_mu and cf_beta of results.json by retraining_rust/rust_retrain.py in the replication package (S2 File; https://doi.org/10.5281/zenodo.23863950).")
d.save('/home/user/fluffy-meme/submission_plos/S1_Appendix.docx')
