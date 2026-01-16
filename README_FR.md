# Vue d'ensemble du projet

Ce projet est une démonstration technique d'une application SaaS multi-tenant.

Il permet à différents clients (tenants) de rechercher dans leurs propres documents privés tout en garantissant une isolation stricte des données entre clients.

Chaque client :

- Possède ses propres documents
- Ne peut pas voir ou accéder aux documents d'autres clients
- Est identifié uniquement par une clé API sécurisée envoyée automatiquement par l'interface

L'objectif est de démontrer :
✔ Séparation sécurisée des tenants
✔ Logique backend simple et fiable
✔ Interface facile à utiliser pour les utilisateurs non techniques

## Technologies utilisées

- **Backend** : Python, FastAPI
- **Frontend** : React (Vite)
- **Stockage** : Fichiers locaux (dossiers par tenant)
- **Sécurité** : Clé API via en-tête HTTP (X-API-KEY)

## Structure du projet

```
TESTACTUDATA/
├── main.py                 # API Backend
├── requirements.txt        # Dépendances Python
├── documents/
│   ├── tenantA/            # Documents Client A
│   └── tenantB/            # Documents Client B
└── frontend/               # Interface web (React)
```

## Prérequis

Assurez-vous d'avoir installé :

✅ **Python 3.8 ou supérieur**

✅ **Node.js 16 ou supérieur** (avec npm)

Vérifier les versions :

```bash
python --version
node --version
```

## Comment exécuter l'application

### ▶ Étape 1 — Démarrer le Backend

Ouvrez un terminal dans le dossier du projet :

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Le backend fonctionne sur :

**http://localhost:8000**

⚠️ Gardez ce terminal ouvert.

### ▶ Étape 2 — Démarrer le Frontend

Ouvrez un deuxième terminal :

```bash
cd frontend
npm install
npm run dev
```

Ouvrez le navigateur :

**http://localhost:3000**

## Comment utiliser l'application

1. Sélectionnez un client dans le menu déroulant :
   - Client A
   - Client B

2. Tapez une question.

3. Cliquez sur **Search**.

Le système retournera :

- La réponse (si trouvée)
- Le(s) document(s) source(s)

## Exemples de tests

### ✅ Test Client A

Sélectionnez **Client A**, demandez :

```
Quelle est l'exclusion du produit RC Pro ?
```

**Résultat attendu :**

```
Travaux en hauteur au-delà de 3 mètres
```

### ✅ Test Client B

Sélectionnez **Client B**, demandez :

```
Quelle est l'exclusion du produit RC Pro B ?
```

**Résultat attendu :**

```
Sous-traitance non déclarée
```

### 🔒 Test de sécurité

Sélectionnez **Client A**, demandez :

```
Sous-traitance non déclarée
```

**Résultat attendu :**

```
Aucune information disponible pour ce client
```

Cela prouve que l'isolation des tenants fonctionne.

## Isolation des tenants expliquée

L'isolation des tenants signifie que chaque client a son propre espace de données privé.

Comment ce projet garantit l'isolation :

1. L'identité du client est résolue uniquement à partir de l'en-tête HTTP `X-API-KEY`.

2. Le tenant n'est jamais envoyé dans le corps de la requête.

3. Les documents sont physiquement séparés dans des dossiers :
   - `documents/tenantA/`
   - `documents/tenantB/`

4. Le backend charge uniquement le dossier appartenant au tenant authentifié.

5. L'accès inter-tenant est impossible par conception.

## Points de terminaison API

### `GET /`
Vérification de santé

### `POST /search`
**Corps :**
```json
{
  "query": "votre question"
}
```

**En-tête :**
```
X-API-KEY: tenantA_key ou tenantB_key
```

## Arrêter l'application

Appuyez sur :

**CTRL + C**

dans les deux fenêtres de terminal.

## Tests automatisés

Pour exécuter les tests d'isolation des tenants :

```bash
pytest test_tenant_isolation.py -v
```

Ces tests vérifient que :
- Le Client A ne peut pas accéder aux documents du Client B
- Le Client B ne peut pas accéder aux documents du Client A
- Les clés API invalides sont rejetées
- Les attaques de traversée de chemin sont bloquées

## Sécurité et isolation

Ce projet implémente plusieurs couches de sécurité pour garantir l'isolation stricte des tenants :

1. **Résolution centralisée du tenant** : Toute identification passe par `resolve_tenant(api_key)`
2. **Authentification par en-tête uniquement** : Le tenant est déterminé uniquement depuis l'en-tête `X-API-KEY`
3. **Scopage strict des documents** : Les documents sont chargés uniquement depuis `documents/<tenant>/`
4. **Validation défensive** : Vérification des valeurs de tenant et prévention des attaques de traversée de chemin
5. **Tests automatisés** : Tests complets pour vérifier l'isolation

Pour plus de détails, consultez la section "Tenant Isolation Security" dans le README principal.

