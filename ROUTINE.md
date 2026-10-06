# Prompt de la routine

Copie ce texte comme prompt d'une routine Claude Code (nouvelle session à chaque passage,
sur ce dépôt). Il est autonome : il ne suppose aucun contexte précédent.

---

Tu fais la veille « bons plans rares » du dépôt centurion-discount. Lis CLAUDE.md puis :

1. Lance `python3 scripts/veille.py fetch`. Si toutes les sources échouent, arrête-toi et
   résume les erreurs (probablement des domaines bloqués par la politique réseau).
2. Lis `config/profil.md` puis `data/candidates.json`. Ouvre aussi les 3 derniers fichiers
   de `digests/` pour ne pas répéter une offre déjà signalée.
3. Note chaque candidat selon le barème du profil. En cas de doute sur la rareté d'une
   offre prometteuse (≥ 6), vérifie-la avec WebSearch/WebFetch : prix habituel, plus bas
   historique, encore disponible ? Ne retiens que ce qui atteint le seuil du profil.
4. Écris `digests/AAAA-MM-JJ-HHhMM.md` (heure de Paris) au format décrit dans CLAUDE.md,
   même si rien n'est retenu (le digest dit alors « Rien d'exceptionnel » et liste les
   sources en échec).
5. Lance `python3 scripts/veille.py commit`, puis commite `digests/` et `state/seen.json`
   et pousse sur la branche par défaut.
6. Termine par un résumé de 5 lignes max : les trouvailles retenues avec leur note et leur
   lien, ou « Rien d'exceptionnel cette fois ». Ce résumé est ce qui m'est notifié.
