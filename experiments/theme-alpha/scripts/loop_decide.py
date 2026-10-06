"""Fill the decision line of the LAST card in reports/loop/ITERATIONS.md (LOOP.md step 5).

  python scripts/loop_decide.py "ACCEPT: <reason>. next: <single change>"
"""
import sys

PH = "decision: _agent fills: ACCEPT / REJECT + one-line reason + next single change_"
p = "reports/loop/ITERATIONS.md"
s = open(p, encoding="utf-8").read()
i = s.rfind(PH)
if i < 0:
    raise SystemExit("no open decision placeholder in the last card")
open(p, "w", encoding="utf-8").write(s[:i] + "decision: " + sys.argv[1] + s[i + len(PH):])
print("decision recorded")
