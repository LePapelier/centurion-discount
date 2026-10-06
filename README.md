# centurion-discount

Claude scanne régulièrement des sites de bons plans, des API de jeux offerts et des
newsletters, puis ne te remonte que ce qui est **vraiment** rare.

```
sources.toml ──fetch──▶ candidates.json ──Claude + profil.md──▶ digests/…md + notification
                           ▲ dédoublonné via state/seen.json
```

## Mise en route
1. **Réseau** : dans les réglages de l'environnement cloud, autorise les domaines des
   sources (Network access → Custom) : `www.dealabs.com`, `www.gamerpower.com`,
   `store-site-backend-static.ak.epicgames.com`, `www.reddit.com`,
   `www.giveawayoftheday.com`, `www.secretflying.com`, `kill-the-newsletter.com`.
2. **Profil** : ajuste `config/profil.md` (centres d'intérêt, barème, seuil).
3. **Newsletters** : pour chacune, crée un flux sur kill-the-newsletter.com, abonne-toi
   avec l'adresse fournie et ajoute l'URL du flux dans `config/sources.toml`.
4. **Routine** : crée une routine Claude Code avec le prompt de `ROUTINE.md`
   (ex. 3 fois par jour) et active les notifications.

## Tester
```
python3 scripts/veille.py fetch   # voir ce qui remonte
python3 -m pytest -q tests
```
