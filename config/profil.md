# Profil de tri

Claude lit ce fichier à chaque passage pour décider ce qui mérite d'être signalé.
Modifie-le librement : c'est lui qui règle la sévérité du filtre.

## Ce qui m'intéresse
- Jeux PC offerts à vie (Epic, Steam, GOG, Prime Gaming…), surtout les jeux connus ou bien notés
- Logiciels / applis payantes offertes (licences à vie, apps iOS/Android normalement payantes)
- Erreurs de prix et prix historiquement bas sur de la tech (PC, composants, audio, photo)
- Vols et voyages à prix aberrants au départ de la France
- Échantillons, abonnements ou services gratuits qui ont une vraie valeur
- **Produits gratuits ou presque une fois les remises cumulées** : ODR / « 100 % remboursé »
  (Envie de Plus, marques), applis de remboursement (Shopmium, Quoty, Coupon Network),
  cagnotte carte de fidélité, cashback (iGraal, Poulpeo, Joko…), coupons. Le cumul peut
  même rapporter de l'argent.

## Ce qui ne m'intéresse pas
- Promos permanentes déguisées (« -70 % » sur un prix barré fictif)
- Codes de réduction génériques, taux de cashback ordinaires, parrainages — **sauf** s'ils
  font partie d'un cumul qui rend le produit gratuit ou presque (voir ci-dessus)
- Jeux mobiles free-to-play, DLC cosmétiques, essais gratuits qui se transforment en abonnement
- Concours / tirages au sort

## Barème de rareté (note de 1 à 10)
- **9-10** : exceptionnel — erreur de prix, produit premium offert, ça arrive quelques fois par an
- **7-8** : très bon — plus bas historique net, jeu AAA ou très bien noté offert
- **5-6** : correct mais courant — ne pas signaler
- **1-4** : bruit

### Cumuls de remises
Pour chaque candidat avec des `signaux` (`rembourse`, `cashback`, `cagnotte`,
`appli_remboursement`…), calcule le **prix net** : prix payé − ODR − remboursement appli
− cagnotte − cashback − coupon, en vérifiant que ces remises sont bien cumulables (une ODR
exclut parfois Shopmium) et encore valables. Barème indicatif :
- net **≤ 0 €** (gratuit ou rémunéré) sur un produit utile : **8-9** (10 si valeur > 30 €)
- net ≤ 20 % du prix habituel sur un produit de marque utile : **7**
- remise cumulée ordinaire : 5-6, ne pas signaler

Dans le digest, détaille le calcul sur une ligne (ex. « 4,99 € − 4,99 € Envie de Plus −
1 € cashback iGraal = −1 € ») et les conditions (enseigne, limite par foyer, date limite
d'achat et de demande de remboursement).

## Recherche active
À chaque passage, lance aussi les recherches de `config/recherches.md` avec WebSearch et
note leurs résultats comme les autres candidats.

Seuil de signalement : **7**. Au-delà de 8 éléments retenus, ne garder que les meilleurs.
Une offre déjà signalée dans un digest précédent ne doit pas être répétée.

## Localisation
France — ignorer les offres réservées à d'autres pays, sauf produits numériques accessibles depuis la France.
