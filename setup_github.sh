#!/bin/bash
# Script pour configurer le repo GitHub

echo "🚀 Configuration du dépôt GitHub"
echo ""

# Vérifier si un remote existe déjà
if git remote | grep -q origin; then
    echo "⚠️  Un remote 'origin' existe déjà :"
    git remote -v
    echo ""
    read -p "Voulez-vous le remplacer ? (o/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        git remote remove origin
    else
        echo "❌ Annulé"
        exit 1
    fi
fi

# Demander l'URL du repo
echo "📝 Entrez l'URL de votre repo GitHub :"
echo "   Exemple: https://github.com/votre-username/exemple-film-graph.git"
read -p "URL: " repo_url

if [ -z "$repo_url" ]; then
    echo "❌ URL vide, annulé"
    exit 1
fi

# Ajouter le remote
echo ""
echo "🔗 Ajout du remote..."
git remote add origin "$repo_url"

# Afficher les remotes
echo ""
echo "✅ Remote configuré :"
git remote -v

# Proposer de pousser
echo ""
read -p "Voulez-vous pousser le code maintenant ? (o/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Oo]$ ]]; then
    echo ""
    echo "📤 Push vers GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Code poussé avec succès !"
        echo "🌐 Votre repo est disponible sur GitHub"
    else
        echo ""
        echo "❌ Erreur lors du push"
        echo "💡 Vérifiez votre authentification GitHub (token ou SSH)"
    fi
else
    echo ""
    echo "💡 Pour pousser plus tard, utilisez :"
    echo "   git push -u origin main"
fi
