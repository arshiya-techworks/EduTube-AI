import os
if not os.getenv("EDUTUBE_NO_DOTENV"):
    _here = os.path.dirname(os.path.dirname(__file__))
    for _p in (os.path.join(_here, ".env"), os.path.join(os.path.dirname(_here), ".env")):
        if os.path.exists(_p):
            for _l in open(_p, encoding="utf-8"):
                _l = _l.strip()
                if _l and not _l.startswith("#") and "=" in _l:
                    _k, _v = _l.split("=", 1)
                    if _v.strip(): os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
