# BETCONTROL — ranking PREMATCH Bet365

Publiczne dane: `bet365_prematch_ranking.json`.

## Integracja ze stroną Flask

Plik `betcontrol_prematch.py` w tym repozytorium to samodzielny Blueprint Flask. Skopiuj go do katalogu aplikacji na bot.oazamody.pl i zarejestruj:

```python
from betcontrol_prematch import prematch_bp
app.register_blueprint(prematch_bp)
```

Adres rankingu: `/ranking-prematch`. Dane są pobierane z publicznego JSON w GitHub, bez dodatkowych wywołań PulseScore. Cache trwa 5 minut; awaria pobierania zwraca informację o niedostępności, a nie fikcyjne wyniki. Nie wymaga tokenu GitHub.