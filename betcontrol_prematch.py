"""BETCONTROL — ranking zmian kursów przedmeczowych Bet365."""
import json
import time
from datetime import datetime
from threading import Lock
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from flask import Blueprint, Response, render_template_string

prematch_bp = Blueprint("betcontrol_prematch", __name__)
SOURCE = "https://raw.githubusercontent.com/nukabobitito-netizen/BETCONTROL-PUBLIC-DATA/main/bet365_prematch_ranking.json"
_CACHE = {"at": 0.0, "data": None}
_LOCK = Lock()

def _data():
    with _LOCK:
        if _CACHE["data"] is not None and time.monotonic() - _CACHE["at"] < 300:
            return _CACHE["data"], False
        try:
            req = Request(SOURCE, headers={"User-Agent": "BETCONTROL/3.0", "Cache-Control": "no-cache"})
            with urlopen(req, timeout=8) as res:
                raw = res.read(512001)
            if len(raw) > 512000:
                raise ValueError("Ranking JSON too large")
            data = json.loads(raw)
            if not isinstance(data, dict) or not all(isinstance(data.get(k), list) for k in ("drops", "rises")):
                raise ValueError("Invalid ranking JSON")
            _CACHE.update(at=time.monotonic(), data=data)
            return data, False
        except Exception:
            return _CACHE["data"], True

HTML = r"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BETCONTROL | Ranking kursów przedmeczowych</title>
<style>
:root{color-scheme:dark;--bg:#071422;--panel:#0d2033;--line:#294058;--turquoise:#24c6bd;--text:#f5f8fc;--muted:#b1c2d4;--green:#75d6a5}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
main{width:min(1200px,calc(100% - 28px));margin:24px auto 65px}
h1{font-size:clamp(24px,4vw,34px);margin:0 0 8px}h2{font-size:19px;margin:0 0 16px}
p{color:var(--muted);line-height:1.5}.accent{color:var(--turquoise)}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px;margin:20px 0}
.filters{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
label{display:grid;gap:7px;color:var(--muted);font-size:13px}select,input{width:100%;min-width:0;background:#071827;border:1px solid #3a536b;border-radius:9px;padding:11px;color:var(--text);font:inherit}
input[type=range]{padding:8px 0;accent-color:var(--turquoise)}button{background:#133b4c;border:1px solid var(--turquoise);color:#fff;border-radius:9px;padding:11px 18px;cursor:pointer}
.summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.metric{border:1px solid var(--line);border-radius:12px;padding:16px;background:#081b2c}.metric small{display:block;color:var(--muted);margin-bottom:9px}.metric strong{font-size:25px}.drop{color:var(--green)}.rise{color:#ffc27d}
table{width:100%;border-collapse:collapse}th,td{padding:12px 10px;text-align:left;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:500;font-size:12px}td small{display:block;color:var(--muted);margin-top:5px}.scroll{overflow-x:auto}
.empty{color:var(--muted);padding:25px 10px;text-align:center}.warn{color:#ffc27d}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
@media(max-width:780px){.filters{grid-template-columns:repeat(2,minmax(0,1fr))}.panel{padding:14px}.summary{grid-template-columns:1fr}}
@media(max-width:420px){.filters{grid-template-columns:1fr}th,td{padding:10px 6px;font-size:12px}}
</style></head><body><main>
<h1>BET<span class="accent">CONTROL</span></h1>
<p>Ranking zmian kursów przedmeczowych · Bet365 · piłka nożna · 1X2 FULL_TIME · HOME / AWAY · historia 12 h</p>
<p>Aktualizacja danych: <strong>{{ stamp }}</strong>{% if stale %} <span class="warn">· Dane z pamięci podręcznej</span>{% endif %}</p>
{% if unavailable %}<section class="panel warn">Ranking jest chwilowo niedostępny. Spróbuj ponownie później.</section>{% else %}
<section class="panel"><h2>Filtry kursów przedmeczowych</h2>
<div class="filters">
<label>Region<select id="region"><option value="">Wszystkie regiony</option></select></label>
<label>Liga<select id="league"><option value="">Wszystkie ligi</option></select></label>
<label>Selekcja<select id="side"><option value="">HOME i AWAY</option><option value="HOME">HOME</option><option value="AWAY">AWAY</option></select></label>
<label>Kierunek<select id="direction"><option value="">Spadki i wzrosty</option><option value="drop">Spadki</option><option value="rise">Wzrosty</option></select></label>
<label>Kurs od<input id="minOdds" type="number" min="1.01" max="100" step=".01" placeholder="1.01"></label>
<label>Kurs do<input id="maxOdds" type="number" min="1.01" max="100" step=".01" placeholder="100.00"></label>
<label>Minimalna zmiana: <span id="percentValue">0%</span><input id="percent" type="range" min="0" max="100" step="1" value="0"></label>
<label>Szukaj meczu<input id="search" type="search" placeholder="Drużyna lub liga"></label>
</div><div class="toolbar" style="margin-top:16px"><span id="count" style="color:var(--muted)"></span><button type="button" id="reset">Wyczyść filtry</button></div></section>
<section class="summary">
<div class="metric"><small>↓ Największy spadek</small><strong id="topDrop" class="drop">Brak danych</strong><p id="topDropMatch"></p></div>
<div class="metric"><small>↑ Największy wzrost</small><strong id="topRise" class="rise">Brak danych</strong><p id="topRiseMatch"></p></div>
</section>
<section class="panel"><h2>Zmiany kursów</h2><div class="scroll"><table><thead><tr><th>Mecz / liga</th><th>Typ</th><th>Przed</th><th>Teraz</th><th>Zmiana</th></tr></thead><tbody id="rows"></tbody></table></div><p id="empty" class="empty" hidden>Brak zmian kursów spełniających kryteria.</p></section>
{% endif %}
</main>
{% if not unavailable %}
<script id="ranking-data" type="application/json">{{ payload | safe }}</script>
<script>
(()=>{
const data=JSON.parse(document.getElementById('ranking-data').textContent);
const all=[...(data.drops||[]).map(x=>({...x,direction:'drop'})),...(data.rises||[]).map(x=>({...x,direction:'rise'}))].filter(x=>x&&typeof x==='object');
const $=id=>document.getElementById(id);
const controls=['region','league','side','direction','minOdds','maxOdds','percent','search'];
const clean=x=>String(x??'').trim();
const num=x=>Number(x);
function fill(id,values){const el=$(id);[...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pl')).forEach(v=>{const opt=document.createElement('option');opt.value=v;opt.textContent=v;el.appendChild(opt)})}
fill('region',all.map(x=>clean(x.region)));fill('league',all.map(x=>clean(x.league)));
function cell(tr,value,cls){const td=document.createElement('td');td.textContent=value;if(cls)td.className=cls;tr.appendChild(td);return td}
function render(){
$('percentValue').textContent=$('percent').value+'%';
const min=$('minOdds').value===''?1.01:num($('minOdds').value);
const max=$('maxOdds').value===''?100:num($('maxOdds').value);
const q=$('search').value.toLocaleLowerCase('pl').trim();
const rows=all.filter(x=>(!$('region').value||clean(x.region)===$('region').value)&&(!$('league').value||clean(x.league)===$('league').value)&&(!$('side').value||x.selection===$('side').value)&&(!$('direction').value||x.direction===$('direction').value)&&num(x.odds_now)>=min&&num(x.odds_now)<=max&&Math.abs(num(x.change_percent))>=num($('percent').value)&&(!q||[x.home,x.away,x.league].some(v=>clean(v).toLocaleLowerCase('pl').includes(q))));
rows.sort((a,b)=>Math.abs(num(b.change_percent))-Math.abs(num(a.change_percent)));
$('count').textContent='Wyniki: '+rows.length;
const body=$('rows');body.replaceChildren();$('empty').hidden=rows.length!==0;
rows.forEach(x=>{const tr=document.createElement('tr');const match=cell(tr,clean(x.home)+' – '+clean(x.away));if(x.league){const small=document.createElement('small');small.textContent=[x.region,x.league].filter(Boolean).join(' · ');match.appendChild(small)}cell(tr,clean(x.selection));cell(tr,clean(x.odds_before));cell(tr,clean(x.odds_now));cell(tr,(num(x.change_percent)>0?'+':'')+clean(x.change_percent)+'%',x.direction==='drop'?'drop':'rise');body.appendChild(tr)});
for(const [kind,valueId,matchId] of [['drop','topDrop','topDropMatch'],['rise','topRise','topRiseMatch']]){
const item=rows.filter(x=>x.direction===kind).sort((a,b)=>Math.abs(num(b.change_percent))-Math.abs(num(a.change_percent)))[0];
$(valueId).textContent=item?(num(item.change_percent)>0?'+':'')+item.change_percent+'%':'Brak danych';
$(matchId).textContent=item?clean(item.home)+' – '+clean(item.away):'Brak zmian w wybranych filtrach';
}
}
controls.forEach(id=>$(id).addEventListener('input',render));
$('reset').addEventListener('click',()=>{controls.forEach(id=>{$(id).value=id==='percent'?'0':''});render()});
render();
})();
</script>{% endif %}</body></html>"""

@prematch_bp.route("/ranking-prematch")
def ranking_prematch():
    data, stale = _data()
    stamp = "Brak danych"
    if data:
        try:
            stamp = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y %H:%M")
        except (KeyError, ValueError, TypeError):
            pass
    payload = json.dumps(data or {}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return Response(render_template_string(HTML, stamp=stamp, stale=stale, unavailable=data is None, payload=payload), mimetype="text/html; charset=utf-8")
