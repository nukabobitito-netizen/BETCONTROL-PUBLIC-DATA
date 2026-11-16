"""BETCONTROL: publiczny ranking PREMATCH Bet365 (Flask Blueprint)."""
import json
import time
from datetime import datetime, timezone, timedelta
from threading import Lock
from urllib.request import Request, urlopen
from flask import Blueprint, Response

prematch_bp = Blueprint("betcontrol_prematch", __name__)
SOURCE = "https://raw.githubusercontent.com/nukabobitito-netizen/BETCONTROL-PUBLIC-DATA/main/bet365_prematch_ranking.json"
_CACHE = {"at": 0.0, "data": None}
_LOCK = Lock()

def _data():
    with _LOCK:
        if _CACHE["data"] is not None and time.monotonic() - _CACHE["at"] < 300:
            return _CACHE["data"], False
        try:
            req = Request(SOURCE, headers={"User-Agent": "BETCONTROL/1.0"})
            with urlopen(req, timeout=6) as res:
                raw = res.read(512_001)
            if len(raw) > 512_000:
                raise ValueError("JSON too large")
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get("drops"), list) or not isinstance(data.get("rises"), list):
                raise ValueError("Invalid ranking format")
            _CACHE.update(at=time.monotonic(), data=data)
            return data, False
        except Exception:
            return _CACHE["data"], True

def _escape(s):
    import html
    return html.escape(str(s), quote=True)

@prematch_bp.route("/ranking-prematch")
def ranking_prematch():
    data, stale = _data()
    css = """body{background:#081a2b;color:#e8f6fa;font:16px system-ui;margin:0;padding:24px}
    main{max-width:1050px;margin:auto}h1{color:#43d9d1}section{margin:24px 0}
    table{width:100%;border-collapse:collapse;background:#10283b;border-radius:12px;overflow:hidden}
    td,th{padding:13px;text-align:left;border-bottom:1px solid #28465a}
    .drop{color:#4de3a1}.rise{color:#ffcb78}.muted{color:#9eb4c5}
    a{color:#43d9d1}@media(max-width:650px){body{padding:12px}td,th{padding:8px;font-size:12px}}"""
    parts = ['<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BETCONTROL — PREMATCH</title>',
             '<style>'+css+'</style><main><h1>BETCONTROL — ranking PREMATCH</h1><p class="muted">Bet365 · piłka nożna · 1X2 FULL_TIME · HOME / AWAY · ostatnie 12 godzin</p>']
    if data is None:
        parts.append('<p>Ranking chwilowo niedostępny. Spróbuj ponownie później.</p>')
    else:
        if stale:
            parts.append('<p class="rise">Uwaga: wyświetlane są ostatnio zapisane dane (aktualizacja nie powiodła się).</p>')
        stamp = data.get("updated_at", "")
        try:
            dt = datetime.fromisoformat(stamp.replace("Z","+00:00")).astimezone(timezone(timedelta(hours=1)))
            stamp = dt.strftime("%d.%m.%Y %H:%M") + " (CET)"
        except (ValueError, TypeError):
            pass
        parts.append('<p class="muted">Aktualizacja: '+_escape(stamp)+'</p>')
        for key, title, klass in (("drops","Spadki kursów","drop"),("rises","Wzrosty kursów","rise")):
            parts.append('<section><h2>'+title+'</h2><table><thead><tr><th>Mecz</th><th>Typ</th><th>Przed</th><th>Po</th><th>Zmiana</th></tr></thead><tbody>')
            rows = data.get(key, [])
            for r in rows:
                if not isinstance(r, dict):
                    continue
                parts.append('<tr><td>'+_escape(r.get("home",""))+' – '+_escape(r.get("away",""))+'</td><td>'+_escape(r.get("selection",""))+'</td><td>'+_escape(r.get("odds_before",""))+'</td><td>'+_escape(r.get("odds_now",""))+'</td><td class="'+klass+'">'+_escape(r.get("change_percent",""))+'%</td></tr>')
            if not rows:
                parts.append('<tr><td colspan="5">Brak zmian kursów</td></tr>')
            parts.append('</tbody></table></section>')
    parts.append('</main></html>')
    return Response(''.join(parts), mimetype="text/html; charset=utf-8")
