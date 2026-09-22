import inspect, enum
from pydantic import BaseModel

lines = []
s_lines = []
def p(*a):
    lines.append(" ".join(str(x) for x in a))
def ps(*a):
    s_lines.append(" ".join(str(x) for x in a))

import app.schemas.risk_opportunity as ros
import app.schemas.decision as ds

def dump_module(mod, tag):
    p("=== %s ENUMS ===" % tag)
    for name in sorted(dir(mod)):
        obj = getattr(mod, name)
        if inspect.isclass(obj) and issubclass(obj, enum.Enum):
            p("enum %s = %r" % (name, [e.value for e in obj]))
    p("=== %s MODELS ===" % tag)
    for name in sorted(dir(mod)):
        obj = getattr(mod, name)
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            p("model %s:" % name)
            for f, m in obj.model_fields.items():
                req = "REQUIRED" if m.is_required() else "optional"
                p("  %s: %s (%s)" % (f, m.annotation, req))

dump_module(ros, "RISK")
dump_module(ds, "DECISION")

import app.intelligence.risk_opportunity as ri
p("=== INTELLIGENCE CONSTANTS ===")
p("ENGINE_VERSION = %r" % getattr(ri, "ENGINE_VERSION", None))
p("RULESET_VERSION = %r" % getattr(ri, "RULESET_VERSION", None))
for n in sorted(dir(ri)):
    if n.isupper() and n not in ("ENGINE_VERSION", "RULESET_VERSION"):
        v = getattr(ri, n)
        if isinstance(v, (str, int, float, bool, tuple, list, set, frozenset, dict)):
            p("%s = %r" % (n, v))

from app.services.risk_opportunity_service import RiskOpportunityService
p("=== SERVICE ===")
p("methods: %r" % [m for m in dir(RiskOpportunityService) if not m.startswith("_")])
try:
    svc = RiskOpportunityService()
    p("init attrs: %r" % {k: v for k, v in vars(svc).items()})
    for m in dir(RiskOpportunityService):
        if not m.startswith("_"):
            fn = getattr(RiskOpportunityService, m)
            if callable(fn):
                try:
                    p("sig %s%s" % (m, inspect.signature(fn)))
                except Exception:
                    pass
except Exception as e:
    p("service init error: %r" % (e,))

try:
    from app.main import app as fastapi_app
    p("=== ROUTES (risk) ===")
    for r in fastapi_app.routes:
        path = getattr(r, "path", "")
        if "risk" in path:
            p("ROUTE %r %s -> %r" % (sorted(getattr(r, "methods", []) or []), path, getattr(r, "response_model", None)))
except Exception as e:
    p("routes error: %r" % (e,))

FNS = ["_weather_signals", "_effective_stage", "_benign_weather_signals", "_signal_evidence",
       "_market_move", "_yield_hint", "_commodity_matches_crop", "_categorical_level",
       "_model_probability", "_grade_risk", "_grade_opportunity", "_confidence",
       "_summary", "_analysis_status", "_assess_data_quality", "_data_quality_notices",
       "_consolidate", "_append_stage_context", "_apply_upstream", "_opportunity",
       "_rule_excess_rainfall", "_rule_heat_stress", "_rule_cold_stress", "_rule_wind_damage",
       "_rule_severe_weather", "_rule_water_stress", "_rule_disease_favourable_weather",
       "_rule_disease_model", "_rule_pest_pressure", "_rule_market_downside", "_rule_market_upside",
       "_rule_yield_market_risk", "_rule_yield_market_opportunity", "_rule_fertilizer_risk",
       "_rule_stage_transition_risk", "_rule_favourable_weather_window", "_rule_irrigation_efficiency",
       "_rule_reduced_disease_pressure", "_rule_reduced_pest_pressure"]
for fn in FNS:
    obj = getattr(ri, fn, None)
    if obj is None:
        ps("MISSING %s" % fn)
        continue
    try:
        ps("----- %s -----" % fn)
        ps(inspect.getsource(obj))
    except Exception as e:
        ps("ERR %s %r" % (fn, e))
cls = getattr(ri, "_AnalysisView", None)
if cls is not None:
    try:
        ps("----- _AnalysisView -----")
        ps(inspect.getsource(cls))
    except Exception as e:
        ps("ERR view %r" % (e,))

with open("_final_probe_out.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
with open("_final_probe_src.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(s_lines))
print("done", len(lines), len(s_lines))
