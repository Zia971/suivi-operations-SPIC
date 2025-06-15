"""
Application SPIC - Suivi des Opérations Immobilières
Interface Streamlit avec Vue Manager, Vue Chargé et Fiche Détail
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import base64
from io import BytesIO
import json

# Imports des modules locaux
import config
import database
import utils

def main():
    """Point d'entrée principal de l'application"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="SPIC - Suivi Opérations",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personnalisé pour le design
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .status-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-etude { background-color: #fff3cd; color: #856404; }
    .status-consultation { background-color: #d1ecf1; color: #0c5460; }
    .status-travaux { background-color: #f8d7da; color: #721c24; }
    .status-livre { background-color: #d4edda; color: #155724; }
    .status-cloture { background-color: #e2e3e5; color: #383d41; }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialisation de la base de données
    if 'db' not in st.session_state:
        st.session_state.db = database.DatabaseManager()
    
    # Navigation principale
    st.sidebar.title("🏗️ SPIC Navigation")
    
    pages = {
        "🎯 Vue Manager": "manager",
        "👷 Vue Chargé": "charge",
        "➕ Nouvelle Opération": "nouvelle",
        "📋 Fiche Détail": "detail"
    }
    
    page = st.sidebar.selectbox("Choisir une vue", list(pages.keys()))
    
    # Affichage des pages
    if pages[page] == "manager":
        page_manager()
    elif pages[page] == "charge":
        page_charge()
    elif pages[page] == "nouvelle":
        page_nouvelle_operation()
    elif pages[page] == "detail":
        page_detail_operation()

def page_manager():
    """Vue Manager - Tableau de bord global"""
    
    st.markdown('<h1 class="main-header">🎯 Tableau de Bord Manager</h1>', unsafe_allow_html=True)
    
    # Récupération des données
    db = st.session_state.db
    operations = db.get_operations()
    
    if not operations:
        st.warning("Aucune opération trouvée. Créez votre première opération !")
        return
    
    df_operations = pd.DataFrame(operations)
    
    # KPI principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_ops = len(df_operations)
        st.metric("Total Opérations", total_ops, delta=None)
    
    with col2:
        avg_progress = df_operations['pourcentage_avancement'].mean()
        st.metric("Avancement Moyen", f"{avg_progress:.1f}%", delta=None)
    
    with col3:
        ops_en_cours = len(df_operations[df_operations['statut_principal'].str.contains('travaux|consultation', na=False)])
        st.metric("En Cours", ops_en_cours, delta=None)
    
    with col4:
        ops_bloquees = len(df_operations[df_operations['statut_principal'].str.contains('Bloqué', na=False)])
        st.metric("🔴 Bloquées", ops_bloquees, delta=None)
    
    st.markdown("---")
    
    # Graphiques
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Répartition par Statut")
        statut_counts = df_operations['statut_principal'].value_counts()
        fig_statuts = px.pie(
            values=statut_counts.values,
            names=statut_counts.index,
            title="Distribution des Statuts"
        )
        st.plotly_chart(fig_statuts, use_container_width=True)
    
    with col_right:
        st.subheader("📈 Répartition par Type")
        type_counts = df_operations['type_operation'].value_counts()
        fig_types = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title="Opérations par Type"
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Top 3 opérations à risque
    st.subheader("⚠️ Top 3 Opérations à Risque")
    
    # Calcul du risque
    df_risque = df_operations.copy()
    df_risque['score_risque'] = (
        (100 - df_risque['pourcentage_avancement']) * 0.7 +
        df_risque['statut_principal'].str.contains('Bloqué|retard', na=False).astype(int) * 30
    )
    
    top_risques = df_risque.nlargest(3, 'score_risque')[['nom', 'responsable_aco', 'statut_principal', 'pourcentage_avancement']]
    
    for idx, (_, row) in enumerate(top_risques.iterrows()):
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            st.write(f"**{idx+1}. {row['nom']}**")
        with col2:
            st.write(f"ACO: {row['responsable_aco']}")
        with col3:
            st.write(f"Avancement: {row['pourcentage_avancement']:.1f}%")
    
    # Filtres avancés
    st.markdown("---")
    st.subheader("🔍 Filtres Avancés")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filtre_type = st.selectbox("Type d'opération", ["Tous"] + list(df_operations['type_operation'].unique()))
    
    with col_f2:
        filtre_statut = st.selectbox("Statut", ["Tous"] + list(df_operations['statut_principal'].unique()))
    
    with col_f3:
        filtre_aco = st.selectbox("Responsable ACO", ["Tous"] + list(df_operations['responsable_aco'].unique()))
    
    # Application des filtres
    df_filtre = df_operations.copy()
    
    if filtre_type != "Tous":
        df_filtre = df_filtre[df_filtre['type_operation'] == filtre_type]
    if filtre_statut != "Tous":
        df_filtre = df_filtre[df_filtre['statut_principal'] == filtre_statut]
    if filtre_aco != "Tous":
        df_filtre = df_filtre[df_filtre['responsable_aco'] == filtre_aco]
    
    # Tableau des opérations filtrées
    if len(df_filtre) > 0:
        st.subheader(f"📋 Opérations ({len(df_filtre)} résultats)")
        
        # Préparation des données pour affichage
        df_display = df_filtre[['nom', 'type_operation', 'statut_principal', 'responsable_aco', 'commune', 'pourcentage_avancement']].copy()
        df_display.columns = ['Nom', 'Type', 'Statut', 'ACO', 'Commune', 'Avancement %']
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.warning("Aucune opération ne correspond aux filtres sélectionnés.")

def page_charge():
    """Vue Chargé d'Opération - Interface principale pour les ACO"""
    
    st.markdown('<h1 class="main-header">👷 Vue Chargé d\'Opération</h1>', unsafe_allow_html=True)
    
    # Sélection du responsable
    responsables = config.INTERVENANTS.get('ACO', [])
    responsable_selectionne = st.sidebar.selectbox("Choisir l'ACO", responsables)
    
    if not responsable_selectionne:
        st.warning("Veuillez sélectionner un responsable ACO.")
        return
    
    # Récupération des opérations du responsable
    db = st.session_state.db
    operations = db.get_operations(responsable=responsable_selectionne)
    
    if not operations:
        st.info(f"Aucune opération trouvée pour {responsable_selectionne}")
        return
    
    st.subheader(f"📋 Opérations de {responsable_selectionne} ({len(operations)} opérations)")
    
    # Affichage des opérations sous forme de cartes
    for i in range(0, len(operations), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(operations):
                op = operations[i + j]
                
                with col:
                    # Couleur selon le statut
                    statut_color = {
                        "🟡 À l'étude": "#fff3cd",
                        "🛠️ En consultation": "#d1ecf1", 
                        "🚧 En travaux": "#f8d7da",
                        "📦 Livré": "#d4edda",
                        "✅ Clôturé": "#e2e3e5"
                    }.get(op['statut_principal'], "#ffffff")
                    
                    st.markdown(f"""
                    <div style="background-color: {statut_color}; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                        <h4>{op['nom']}</h4>
                        <p><strong>Type:</strong> {op['type_operation']}</p>
                        <p><strong>Statut:</strong> {op['statut_principal']}</p>
                        <p><strong>Commune:</strong> {op.get('commune', 'N/A')}</p>
                        <p><strong>Avancement:</strong> {op['pourcentage_avancement']:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Bouton pour accéder au détail
                    if st.button(f"Voir détail", key=f"detail_{op['id']}"):
                        st.session_state.operation_selectionnee = op['id']
                        st.rerun()

def page_nouvelle_operation():
    """Page de création d'une nouvelle opération"""
    
    st.markdown('<h1 class="main-header">➕ Nouvelle Opération</h1>', unsafe_allow_html=True)
    
    with st.form("nouvelle_operation"):
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom de l'opération *", placeholder="Ex: Résidence Les Palmiers")
            type_operation = st.selectbox("Type d'opération *", config.TYPES_OPERATIONS)
            responsable_aco = st.selectbox("Responsable ACO *", config.INTERVENANTS.get('ACO', []))
            commune = st.text_input("Commune", placeholder="Ex: Les Abymes")
        
        with col2:
            promoteur = st.text_input("Promoteur/Partenaire", placeholder="Ex: SEMAG")
            nb_logements = st.number_input("Nombre de logements", min_value=0, value=0)
            budget_total = st.number_input("Budget total (€)", min_value=0.0, value=0.0, step=1000.0)
            
        st.markdown("---")
        
        # Répartition des logements
        st.subheader("Répartition des logements")
        col_lls, col_llts, col_pls = st.columns(3)
        
        with col_lls:
            nb_lls = st.number_input("LLS", min_value=0, value=0)
        with col_llts:
            nb_llts = st.number_input("LLTS", min_value=0, value=0)
        with col_pls:
            nb_pls = st.number_input("PLS", min_value=0, value=0)
        
        submitted = st.form_submit_button("Créer l'opération", type="primary")
        
        if submitted:
            if not nom or not type_operation or not responsable_aco:
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                try:
                    db = st.session_state.db
                    operation_id = db.create_operation(
                        nom=nom,
                        type_operation=type_operation,
                        responsable_aco=responsable_aco,
                        commune=commune,
                        promoteur=promoteur,
                        nb_logements_total=nb_logements,
                        nb_lls=nb_lls,
                        nb_llts=nb_llts,
                        nb_pls=nb_pls,
                        budget_total=budget_total
                    )
                    
                    st.success(f"✅ Opération '{nom}' créée avec succès ! (ID: {operation_id})")
                    st.info("Les phases ont été automatiquement générées selon le type d'opération.")
                        
                except Exception as e:
                    st.error(f"Erreur lors de la création : {str(e)}")

def page_detail_operation():
    """Fiche détail d'une opération avec 5 onglets"""
    
    # Sélection de l'opération
    if 'operation_selectionnee' not in st.session_state:
        st.subheader("Sélection d'une opération")
        
        db = st.session_state.db
        operations = db.get_operations()
        
        if not operations:
            st.warning("Aucune opération disponible. Créez d'abord une opération.")
            return
        
        options = {f"{op['nom']} ({op['type_operation']})": op['id'] for op in operations}
        selection = st.selectbox("Choisir une opération", list(options.keys()))
        
        if st.button("Accéder au détail"):
            st.session_state.operation_selectionnee = options[selection]
            st.rerun()
        return
    
    # Récupération des détails de l'opération
    operation_id = st.session_state.operation_selectionnee
    db = st.session_state.db
    
    operation = db.get_operation_detail(operation_id)
    if not operation:
        st.error("Opération introuvable")
        return
    
    # En-tête de l'opération
    st.markdown(f'<h1 class="main-header">📋 {operation["nom"]}</h1>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Type", operation['type_operation'])
    with col2:
        st.metric("Statut", operation['statut_principal'])
    with col3:
        st.metric("ACO", operation['responsable_aco'])
    with col4:
        st.metric("Avancement", f"{operation['pourcentage_avancement']:.1f}%")
    
    # Onglets de détail
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📌 Phases", "💬 Journal", "💰 Finances", "📎 Fichiers", "🧠 Timeline"])
    
    with tab1:
        render_phases_tab(operation_id)
    
    with tab2:
        render_journal_tab(operation_id)
    
    with tab3:
        render_finances_tab(operation_id)
    
    with tab4:
        render_fichiers_tab(operation_id)
    
    with tab5:
        render_timeline_tab(operation_id)

def render_phases_tab(operation_id):
    """Onglet de gestion des phases"""
    
    db = st.session_state.db
    phases = db.get_phases_by_operation(operation_id)
    
    if not phases:
        st.warning("Aucune phase trouvée pour cette opération")
        return
    
    st.subheader("📌 Gestion des Phases")
    
    # Affichage des phases avec possibilité de modification
    phases_modifiees = []
    
    for phase in phases:
        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
        
        with col1:
            est_validee = st.checkbox("", value=phase.get('est_validee', False), key=f"phase_{phase['id']}")
        
        with col2:
            st.write(f"**{phase.get('sous_phase', 'Phase sans nom')}**")
            if phase.get('commentaire'):
                st.caption(phase.get('commentaire', ''))
        
        with col3:
            date_debut = st.date_input(
                "Début", 
                value=None,
                key=f"debut_{phase['id']}"
            )
        
        with col4:
            date_fin = st.date_input(
                "Fin", 
                value=None,
                key=f"fin_{phase['id']}"
            )
        
        with col5:
            # Couleur selon validation et dates
            if est_validee:
                couleur = "🟢"  # Vert - Validée
            elif date_fin and date_fin < datetime.now().date():
                couleur = "🔴"  # Rouge - En retard
            elif date_fin and (date_fin - datetime.now().date()).days <= 7:
                couleur = "🟠"  # Orange - Échéance proche
            else:
                couleur = "🟡"  # Jaune - En cours
            
            st.write(couleur)
        
        # Stockage des modifications
        if est_validee != phase.get('est_validee', False):
            phases_modifiees.append({
                'id': phase['id'],
                'est_validee': est_validee,
                'date_debut_prevue': str(date_debut) if date_debut else None,
                'date_fin_prevue': str(date_fin) if date_fin else None
            })
    
    # Bouton de sauvegarde
    if phases_modifiees:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            try:
                for phase_modif in phases_modifiees:
                    db.update_phase(
                        phase_id=phase_modif['id'],
                        est_validee=phase_modif['est_validee'],
                        date_debut_prevue=phase_modif['date_debut_prevue'],
                        date_fin_prevue=phase_modif['date_fin_prevue']
                    )
                
                # Mise à jour du pourcentage d'avancement
                phases_actualisees = db.get_phases_by_operation(operation_id)
                nouveau_pourcentage = utils.calculate_progress(phases_actualisees)
                db.update_operation_progress(operation_id, nouveau_pourcentage)
                
                # Ajout dans le journal
                db.add_journal_entry(
                    operation_id=operation_id,
                    auteur="Système",
                    type_action="MODIFICATION",
                    contenu=f"Mise à jour de {len(phases_modifiees)} phase(s)"
                )
                
                st.success("✅ Modifications sauvegardées !")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde : {str(e)}")

def render_journal_tab(operation_id):
    """Onglet journal de suivi"""
    
    st.subheader("💬 Journal de Suivi")
    
    db = st.session_state.db
    
    # Formulaire de nouvelle entrée
    with st.form("nouvelle_entree_journal"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            contenu = st.text_area("Nouvelle entrée", placeholder="Décrivez l'action ou l'événement...")
        
        with col2:
            auteur = st.text_input("Auteur", value="ACO")
            type_action = st.selectbox("Type", ["INFO", "ALERTE", "VALIDATION", "PROBLEME"])
        
        if st.form_submit_button("Ajouter", type="primary"):
            if contenu:
                try:
                    db.add_journal_entry(
                        operation_id=operation_id,
                        auteur=auteur,
                        type_action=type_action,
                        contenu=contenu
                    )
                    st.success("✅ Entrée ajoutée au journal")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
            else:
                st.warning("Veuillez saisir un contenu")
    
    # Affichage de l'historique
    st.markdown("---")
    journal_entries = db.get_journal_by_operation(operation_id)
    
    if journal_entries:
        st.subheader("📜 Historique")
        
        for entry in journal_entries:
            # Couleur selon le type
            couleur = {
                "INFO": "#d1ecf1",
                "ALERTE": "#f8d7da", 
                "VALIDATION": "#d4edda",
                "PROBLEME": "#f5c6cb"
            }.get(entry['type_action'], "#ffffff")
            
            st.markdown(f"""
            <div style="background-color: {couleur}; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{entry['type_action']}</strong>
                    <small>{entry['date_saisie']} - {entry['auteur']}</small>
                </div>
                <p style="margin: 0.5rem 0 0 0;">{entry['contenu']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucune entrée dans le journal")

def render_finances_tab(operation_id):
    """Onglet suivi financier"""
    
    st.subheader("💰 Suivi Financier")
    
    db = st.session_state.db
    
    # Formulaire nouveau mouvement
    with st.form("nouveau_mouvement"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            type_mouvement = st.selectbox("Type", ["engagement", "mandat", "solde", "revision", "avenant"])
            montant_ht = st.number_input("Montant HT (€)", min_value=0.0, step=100.0)
        
        with col2:
            date_mouvement = st.date_input("Date", value=datetime.now().date())
            fournisseur = st.text_input("Entreprise/Fournisseur")
        
        with col3:
            numero_facture = st.text_input("N° Facture")
            commentaire = st.text_area("Commentaire")
        
        if st.form_submit_button("Ajouter mouvement", type="primary"):
            if montant_ht > 0:
                try:
                    db.add_finance_entry(
                        operation_id=operation_id,
                        type_mouvement=type_mouvement,
                        montant_ht=montant_ht,
                        montant_ttc=montant_ht * 1.20,  # TVA 20%
                        date_mouvement=str(date_mouvement),
                        fournisseur_entreprise=fournisseur,
                        numero_facture=numero_facture,
                        commentaire=commentaire
                    )
                    st.success("✅ Mouvement financier ajouté")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
            else:
                st.warning("Veuillez saisir un montant")
    
    # Affichage des mouvements
    st.markdown("---")
    mouvements = db.get_finances_by_operation(operation_id)
    
    if mouvements:
        # Totaux par type
        df_mouvements = pd.DataFrame(mouvements)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_engagements = df_mouvements[df_mouvements['type_mouvement'] == 'engagement']['montant_ht'].sum()
            st.metric("Engagements", f"{total_engagements:,.2f} €")
        
        with col2:
            total_mandats = df_mouvements[df_mouvements['type_mouvement'] == 'mandat']['montant_ht'].sum()
            st.metric("Mandats", f"{total_mandats:,.2f} €")
        
        with col3:
            total_soldes = df_mouvements[df_mouvements['type_mouvement'] == 'solde']['montant_ht'].sum()
            st.metric("Soldes", f"{total_soldes:,.2f} €")
        
        # Tableau détaillé
        st.subheader("📊 Détail des mouvements")
        
        df_display = df_mouvements[['date_mouvement', 'type_mouvement', 'montant_ht', 'fournisseur_entreprise', 'commentaire']].copy()
        df_display.columns = ['Date', 'Type', 'Montant HT', 'Entreprise', 'Commentaire']
        df_display['Montant HT'] = df_display['Montant HT'].apply(lambda x: f"{x:,.2f} €")
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Aucun mouvement financier enregistré")

def render_fichiers_tab(operation_id):
    """Onglet gestion des fichiers"""
    
    st.subheader("📎 Pièces Jointes")
    
    db = st.session_state.db
    
    # Upload de nouveaux fichiers
    with st.form("upload_fichier"):
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choisir un fichier",
                type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png', 'jpeg']
            )
            categorie = st.selectbox("Catégorie", [
                "PC - Permis de construire",
                "DCE - Dossier consultation",
                "Marché - Contrats",
                "PV - Procès verbal",
                "Facture - Facturation",
                "DOE - Dossier ouvrage",
                "Autre"
            ])
        
        with col2:
            description = st.text_area("Description", placeholder="Décrivez le contenu du fichier")
        
        if st.form_submit_button("📤 Uploader", type="primary"):
            if uploaded_file:
                try:
                    # Encodage en base64
                    file_bytes = uploaded_file.read()
                    encoded_content = base64.b64encode(file_bytes).decode()
                    
                    # Validation de la taille (max 10MB)
                    if len(file_bytes) > 10 * 1024 * 1024:
                        st.error("Fichier trop volumineux (max 10MB)")
                    else:
                        db.add_file(
                            operation_id=operation_id,
                            nom_fichier=uploaded_file.name,
                            contenu_base64=encoded_content,
                            type_mime=uploaded_file.type,
                            taille_bytes=len(file_bytes),
                            categorie=categorie,
                            description=description,
                            uploade_par="ACO"
                        )
                        st.success("✅ Fichier uploadé avec succès")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Erreur upload : {str(e)}")
            else:
                st.warning("Veuillez sélectionner un fichier")

    # Liste des fichiers
    st.markdown("---")
    fichiers = db.get_files_by_operation(operation_id)
    
    if fichiers:
        st.subheader("📁 Fichiers disponibles")
        
        for fichier in fichiers:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{fichier['nom_fichier']}**")
                if fichier.get('description'):
                    st.caption(fichier.get('description', ''))
            
            with col2:
                st.write(fichier.get('categorie', 'N/A'))
            
            with col3:
                taille_mb = fichier.get('taille_bytes', 0) / (1024 * 1024)
                st.write(f"{taille_mb:.2f} MB")
                st.caption(fichier.get('date_upload', ''))
            
            with col4:
                # Bouton de téléchargement
                try:
                    file_data = base64.b64decode(fichier['contenu_base64'])
                    st.download_button(
                        label="📥",
                        data=file_data,
                        file_name=fichier['nom_fichier'],
                        mime=fichier.get('type_mime', 'application/octet-stream'),
                        key=f"download_{fichier['id']}"
                    )
                except Exception as e:
                    st.error("Erreur téléchargement")
    else:
        st.info("Aucun fichier attaché à cette opération")

def render_timeline_tab(operation_id):
    """Onglet timeline et frise chronologique"""
    
    st.subheader("🧠 Timeline & Frise Chronologique")
    
    db = st.session_state.db
    
    # Choix du type de visualisation
    type_viz = st.radio(
        "Type de visualisation",
        ["Frise chronologique", "Carte mentale", "Diagramme de Gantt"]
    )
    
    if type_viz == "Frise chronologique":
        try:
            phases = db.get_phases_by_operation(operation_id)
            if phases:
                st.subheader("📅 Planning des phases")
                
                for phase in phases:
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if phase.get('est_validee', False):
                            st.write("✅")
                        else:
                            st.write("⏳")
                    
                    with col2:
                        st.write(f"**{phase.get('sous_phase', 'Phase')}**")
                        st.caption(f"Phase: {phase.get('phase_principale', '')}")
                    
                    with col3:
                        duree = phase.get('duree_mini_jours', 0)
                        if duree:
                            st.caption(f"{duree} jours")
            else:
                st.warning("Aucune phase pour cette opération")
        except Exception as e:
            st.error(f"Erreur génération timeline : {str(e)}")
    
    elif type_viz == "Carte mentale":
        try:
            phases = db.get_phases_by_operation(operation_id)
            if phases:
                st.subheader("🗂️ Vue d'ensemble des phases")
                
                # Groupement par phase principale
                phases_groupees = {}
                for phase in phases:
                    phase_principale = phase.get('phase_principale', 'Autres')
                    if phase_principale not in phases_groupees:
                        phases_groupees[phase_principale] = []
                    phases_groupees[phase_principale].append(phase)
                
                # Affichage par groupe
                for phase_principale, sous_phases in phases_groupees.items():
                    with st.expander(f"📋 {phase_principale} ({len(sous_phases)} sous-phases)"):
                        for sous_phase in sous_phases:
                            col1, col2 = st.columns([1, 4])
                            
                            with col1:
                                if sous_phase.get('est_validee', False):
                                    st.write("✅")
                                else:
                                    st.write("⏳")
                            
                            with col2:
                                st.write(f"**{sous_phase.get('sous_phase', 'Sous-phase')}**")
                                
                                responsable = sous_phase.get('responsable_principal', '')
                                if responsable:
                                    st.caption(f"Responsable: {responsable}")
            else:
                st.warning("Aucune phase pour cette opération")
        except Exception as e:
            st.error(f"Erreur génération carte mentale : {str(e)}")
    
    elif type_viz == "Diagramme de Gantt":
        try:
            phases = db.get_phases_by_operation(operation_id)
            if phases:
                # Préparation des données pour Gantt
                gantt_data = []
                for phase in phases:
                    if phase.get('date_debut_prevue') and phase.get('date_fin_prevue'):
                        gantt_data.append({
                            'Task': phase.get('sous_phase', 'Phase'),
                            'Start': phase['date_debut_prevue'],
                            'Finish': phase['date_fin_prevue'],
                            'Resource': phase.get('responsable_principal', 'Non défini')
                        })
                
                if gantt_data:
                    df_gantt = pd.DataFrame(gantt_data)
                    
                    fig = px.timeline(
                        df_gantt,
                        x_start="Start",
                        x_end="Finish", 
                        y="Task",
                        color="Resource",
                        title="Planning des phases"
                    )
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucune date définie pour les phases")
            else:
                st.warning("Aucune phase trouvée")
        except Exception as e:
            st.error(f"Erreur génération Gantt : {str(e)}")
    
    # Alertes de cette opération
    st.markdown("---")
    st.subheader("🚨 Alertes actives")
    
    try:
        phases = db.get_phases_by_operation(operation_id)
        alertes_detectees = []
        
        for phase in phases:
            if not phase.get('est_validee', False):
                duree_max = phase.get('duree_maxi_jours', 30)
                alertes_detectees.append({
                    'phase': phase.get('sous_phase', 'Phase'),
                    'message': f"Phase non validée - Durée max: {duree_max} jours",
                    'niveau': 2
                })
        
        if alertes_detectees:
            for alerte in alertes_detectees[:3]:  # Top 3
                niveau_couleur = {
                    1: "#d4edda",  # Vert
                    2: "#d1ecf1",  # Bleu
                    3: "#fff3cd",  # Jaune
                    4: "#f8d7da",  # Orange
                    5: "#f5c6cb"   # Rouge
                }.get(alerte['niveau'], "#ffffff")
                
                st.markdown(f"""
                <div style="background-color: {niveau_couleur}; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <strong>{alerte['phase']}</strong>
                        <span>Niveau: {alerte['niveau']}/5</span>
                    </div>
                    <p style="margin: 0.5rem 0 0 0;">{alerte['message']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Aucune alerte active pour cette opération")
    except Exception as e:
        st.error(f"Erreur vérification alertes : {str(e)}")

# Fonctions utilitaires pour l'interface

def get_status_color(statut):
    """Retourne la couleur associée à un statut"""
    colors = {
        "🟡 À l'étude": "#fff3cd",
        "🛠️ En consultation": "#d1ecf1",
        "📋 Marché attribué": "#d4edda", 
        "🚧 En travaux": "#f8d7da",
        "📦 Livré (non soldé)": "#d4edda",
        "📄 En GPA": "#e2e3e5",
        "✅ Clôturé (soldé)": "#d4edda",
        "🔴 Bloqué": "#f5c6cb"
    }
    return colors.get(statut, "#ffffff")

def format_phase_duration(duree_mini, duree_maxi):
    """Formate la durée d'une phase"""
    if duree_mini and duree_maxi:
        if duree_mini == duree_maxi:
            return f"{duree_mini} jours"
        else:
            return f"{duree_mini}-{duree_maxi} jours"
    elif duree_mini:
        return f"Min {duree_mini} jours"
    elif duree_maxi:
        return f"Max {duree_maxi} jours"
    else:
        return "Durée non définie"

if __name__ == "__main__":
    main()