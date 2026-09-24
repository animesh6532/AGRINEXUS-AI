import inspect, json
from app.schemas import risk_opportunity as rs
from app.schemas import decision as ds

def fields(m):
    out = {}
    for n, f in m.model_fields.items():
        out[n] = ('REQ' if f.is_required() else 'opt')
    return out

info = {}
for name in ['RiskOpportunityContext','Risk','Opportunity','RiskOpportunitySummary','DataQualityNotice','ConflictNotice','RiskOpportunityResponse','RiskOpportunityHealthResponse','RiskOpportunityCategoriesResponse','CategoryInfo']:
    cls = getattr(rs, name)
    info[name] = fields(cls)

enums = {}
for name in dir(rs):
    obj = getattr(rs, name)
    if inspect.isclass(obj) and issubclass(obj, __import__('enum').Enum):
        enums[name] = [ (m.name, m.value) for m in obj ]

farm = {}
for name in ['FarmContext','WeatherContext','MarketContext','CropCalendarContext','MLPrediction','Decision','DecisionResponse','DataQuality']:
    cls = getattr(ds, name)
    farm[name] = fields(cls)

from app.services.risk_opportunity_service import RiskOpportunityService
svc_methods = [m for m,_ in inspect.getmembers(RiskOpportunityService, predicate=inspect.isfunction) if not m.startswith('_')]

from app.api import risk_opportunity as api
routes = [(r.path, sorted(r.methods)) for r in api.router.routes]

print(json.dumps({'schemas': info, 'enums': enums, 'decision': farm, 'svc': svc_methods, 'routes': routes}, indent=1, default=str))
