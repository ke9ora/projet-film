# Instructions pour publier sur GitHub

## Étape 1 : Créer le dépôt sur GitHub

1. Allez sur https://github.com/new
2. **Repository name** : `exemple-film-graph` (ou le nom de votre choix)
3. **Description** : `Système de recommandation de films avec graphe pondéré`
4. Choisissez **Public** ou **Private**
5. ⚠️ **NE COCHEZ PAS** "Initialize with README" (on a déjà un README)
6. Cliquez sur **Create repository**

## Étape 2 : Connecter le repo local au repo distant

Après avoir créé le repo, GitHub vous donnera une URL. Utilisez-la dans cette commande :

```bash
# Remplacez <votre-username> et <nom-du-repo> par vos valeurs
git remote add origin https://github.com/<votre-username>/<nom-du-repo>.git
```

**Exemple :**
```bash
git remote add origin https://github.com/elora/exemple-film-graph.git
```

## Étape 3 : Pousser le code

```bash
git push -u origin main
```

Si vous avez des erreurs d'authentification, GitHub utilise maintenant des tokens personnels :

1. Allez dans Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Créez un nouveau token avec les permissions `repo`
3. Utilisez le token comme mot de passe lors du push

**Ou utilisez SSH :**

```bash
# Si vous avez configuré SSH avec GitHub
git remote set-url origin git@github.com:<votre-username>/<nom-du-repo>.git
git push -u origin main
```

## Vérification

Après le push, vérifiez que tout est bien en ligne :

```bash
git remote -v
```

Vous devriez voir l'URL de votre repo distant.
