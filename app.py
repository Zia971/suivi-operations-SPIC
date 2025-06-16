"""
Application Flask SPIC 2.0 - VERSION COMPLÈTE ET AMÉLIORÉE
Gestion des opérations immobilières avec interface épurée
Intégration: alertes intelligentes, timeline colorée, statuts automatiques
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO

# Import des modules personnalisés
import config
import database
import utils

# ============================================================================
# CONFIGURATION STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="SPIC 2.0 - Suivi Opérations",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour interface moderne
st.markdown("""

    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .alert-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .phase-card {
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .phase-validee { border-left-color: #10b981; background: #f0fdf4; }
    .phase-en-cours { border-left-color: #f59e0b; background: #fffbeb; }
    .phase-bloquee { border-left-color: #ef4444; background: #fef2f2; }
    .phase-attente { border-left-color: #6b7280; background: #f9fafb; }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f1f5f9;
        border-radius: 8px;
        color: #475569;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    
    .timeline-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

""", unsafe_allow_html=True)

# ============================================================================
# INITIALISATION BASE DE DONNÉES
# ============================================================================

@st.cache_resource
def init_database():
    """Initialise la base de données avec cache"""
    return database.DatabaseManager()

# ============================================================================
# FONCTIONS UTILITAIRES STREAMLIT
# ============================================================================

def display_metric_cards(col1, col2, col3, col4, kpi_data):
    """Affiche les cartes métriques"""
    
    with col1:
        st.markdown("""
        
            📊 Total Opérations
            
                {}
            
        
        """.format(kpi_data.get('total_operations', 0)), unsafe_allow_html=True)
    
    with col2:
        avg_progress = kpi_data.get('avancement_moyen', 0)
        color = "#10b981" if avg_progress >= 70 else "#f59e0b" if avg_progress >= 40 else "#ef4444"
        st.markdown(f"""
        
            📈 Avancement Moyen
            
                {avg_progress}%
            
        
        """, unsafe_allow_html=True)
    
    with col3:
        blocked_ops = kpi_data.get('operations_bloquees', 0)
        color = "#ef4444" if blocked_ops > 0 else "#10b981"
        st.markdown(f"""
        
            🔴 Opérations Bloquées
            
                {blocked_ops}
            
        
        """, unsafe_allow_html=True)
    
    with col4:
        active_alerts = kpi_data.get('alertes_actives', 0)
        color = "#ef4444" if active_alerts > 5 else "#f59e0b" if active_alerts > 0 else "#10b981"
        st.markdown(f"""
        
            🚨 Alertes Actives
            
                {active_alerts}
            
        
        """, unsafe_allow_html=True)

def display_alert(message, alert_type="info"):
    """Affiche une alerte stylisée"""
    
    if alert_type == "success":
        st.markdown(f'✅ {message}', unsafe_allow_html=True)
    elif alert_type == "error":
        st.markdown(f'❌ {message}', unsafe_allow_html=True)
    elif alert_type == "warning":
        st.markdown(f'⚠️ {message}', unsafe_allow_html=True)
    else:
        st.info(f"ℹ️ {message}")

def format_phase_display(phase):
    """Formate l'affichage d'une phase avec couleurs"""
    
    if phase.get('blocage_actif', False):
        css_class = "phase-bloquee"
        status_icon = "🔴"
        status_text = "BLOQUÉ"
    elif phase.get('est_validee', False):
        css_class = "phase-validee"
        status_icon = "✅"
        status_text = "VALIDÉ"
    else:
        # Vérifier si en retard
        if phase.get('date_fin_prevue'):
            try:
                date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                if datetime.now().date() > date_fin:
                    css_class = "phase-bloquee"
                    status_icon = "⏰"
                    status_text = "EN RETARD"
                else:
                    css_class = "phase-en-cours"
                    status_icon = "🔄"
                    status_text = "EN COURS"
            except:
                css_class = "phase-attente"
                status_icon = "⏳"
                status_text = "EN ATTENTE"
        else:
            css_class = "phase-attente"
            status_icon = "⏳"
            status_text = "EN ATTENTE"
    
    return css_class, status_icon, status_text

# ============================================================================
# PAGES PRINCIPALES
# ============================================================================

def render_manager_dashboard():
    """Page tableau de bord Manager avec design amélioré"""
    
    st.markdown('📊 Tableau de Bord Manager', unsafe_allow_html=True)
    
    db = init_database()
    
    # Récupération des données KPI
    kpi_data = db.get_kpi_data()
    operations = db.get_operations(with_risk_score=True)
    
    # Section métriques principales
    st.markdown("### 📈 Indicateurs Clés")
    col1, col2, col3, col4 = st.columns(4)
    display_metric_cards(col1, col2, col3, col4, kpi_data)
    
    st.markdown("---")
    
    # Section graphiques
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📊 Répartition par Statut")
        if kpi_data.get('repartition_statuts'):
            # Graphique camembert des statuts
            statuts = list(kpi_data['repartition_statuts'].keys())
            valeurs = list(kpi_data['repartition_statuts'].values())
            
            fig_statuts = px.pie(
                values=valeurs,
                names=statuts,
                title="Opérations par Statut",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_statuts.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_statuts, use_container_width=True)
        else:
            st.info("Aucune donnée de statut disponible")
    
    with col_right:
        st.markdown("### 📈 Répartition par Type")
        if kpi_data.get('repartition_types'):
            # Graphique barres des types
            types = list(kpi_data['repartition_types'].keys())
            valeurs = list(kpi_data['repartition_types'].values())
            
            fig_types = px.bar(
                x=types,
                y=valeurs,
                title="Opérations par Type",
                color=types,
                color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
            )
            fig_types.update_layout(showlegend=False)
            st.plotly_chart(fig_types, use_container_width=True)
        else:
            st.info("Aucune donnée de type disponible")
    
    st.markdown("---")
    
    # Section TOP 3 Opérations à Risque - LOGIQUE AMÉLIORÉE
    st.markdown("### 🚨 TOP 3 Opérations à Risque")
    
    operations_risque = db.get_operations_at_risk(limit=3)
    
    if operations_risque:
        for i, operation in enumerate(operations_risque, 1):
            with st.expander(f"🥇 #{i} - {operation.get('nom', 'N/A')} - Score: {operation.get('score_risque', 0):.1f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {operation.get('type_operation', 'N/A')}")
                    st.write(f"**Responsable:** {operation.get('responsable_aco', 'N/A')}")
                    st.write(f"**Statut:** {operation.get('statut_principal', 'N/A')}")
                    st.write(f"**Avancement:** {operation.get('pourcentage_avancement', 0):.1f}%")
                
                with col2:
                    st.write("**Raisons du risque:**")
                    raisons = operation.get('raisons_risque', [])
                    if raisons:
                        for raison in raisons:
                            st.write(f"• {raison}")
                    else:
                        st.write("• Score de risque élevé selon critères automatiques")
                    
                    if operation.get('alertes_actives', 0) > 0:
                        st.error(f"🚨 {operation['alertes_actives']} alerte(s) active(s)")
                    
                    if operation.get('blocages_actifs', 0) > 0:
                        st.error(f"🔴 {operation['blocages_actifs']} blocage(s) actif(s)")
    else:
        st.success("🎉 Aucune opération à risque élevé détectée")
    
    # Section évolution récente
    st.markdown("---")
    st.markdown("### 📊 Évolution Récente")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nouvelles = kpi_data.get('nouvelles_operations_semaine', 0)
        st.metric("Nouvelles opérations (7j)", nouvelles)
    
    with col2:
        cloturees = kpi_data.get('operations_cloturees_semaine', 0)
        st.metric("Opérations clôturées (7j)", cloturees)
    
    with col3:
        en_retard = kpi_data.get('operations_en_retard', 0)
        st.metric("Opérations en retard", en_retard)

def render_aco_view():
    """Page Vue Chargé d'Opération avec fonctionnalités améliorées"""
    
    st.markdown('👤 Vue Chargé d\'Opération', unsafe_allow_html=True)
    
    db = init_database()
    
    # Sélection ACO avec gestion dynamique
    col1, col2 = st.columns([3, 1])
    
    with col1:
        acos_disponibles = [aco['nom_aco'] for aco in db.get_acos_list()]
        if acos_disponibles:
            aco_selectionne = st.selectbox(
                "Choisir un chargé d'opération:",
                options=acos_disponibles,
                key="aco_selector"
            )
        else:
            st.error("Aucun ACO configuré")
            return
    
    with col2:
        if st.button("⚙️ Gérer ACO", key="manage_aco_btn"):
            st.session_state.show_aco_management = not st.session_state.get('show_aco_management', False)
    
    # Interface de gestion des ACO
    if st.session_state.get('show_aco_management', False):
        st.markdown("---")
        st.markdown("### ⚙️ Gestion des ACO")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Ajouter un ACO**")
            nouveau_aco = st.text_input("Nom du nouvel ACO:", key="new_aco_name")
            if st.button("Ajouter", key="add_aco_btn"):
                if nouveau_aco and nouveau_aco.strip():
                    if db.add_aco(nouveau_aco.strip()):
                        display_alert(f"ACO '{nouveau_aco}' ajouté avec succès", "success")
                        st.rerun()
                    else:
                        display_alert("Erreur lors de l'ajout (nom déjà existant ?)", "error")
                else:
                    display_alert("Veuillez saisir un nom valide", "warning")
        
        with col2:
            st.markdown("**Supprimer un ACO**")
            aco_a_supprimer = st.selectbox(
                "ACO à supprimer:",
                options=acos_disponibles,
                key="delete_aco_selector"
            )
            if st.button("Supprimer", key="delete_aco_btn"):
                if db.remove_aco(aco_a_supprimer):
                    display_alert(f"ACO '{aco_a_supprimer}' supprimé", "success")
                    st.rerun()
                else:
                    display_alert("Impossible de supprimer (opérations en cours ?)", "error")
        
        with col3:
            st.markdown("**Modifier un ACO**")
            aco_a_modifier = st.selectbox(
                "ACO à modifier:",
                options=acos_disponibles,
                key="modify_aco_selector"
            )
            nouveau_nom = st.text_input("Nouveau nom:", key="modify_aco_name")
            if st.button("Modifier", key="modify_aco_btn"):
                if nouveau_nom and nouveau_nom.strip():
                    if db.update_aco(aco_a_modifier, nouveau_nom.strip()):
                        display_alert(f"ACO renommé vers '{nouveau_nom}'", "success")
                        st.rerun()
                    else:
                        display_alert("Erreur lors de la modification", "error")
        
        st.markdown("---")
    
    # Récupération des opérations de l'ACO
    operations_aco = db.get_operations(responsable=aco_selectionne)
    
    if not operations_aco:
        st.info(f"Aucune opération trouvée pour {aco_selectionne}")
        return
    
    # Résumé de performance de l'ACO
    performance_summary = utils.generate_aco_performance_summary(aco_selectionne, operations_aco, db)
    
    st.markdown("### 📊 Résumé de Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Opérations totales", performance_summary.get('total_operations', 0))
    
    with col2:
        st.metric("Opérations actives", performance_summary.get('operations_actives', 0))
    
    with col3:
        avg_progress = performance_summary.get('avancement_moyen', 0)
        st.metric("Avancement moyen", f"{avg_progress}%")
    
    with col4:
        risk_ops = performance_summary.get('nb_operations_a_risque', 0)
        st.metric("Opérations à risque", risk_ops)
    
    # Tâches prioritaires de la semaine
    st.markdown("---")
    st.markdown("### 📅 Tâches Prioritaires Cette Semaine")
    
    taches_semaine = utils.get_weekly_focus_tasks(operations_aco, db)
    
    if taches_semaine:
        for tache in taches_semaine[:5]:  # Top 5
            priorite = tache.get('priorite', 'NORMAL')
            
            if priorite == 'BLOQUÉ':
                bg_color = "#fef2f2"
                border_color = "#ef4444"
            elif priorite == 'URGENT':
                bg_color = "#fff7ed"
                border_color = "#f59e0b"
            else:
                bg_color = "#f0f9ff"
                border_color = "#3b82f6"
            
            st.markdown(f"""
            
                
                    
                        {tache.get('icone', '📌')} {tache.get('operation_nom', 'N/A')}
                        {tache.get('phase_nom', 'N/A')}
                    
                    
                        
                            {priorite}
                        
                        
                            {tache.get('jours_restants', 0)} jour(s) restant(s)
                        
                    
                
            
            """, unsafe_allow_html=True)
    else:
        st.success("🎉 Aucune tâche urgente cette semaine")
    
    # Liste des opérations avec détails
    st.markdown("---")
    st.markdown("### 📋 Mes Opérations")
    
    for operation in operations_aco:
        with st.expander(f"{operation.get('nom', 'N/A')} - {operation.get('statut_principal', 'N/A')} ({operation.get('pourcentage_avancement', 0):.1f}%)"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {operation.get('type_operation', 'N/A')}")
                st.write(f"**Commune:** {operation.get('commune', 'N/A')}")
                st.write(f"**Logements:** {operation.get('nb_logements_total', 0)}")
                
                # Vérifier les alertes
                alertes = utils.check_alerts(operation['id'], db)
                if alertes:
                    st.error(f"🚨 {len(alertes)} alerte(s) active(s)")
                    for alerte in alertes[:2]:  # Top 2
                        st.write(f"• {alerte.get('icone', '⚠️')} {alerte.get('message', 'N/A')}")
            
            with col2:
                # Bouton d'accès aux détails
                if st.button(f"Voir détails", key=f"detail_{operation['id']}"):
                    st.session_state.operation_detail_id = operation['id']
                    st.session_state.current_page = "detail_operation"
                    st.rerun()
                
                # Phase actuelle
                phases = db.get_phases_by_operation(operation['id'])
                phase_actuelle = utils.get_current_phase(phases)
                if phase_actuelle:
                    st.write(f"**Phase actuelle:** {phase_actuelle.get('sous_phase', 'N/A')}")

def render_operation_detail():
    """Page de détail d'une opération avec onglets épurés"""
    
    operation_id = st.session_state.get('operation_detail_id')
    if not operation_id:
        st.error("Aucune opération sélectionnée")
        return
    
    db = init_database()
    operation = db.get_operation_detail(operation_id)
    
    if not operation:
        st.error("Opération introuvable")
        return
    
    # En-tête avec bouton retour
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.markdown(f'🏗️ {operation.get("nom", "N/A")}', unsafe_allow_html=True)
    
    with col2:
        if st.button("← Retour", key="back_btn"):
            st.session_state.current_page = "aco_view"
            st.rerun()
    
    # Informations générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", operation.get('type_operation', 'N/A'))
    with col2:
        st.metric("Statut", operation.get('statut_principal', 'N/A'))
    with col3:
        st.metric("Avancement", f"{operation.get('pourcentage_avancement', 0):.1f}%")
    with col4:
        st.metric("Score Risque", f"{operation.get('score_risque', 0):.1f}")
    
    # Onglets épurés (SANS Finance et Pièces jointes)
    tab1, tab2, tab3 = st.tabs(["📋 Phases", "📝 Journal de Suivi", "📊 Timeline"])
    
    with tab1:
        render_phases_tab(operation_id, db)
    
    with tab2:
        render_journal_tab(operation_id, db)
    
    with tab3:
        render_timeline_tab(operation_id, db)

def render_phases_tab(operation_id: int, db):
    """Onglet gestion des phases avec validation automatique"""
    
    st.markdown("### 📋 Gestion des Phases")
    
    phases = db.get_phases_by_operation(operation_id)
    
    if not phases:
        st.warning("Aucune phase trouvée pour cette opération")
        return
    
    # Statistiques rapides
    total_phases = len(phases)
    phases_validees = sum(1 for p in phases if p.get('est_validee', False))
    phases_bloquees = sum(1 for p in phases if p.get('blocage_actif', False))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total phases", total_phases)
    with col2:
        st.metric("Validées", phases_validees)
    with col3:
        st.metric("Bloquées", phases_bloquees)
    
    st.markdown("---")
    
    # Affichage des phases par groupe
    phases_par_groupe = {}
    for phase in phases:
        groupe = phase.get('phase_principale', 'Autres')
        if groupe not in phases_par_groupe:
            phases_par_groupe[groupe] = []
        phases_par_groupe[groupe].append(phase)
    
    # Variable pour tracker les modifications
    phases_modifiees = False
    
    for groupe, phases_groupe in phases_par_groupe.items():
        st.markdown(f"#### {groupe}")
        
        for phase in phases_groupe:
            css_class, status_icon, status_text = format_phase_display(phase)
            
            with st.container():
                st.markdown(f'', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([4, 2, 2])
                
                with col1:
                    st.markdown(f"**{status_icon} {phase.get('sous_phase', 'N/A')}**")
                    if phase.get('responsable_principal'):
                        st.caption(f"Responsable: {phase['responsable_principal']}")
                
                with col2:
                    # Checkbox pour validation
                    est_validee = st.checkbox(
                        "Validée",
                        value=phase.get('est_validee', False),
                        key=f"phase_validee_{phase['id']}"
                    )
                    
                    if est_validee != phase.get('est_validee', False):
                        phases_modifiees = True
                
                with col3:
                    # Gestion des blocages
                    if phase.get('blocage_actif', False):
                        if st.button(f"🔓 Débloquer", key=f"unblock_{phase['id']}"):
                            # Logique de déblocage
                            if db.update_phase(phase['id'], blocage_actif=False):
                                display_alert("Phase débloquée avec succès", "success")
                                st.rerun()
                    else:
                        if st.button(f"🔒 Bloquer", key=f"block_{phase['id']}"): 
                            # Interface de blocage
                            motif = st.text_input(f"Motif du blocage pour {phase['sous_phase']}:", key=f"motif_{phase['id']}")
                            if motif:
                                if db.update_phase(phase['id'], blocage_actif=True, motif_blocage=motif):
                                    display_alert("Phase bloquée avec succès", "success")
                                    st.rerun()
                
                st.markdown('', unsafe_allow_html=True)
    
    # Bouton de sauvegarde global
    if st.button("💾 Sauvegarder les modifications", key="save_phases"):
        try:
            # Mise à jour de toutes les phases modifiées
            for phase in phases:
                checkbox_key = f"phase_validee_{phase['id']}"
                if checkbox_key in st.session_state:
                    nouvelle_valeur = st.session_state[checkbox_key]
                    if nouvelle_valeur != phase.get('est_validee', False):
                        db.update_phase(phase['id'], est_validee=nouvelle_valeur)
            
            # Mise à jour automatique du statut et de l'avancement
            if db.update_operation_progress_and_status(operation_id):
                display_alert("Phases mises à jour avec succès! Statut recalculé automatiquement.", "success")
                st.rerun()
            else:
                display_alert("Erreur lors de la mise à jour", "error")
                
        except Exception as e:
            display_alert(f"Erreur: {str(e)}", "error")

def render_journal_tab(operation_id: int, db):
    """Onglet journal avec gestion des blocages et alertes"""
    
    st.markdown("### 📝 Journal de Suivi")
    
    # Interface d'ajout d'entrée
    st.markdown("#### ➕ Nouvelle Entrée")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        type_action = st.selectbox(
            "Type d'action:",
            options=["INFO", "ATTENTION", "BLOCAGE", "VALIDATION", "RETARD"],
            key="journal_type_action"
        )
    
    with col2:
        niveau_urgence = st.slider(
            "Niveau d'urgence:",
            min_value=1,
            max_value=5,
            value=2,
            key="journal_urgence"
        )
    
    contenu = st.text_area(
        "Contenu de l'entrée:",
        height=100,
        key="journal_contenu"
    )
    
    # Phase concernée (optionnel)
    phases = db.get_phases_by_operation(operation_id)
    phases_options = ["Aucune phase spécifique"] + [f"{p.get('sous_phase', 'N/A')}" for p in phases]
    phase_concernee = st.selectbox(
        "Phase concernée (optionnel):",
        options=phases_options,
        key="journal_phase"
    )
    
    phase_concernee_final = None if phase_concernee == "Aucune phase spécifique" else phase_concernee
    
    # Indicateur de blocage
    est_blocage = st.checkbox(
        "🔴 Marquer comme blocage (remontera dans le TOP 3 risques)",
        value=(type_action == "BLOCAGE"),
        key="journal_est_blocage"
    )
    
    if st.button("💾 Ajouter l'entrée", key="add_journal_entry"):
        if contenu and contenu.strip():
            auteur = "Utilisateur"  # Peut être amélioré avec authentification
            
            if db.add_journal_entry(
                operation_id=operation_id,
                auteur=auteur,
                type_action=type_action,
                contenu=contenu.strip(),
                phase_concernee=phase_concernee_final,
                est_blocage=est_blocage,
                niveau_urgence=niveau_urgence
            ):
                display_alert("Entrée ajoutée avec succès", "success")
                
                if est_blocage:
                    display_alert("Blocage enregistré - L'opération remontera dans les alertes prioritaires", "warning")
                
                st.rerun()
            else:
                display_alert("Erreur lors de l'ajout", "error")
        else:
            display_alert("Veuillez saisir un contenu", "warning")
    
    st.markdown("---")
    
    # Affichage du journal existant
    st.markdown("#### 📚 Historique")
    
    journal_entries = db.get_journal_by_operation(operation_id)
    
    if journal_entries:
        for entry in journal_entries:
            # Couleur selon le type et statut
            if entry.get('est_blocage', False) and not entry.get('est_resolu', False):
                bg_color = "#fef2f2"
                border_color = "#ef4444"
                icon = "🔴"
            elif entry.get('est_blocage', False) and entry.get('est_resolu', False):
                bg_color = "#f0fdf4"
                border_color = "#10b981"
                icon = "✅"
            elif entry.get('type_action') == "ATTENTION":
                bg_color = "#fff7ed"
                border_color = "#f59e0b"
                icon = "⚠️"
            elif entry.get('type_action') == "VALIDATION":
                bg_color = "#f0fdf4"
                border_color = "#10b981"
                icon = "✅"
            else:
                bg_color = "#f8fafc"
                border_color = "#64748b"
                icon = "ℹ️"
            
            date_saisie = entry.get('date_saisie', '')
            if date_saisie:
                try:
                    date_formatee = datetime.strptime(date_saisie, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                except:
                    date_formatee = date_saisie
            else:
                date_formatee = "Date inconnue"
            
            st.markdown(f"""
            
                
                    
                        
                            {icon}
                            {entry.get('type_action', 'INFO')}
                            {f" - Niveau {entry.get('niveau_urgence', 1)}/5" if entry.get('niveau_urgence', 1) > 1 else ""}
                        
                        {entry.get('contenu', 'N/A')}
                        
                            Par {entry.get('auteur', 'N/A')} le {date_formatee}
                            {f" • Phase: {entry.get('phase_concernee', 'N/A')}" if entry.get('phase_concernee') else ""}
                        
                    
                
            
            """, unsafe_allow_html=True)
            
            # Bouton pour résoudre un blocage
            if entry.get('est_blocage', False) and not entry.get('est_resolu', False):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"✅ Résoudre", key=f"resolve_{entry['id']}"):
                        resolu_par = "Utilisateur"  # Peut être amélioré
                        commentaire = st.text_input(f"Commentaire de résolution:", key=f"comment_{entry['id']}")
                        
                        if db.resolve_blocage(entry['id'], resolu_par, commentaire):
                            display_alert("Blocage résolu avec succès", "success")
                            st.rerun()
    else:
        st.info("Aucune entrée dans le journal pour cette opération")

def render_timeline_tab(operation_id: int, db):
    """Onglet timeline avec visualisations colorées améliorées"""
    
    st.markdown("### 📊 Timeline et Visualisations")
    
    operation = db.get_operation_detail(operation_id)
    phases = db.get_phases_by_operation(operation_id)
    
    if not phases:
        st.warning("Aucune phase disponible pour générer la timeline")
        return
    
    # Sélecteur de type de visualisation
    type_viz = st.selectbox(
        "Type de visualisation:",
        options=["chronologique", "gantt", "mental_map"],
        format_func=lambda x: {
            "chronologique": "📅 Frise Chronologique",
            "gantt": "📊 Diagramme de Gantt",
            "mental_map": "🧠 Carte Mentale"
        }[x],
        key="timeline_type"
    )
    
    st.markdown("---")
    
    try:
        # Générer la visualisation selon le type sélectionné
        timeline_html = utils.generate_timeline(operation_id, db, type_viz)
        
        if timeline_html:
            st.markdown('', unsafe_allow_html=True)
            st.markdown(timeline_html, unsafe_allow_html=True)
            st.markdown('', unsafe_allow_html=True)
        else:
            st.error("Impossible de générer la timeline")
            
    except Exception as e:
        st.error(f"Erreur lors de la génération : {str(e)}")
        
        # Affichage de fallback simple
        st.markdown("### 📋 Vue Simple des Phases")
        
        for phase in phases:
            css_class, status_icon, status_text = format_phase_display(phase)
            
            progress = 100 if phase.get('est_validee', False) else 0
            
            st.markdown(f"""
            
                
                    
                        {status_icon} {phase.get('sous_phase', 'N/A')}
                        {phase.get('phase_principale', 'N/A')}
                    
                    
                        {status_text}
                        
                            
                        
                    
                
            
            """, unsafe_allow_html=True)

def render_create_operation():
    """Page de création d'une nouvelle opération"""
    
    st.markdown('➕ Créer une Nouvelle Opération', unsafe_allow_html=True)
    
    db = init_database()
    
    with st.form("create_operation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom de l'opération *", key="op_nom")
            type_operation = st.selectbox(
                "Type d'opération *",
                options=config.TYPES_OPERATIONS,
                key="op_type"
            )
            
            acos_disponibles = [aco['nom_aco'] for aco in db.get_acos_list()]
            responsable_aco = st.selectbox(
                "Responsable ACO *",
                options=acos_disponibles,
                key="op_aco"
            )
            
            commune = st.text_input("Commune", key="op_commune")
        
        with col2:
            promoteur = st.text_input("Promoteur", key="op_promoteur")
            
            nb_logements_total = st.number_input(
                "Nombre total de logements",
                min_value=0,
                value=0,
                key="op_total_log"
            )
            
            col2_1, col2_2, col2_3 = st.columns(3)
            
            with col2_1:
                nb_lls = st.number_input("LLS", min_value=0, value=0, key="op_lls")
            with col2_2:
                nb_llts = st.number_input("LLTS", min_value=0, value=0, key="op_llts")
            with col2_3:
                nb_pls = st.number_input("PLS", min_value=0, value=0, key="op_pls")
            
            budget_total = st.number_input(
                "Budget total (€)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                key="op_budget"
            )
        
        submitted = st.form_submit_button("✅ Créer l'Opération")
        
        if submitted:
            if nom and nom.strip() and type_operation and responsable_aco:
                try:
                    operation_id = db.create_operation(
                        nom=nom.strip(),
                        type_operation=type_operation,
                        responsable_aco=responsable_aco,
                        commune=commune,
                        promoteur=promoteur,
                        nb_logements_total=int(nb_logements_total),
                        nb_lls=int(nb_lls),
                        nb_llts=int(nb_llts),
                        nb_pls=int(nb_pls),
                        budget_total=float(budget_total)
                    )
                    
                    if operation_id:
                        display_alert(f"Opération '{nom}' créée avec succès (ID: {operation_id})", "success")
                        
                        # Récupérer le nombre de phases générées
                        phases_count = len(config.get_phases_for_type(type_operation))
                        display_alert(f"{phases_count} phases automatiquement générées selon le référentiel {type_operation}", "success")
                        
                        # Redirection vers la vue détail
                        if st.button("Voir l'opération créée"):
                            st.session_state.operation_detail_id = operation_id
                            st.session_state.current_page = "detail_operation"
                            st.rerun()
                    else:
                        display_alert("Erreur lors de la création", "error")
                        
                except Exception as e:
                    display_alert(f"Erreur: {str(e)}", "error")
            else:
                display_alert("Veuillez remplir tous les champs obligatoires (*)", "warning")

# ============================================================================
# NAVIGATION ET POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main():
    """Point d'entrée principal de l'application"""
    
    # Initialisation des variables de session
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "manager_dashboard"
    
    if 'operation_detail_id' not in st.session_state:
        st.session_state.operation_detail_id = None
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        
            🏗️ SPIC 2.0
            Suivi Opérations Immobilières
        
        """, unsafe_allow_html=True)
        
        st.markdown("### 🧭 Navigation")
        
        if st.button("📊 Tableau de Bord Manager", use_container_width=True):
            st.session_state.current_page = "manager_dashboard"
            st.rerun()
        
        if st.button("👤 Vue Chargé d'Opération", use_container_width=True):
            st.session_state.current_page = "aco_view"
            st.rerun()
        
        if st.button("➕ Créer Opération", use_container_width=True):
            st.session_state.current_page = "create_operation"
            st.rerun()
        
        st.markdown("---")
        
        # Statistiques rapides
        try:
            db = init_database()
            kpi_data = db.get_kpi_data()
            
            st.markdown("### 📈 Stats Rapides")
            st.metric("Total Opérations", kpi_data.get('total_operations', 0))
            st.metric("Alertes Actives", kpi_data.get('alertes_actives', 0))
            st.metric("Opérations Bloquées", kpi_data.get('operations_bloquees', 0))
            
        except Exception as e:
            st.sidebar.error(f"Erreur stats: {str(e)}")
        
        st.markdown("---")
        st.markdown("**Version:** 2.0.0")
        st.markdown("**Dernière MAJ:** " + datetime.now().strftime('%d/%m/%Y'))
    
    # Routage des pages
    current_page = st.session_state.current_page
    
    if current_page == "manager_dashboard":
        render_manager_dashboard()
    elif current_page == "aco_view":
        render_aco_view()
    elif current_page == "detail_operation":
        render_operation_detail()
    elif current_page == "create_operation":
        render_create_operation()
    else:
        st.error("Page inconnue")

# ============================================================================
# EXÉCUTION DE L'APPLICATION
# ============================================================================

if __name__ == "__main__":
    try:
        # Vérification de la configuration
        if not config.validate_config():
            st.error("❌ Erreur dans la configuration - Vérifiez config.py")
            st.stop()
        
        # Lancement de l'application
        main()
        
    except Exception as e:
        st.error(f"❌ Erreur critique de l'application : {str(e)}")
        st.info("Vérifiez que tous les modules (config.py, database.py, utils.py) sont présents et corrects")
