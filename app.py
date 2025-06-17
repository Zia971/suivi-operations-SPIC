"""
Application Streamlit SPIC 2.0 - VERSION COMPLÈTE ET MODERNE
Gestion des opérations immobilières avec interface épurée et collaborative
Intégration: alertes intelligentes, timeline colorée, statuts automatiques, module REM
Optimisé pour performance Streamlit avec cache et sessions
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
import time

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
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "SPIC 2.0 - Application de suivi des opérations immobilières"
    }
)

# CSS personnalisé pour interface moderne et collaborative
st.markdown("""
<style>
    /* Variables CSS pour cohérence */
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --success-color: #22c55e;
        --border-radius: 12px;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Cartes métriques modernes */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        border-left: 4px solid var(--primary-color);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #6b7280;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .metric-delta.positive { color: var(--success-color); }
    .metric-delta.negative { color: var(--danger-color); }
    .metric-delta.neutral { color: #6b7280; }
    
    /* Cards d'alertes et notifications */
    .alert-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--danger-color);
    }
    
    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--success-color);
    }
    
    .warning-card {
        background: #fffbeb;
        border: 1px solid #fed7aa;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--warning-color);
    }
    
    .info-card {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Cards de phases avec couleurs dynamiques */
    .phase-card {
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .phase-card:hover {
        transform: translateX(4px);
        box-shadow: var(--shadow);
    }
    
    .phase-validee { 
        border-left-color: var(--success-color); 
        background: #f0fdf4; 
    }
    .phase-en-cours { 
        border-left-color: var(--warning-color); 
        background: #fffbeb; 
    }
    .phase-bloquee { 
        border-left-color: var(--danger-color); 
        background: #fef2f2; 
    }
    .phase-attente { 
        border-left-color: #6b7280; 
        background: #f9fafb; 
    }
    
    /* Sidebar modernisée */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: var(--border-radius);
    }
    
    /* Onglets modernes */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8fafc;
        border-radius: var(--border-radius);
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #475569;
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 0 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e2e8f0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
        box-shadow: var(--shadow);
    }
    
    /* Timeline container */
    .timeline-container {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        margin: 1rem 0;
    }
    
    /* Boutons personnalisés */
    .custom-button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .custom-button:hover {
        background: #2563eb;
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    .custom-button.secondary {
        background: #6b7280;
    }
    
    .custom-button.success {
        background: var(--success-color);
    }
    
    .custom-button.warning {
        background: var(--warning-color);
    }
    
    .custom-button.danger {
        background: var(--danger-color);
    }
    
    /* Progress bars modernes */
    .progress-container {
        background: #e5e7eb;
        border-radius: 50px;
        height: 8px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 50px;
        transition: width 0.3s ease;
    }
    
    /* Tables améliorées */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1a1;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALISATION ET GESTION DES SESSIONS
# ============================================================================

@st.cache_resource
def init_database():
    """Initialise la base de données avec cache pour performance"""
    return database.DatabaseManager()

def init_session_state():
    """Initialise les variables de session Streamlit"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard_manager"
    
    if 'operation_detail_id' not in st.session_state:
        st.session_state.operation_detail_id = None
    
    if 'selected_aco' not in st.session_state:
        st.session_state.selected_aco = None
    
    if 'show_aco_management' not in st.session_state:
        st.session_state.show_aco_management = False
    
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

def add_notification(message: str, type_notif: str = "info", duration: int = 5):
    """Ajoute une notification temporaire"""
    notification = {
        'id': datetime.now().timestamp(),
        'message': message,
        'type': type_notif,
        'timestamp': datetime.now(),
        'duration': duration
    }
    st.session_state.notifications.append(notification)

def display_notifications():
    """Affiche les notifications actives"""
    current_time = datetime.now()
    active_notifications = []
    
    for notif in st.session_state.notifications:
        if (current_time - notif['timestamp']).seconds < notif['duration']:
            active_notifications.append(notif)
            
            if notif['type'] == 'success':
                st.success(notif['message'])
            elif notif['type'] == 'error':
                st.error(notif['message'])
            elif notif['type'] == 'warning':
                st.warning(notif['message'])
            else:
                st.info(notif['message'])
    
    st.session_state.notifications = active_notifications

# ============================================================================
# FONCTIONS UTILITAIRES INTERFACE
# ============================================================================

def display_metric_card(label: str, value: str, delta: str = None, delta_type: str = "neutral"):
    """Affiche une carte métrique moderne"""
    
    delta_class = f"metric-delta {delta_type}" if delta else ""
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    
    st.markdown(f"""
    <div class="metric-card fade-in">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def display_progress_bar(percentage: float, label: str = "", color: str = "primary"):
    """Affiche une barre de progression moderne"""
    
    color_map = {
        "primary": "var(--primary-color)",
        "success": "var(--success-color)",
        "warning": "var(--warning-color)",
        "danger": "var(--danger-color)"
    }
    
    bar_color = color_map.get(color, color_map["primary"])
    
    st.markdown(f"""
    <div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span style="font-size: 0.9rem; color: #374151;">{label}</span>
            <span style="font-size: 0.9rem; font-weight: 600; color: {bar_color};">{percentage:.1f}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {percentage}%; background: {bar_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_status_badge(status: str):
    """Affiche un badge de statut coloré"""
    
    status_colors = {
        "🟡 À l'étude": "#fbbf24",
        "🛠️ En consultation": "#f97316",
        "📋 Marché attribué": "#3b82f6",
        "🚧 En travaux": "#8b5cf6",
        "📦 Livré (non soldé)": "#06b6d4",
        "✅ Clôturé (soldé)": "#22c55e",
        "🔴 Bloqué": "#ef4444"
    }
    
    color = status_colors.get(status, "#6b7280")
    
    st.markdown(f"""
    <span style="
        background: {color}20;
        color: {color};
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid {color}40;
    ">{status}</span>
    """, unsafe_allow_html=True)

def create_action_buttons(operation_id: int, show_detail: bool = True, show_edit: bool = False):
    """Crée des boutons d'action pour une opération"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if show_detail and st.button("👁️ Voir détail", key=f"detail_{operation_id}"):
            st.session_state.operation_detail_id = operation_id
            st.session_state.current_page = "detail_operation"
            st.rerun()
    
    with col2:
        if show_edit and st.button("✏️ Modifier", key=f"edit_{operation_id}"):
            # TODO: Implémenter la modification
            add_notification("Fonction de modification en cours de développement", "info")
    
    with col3:
        if st.button("📊 Analytics", key=f"analytics_{operation_id}"):
            # TODO: Implémenter les analytics
            add_notification("Vue analytics en cours de développement", "info")

# ============================================================================
# PAGES PRINCIPALES
# ============================================================================

def render_dashboard_manager():
    """Page tableau de bord Manager avec design moderne et collaboratif"""
    
    st.markdown("""
    <div class="main-header">
        <h1>📊 Tableau de Bord Manager</h1>
        <p>Vue d'ensemble des opérations et indicateurs clés de performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = init_database()
    
    # Récupération des données avec gestion d'erreur
    try:
        with st.spinner("Chargement des données..."):
            kpi_data = db.get_kpi_data()
            operations = db.get_operations(with_risk_score=True, limit=50)
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return
    
    if not kpi_data:
        st.warning("Aucune donnée disponible. Créez d'abord une opération.")
        return
    
    # Section métriques principales
    st.markdown("### 📈 Indicateurs Clés de Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            "Total Opérations", 
            str(kpi_data.get('total_operations', 0)),
            f"+{kpi_data.get('nouvelles_operations_semaine', 0)} cette semaine",
            "positive" if kpi_data.get('nouvelles_operations_semaine', 0) > 0 else "neutral"
        )
    
    with col2:
        avancement = kpi_data.get('avancement_moyen', 0)
        color = "success" if avancement >= 70 else "warning" if avancement >= 40 else "danger"
        display_metric_card(
            "Avancement Moyen",
            f"{avancement:.1f}%",
            "Performance globale du portfolio",
            "neutral"
        )
    
    with col3:
        bloquees = kpi_data.get('operations_bloquees', 0)
        color = "danger" if bloquees > 0 else "success"
        display_metric_card(
            "Opérations Bloquées",
            str(bloquees),
            "Nécessitent une action immédiate" if bloquees > 0 else "Aucun blocage actuel",
            "danger" if bloquees > 0 else "success"
        )
    
    with col4:
        alertes = kpi_data.get('alertes_actives', 0)
        color = "danger" if alertes > 5 else "warning" if alertes > 0 else "success"
        display_metric_card(
            "Alertes Actives",
            str(alertes),
            f"Niveau d'attention requis",
            "danger" if alertes > 3 else "warning" if alertes > 0 else "success"
        )
    
    # Section REM si disponible
    if kpi_data.get('rem_totale_portfolio', 0) > 0:
        st.markdown("### 💰 Performance Financière")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            display_metric_card(
                "REM Portfolio",
                utils.format_currency(kpi_data['rem_totale_portfolio']),
                f"{kpi_data.get('operations_avec_rem', 0)} opérations génératrices",
                "success"
            )
        
        with col2:
            budget_total = kpi_data.get('budget_total_portfolio', 0)
            if budget_total > 0:
                display_metric_card(
                    "Budget Portfolio",
                    utils.format_currency(budget_total),
                    "Investissement total en cours",
                    "neutral"
                )
        
        with col3:
            if budget_total > 0 and kpi_data['rem_totale_portfolio'] > 0:
                ratio_rem = (kpi_data['rem_totale_portfolio'] / budget_total) * 100
                display_metric_card(
                    "Ratio REM/Budget",
                    f"{ratio_rem:.2f}%",
                    "Efficacité des investissements",
                    "success" if ratio_rem > 5 else "warning"
                )
    
    st.markdown("---")
    
    # Section graphiques
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📊 Répartition par Statut")
        try:
            charts = utils.generate_kpi_charts_streamlit(kpi_data)
            if 'statuts' in charts:
                st.plotly_chart(charts['statuts'], use_container_width=True)
            else:
                st.info("Données de statut non disponibles")
        except Exception as e:
            st.error(f"Erreur génération graphique statuts : {e}")
    
    with col_right:
        st.markdown("### 📈 Répartition par Type")
        try:
            if 'types' in charts:
                st.plotly_chart(charts['types'], use_container_width=True)
            else:
                st.info("Données de type non disponibles")
        except Exception as e:
            st.error(f"Erreur génération graphique types : {e}")
    
    # Graphique d'avancement global
    if 'avancement' in charts:
        st.markdown("### 📊 Avancement Global")
        st.plotly_chart(charts['avancement'], use_container_width=True)
    
    st.markdown("---")
    
    # Section TOP 3 Opérations à Risque - LOGIQUE AUTOMATIQUE
    st.markdown("### 🚨 TOP 3 Opérations à Risque")
    st.markdown("*Calcul automatique basé sur le journal, les blocages et l'avancement*")
    
    try:
        operations_risque = db.get_operations_at_risk(limit=3)
        
        if operations_risque:
            for i, operation in enumerate(operations_risque, 1):
                with st.expander(f"🥇 #{i} - {operation.get('nom', 'N/A')} - Score: {operation.get('score_risque', 0):.1f}/100", expanded=(i == 1)):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Type:** {operation.get('type_operation', 'N/A')}")
                        st.write(f"**Responsable:** {operation.get('responsable_aco', 'N/A')}")
                        display_status_badge(operation.get('statut_principal', 'N/A'))
                        
                        # Barre de progression
                        avancement = operation.get('pourcentage_avancement', 0)
                        color = "success" if avancement > 70 else "warning" if avancement > 30 else "danger"
                        display_progress_bar(avancement, "Avancement", color)
                    
                    with col2:
                        st.write("**Raisons du risque:**")
                        raisons = operation.get('raisons_risque', [])
                        if raisons:
                            for raison in raisons:
                                st.markdown(f"• {raison}")
                        else:
                            st.write("• Score de risque élevé selon critères automatiques")
                        
                        # Alertes et blocages
                        if operation.get('alertes_actives', 0) > 0:
                            st.markdown(f"""
                            <div class="alert-card">
                                🚨 {operation['alertes_actives']} alerte(s) active(s)
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if operation.get('blocages_actifs', 0) > 0:
                            st.markdown(f"""
                            <div class="alert-card">
                                🔴 {operation['blocages_actifs']} blocage(s) actif(s)
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col3:
                        create_action_buttons(operation['id'], show_detail=True)
                        
                        # REM si disponible
                        if operation.get('rem_annuelle_prevue', 0) > 0:
                            st.markdown(f"""
                            <div class="info-card">
                                💰 REM: {utils.format_currency(operation['rem_annuelle_prevue'])}
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-card">
                🎉 Excellente nouvelle ! Aucune opération à risque élevé détectée.
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erreur lors du calcul des risques : {e}")
    
    # Section graphique analyse des risques
    if operations_risque:
        st.markdown("### 📈 Analyse Détaillée des Risques")
        try:
            risk_chart = utils.create_risk_analysis_chart_streamlit(operations_risque)
            st.plotly_chart(risk_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur génération graphique risques : {e}")
    
    # Section évolution récente
    st.markdown("---")
    st.markdown("### 📊 Évolution et Tendances")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nouvelles = kpi_data.get('nouvelles_operations_semaine', 0)
        st.metric("Nouvelles opérations (7j)", nouvelles, delta=None)
    
    with col2:
        cloturees = kpi_data.get('operations_cloturees_semaine', 0)
        st.metric("Opérations clôturées (7j)", cloturees, delta=None)
    
    with col3:
        en_retard = kpi_data.get('operations_en_retard', 0)
        st.metric("Opérations en retard", en_retard, delta=None)
    
    with col4:
        if 'evolution' in charts:
            st.plotly_chart(charts['evolution'], use_container_width=True)
    
    # Refresh automatique
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        add_notification("Données actualisées avec succès", "success")
        st.rerun()

def render_aco_view():
    """Page Vue Chargé d'Opération avec fonctionnalités complètes"""
    
    st.markdown("""
    <div class="main-header">
        <h1>👤 Vue Chargé d'Opération</h1>
        <p>Interface personnalisée pour le suivi de vos opérations</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = init_database()
    
    # Sélection ACO avec gestion dynamique
    col1, col2 = st.columns([3, 1])
    
    with col1:
        try:
            acos_disponibles = [aco['nom_aco'] for aco in db.get_acos_list()]
            if acos_disponibles:
                aco_selectionne = st.selectbox(
                    "Choisir un chargé d'opération:",
                    options=acos_disponibles,
                    key="aco_selector",
                    index=0 if not st.session_state.selected_aco else acos_disponibles.index(st.session_state.selected_aco) if st.session_state.selected_aco in acos_disponibles else 0
                )
                st.session_state.selected_aco = aco_selectionne
            else:
                st.error("Aucun ACO configuré")
                return
        except Exception as e:
            st.error(f"Erreur lors de la récupération des ACO : {e}")
            return
    
    with col2:
        if st.button("⚙️ Gérer ACO", key="manage_aco_btn"):
            st.session_state.show_aco_management = not st.session_state.get('show_aco_management', False)
    
    # Interface de gestion des ACO
    if st.session_state.get('show_aco_management', False):
        render_aco_management(db, acos_disponibles)
    
    # Récupération des opérations de l'ACO
    try:
        operations_aco = db.get_operations(responsable=aco_selectionne)
        performance_data = db.get_performance_aco(aco_selectionne)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return
    
    if not operations_aco:
        st.markdown(f"""
        <div class="info-card">
            ℹ️ Aucune opération trouvée pour <strong>{aco_selectionne}</strong>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Résumé de performance de l'ACO
    st.markdown("### 📊 Mon Tableau de Bord")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            "Mes Opérations",
            str(performance_data.get('operations_actives', 0)),
            f"Total: {performance_data.get('total_operations', 0)}",
            "neutral"
        )
    
    with col2:
        avg_progress = performance_data.get('avancement_moyen', 0)
        perf_relative = performance_data.get('performance_relative', 0)
        delta_text = f"{perf_relative:+.1f}% vs moyenne" if perf_relative != 0 else "Dans la moyenne"
        delta_type = "positive" if perf_relative > 0 else "negative" if perf_relative < 0 else "neutral"
        
        display_metric_card(
            "Mon Avancement",
            f"{avg_progress:.1f}%",
            delta_text,
            delta_type
        )
    
    with col3:
        risk_ops = performance_data.get('operations_bloquees', 0)
        display_metric_card(
            "Opérations à Risque",
            str(risk_ops),
            "Action requise" if risk_ops > 0 else "Tout va bien",
            "danger" if risk_ops > 0 else "success"
        )
    
    with col4:
        taux_reussite = performance_data.get('taux_reussite', 0)
        display_metric_card(
            "Taux de Réussite",
            f"{taux_reussite:.1f}%",
            f"{performance_data.get('operations_terminees', 0)} terminées",
            "success" if taux_reussite > 80 else "warning"
        )
    
    # REM gérée si disponible
    if performance_data.get('rem_totale_geree', 0) > 0:
        st.markdown("### 💰 Ma Performance Financière")
        col1, col2 = st.columns(2)
        
        with col1:
            display_metric_card(
                "REM Sous Ma Responsabilité",
                utils.format_currency(performance_data['rem_totale_geree']),
                "Rentabilité annuelle générée",
                "success"
            )
        
        with col2:
            if performance_data.get('budget_total_gere', 0) > 0:
                display_metric_card(
                    "Budget Géré",
                    utils.format_currency(performance_data['budget_total_gere']),
                    "Investissement sous responsabilité",
                    "neutral"
                )
    
    # Tâches prioritaires de la semaine
    st.markdown("---")
    st.markdown("### 📅 Mes Tâches Prioritaires Cette Semaine")
    
    try:
        taches_semaine = utils.get_weekly_focus_tasks_streamlit(operations_aco, db)
        
        if taches_semaine:
            # Grouper par priorité
            taches_bloquees = [t for t in taches_semaine if t.get('priorite') == 'BLOQUÉ']
            taches_urgentes = [t for t in taches_semaine if t.get('priorite') == 'URGENT']
            taches_importantes = [t for t in taches_semaine if t.get('priorite') == 'IMPORTANT']
            
            # Afficher les tâches par ordre de priorité
            for priorite, taches, color_class in [
                ('BLOQUÉ', taches_bloquees, 'alert-card'),
                ('URGENT', taches_urgentes, 'warning-card'),
                ('IMPORTANT', taches_importantes, 'info-card')
            ]:
                if taches:
                    st.markdown(f"#### {priorite} ({len(taches)})")
                    for tache in taches:
                        domaine_info = config.DOMAINES_OPERATIONNELS.get(tache.get('domaine', 'OPERATIONNEL'), {})
                        couleur_domaine = domaine_info.get('couleur', '#6b7280')
                        
                        st.markdown(f"""
                        <div class="{color_class}" style="border-left-color: {couleur_domaine};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{tache.get('icone', '📌')} {tache.get('operation_nom', 'N/A')}</strong>
                                    <br>
                                    <span style="color: #6b7280;">{tache.get('phase_nom', 'N/A')}</span>
                                    {f"<br><small>Motif: {tache.get('motif_blocage', '')}</small>" if tache.get('motif_blocage') else ""}
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-weight: bold; color: {couleur_domaine};">{priorite}</span>
                                    <br>
                                    <small>{tache.get('jours_restants', 0)} jour(s) restant(s)</small>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-card">
                🎉 Excellente nouvelle ! Aucune tâche urgente cette semaine.
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erreur lors de la récupération des tâches : {e}")
    
    # Liste des opérations avec vue détaillée
    st.markdown("---")
    st.markdown("### 📋 Mes Opérations")
    
    # Filtres pour les opérations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtre_statut = st.selectbox(
            "Filtrer par statut:",
            options=["Tous"] + list(set([op.get('statut_principal', 'N/A') for op in operations_aco])),
            key="filtre_statut_aco"
        )
    
    with col2:
        filtre_type = st.selectbox(
            "Filtrer par type:",
            options=["Tous"] + list(set([op.get('type_operation', 'N/A') for op in operations_aco])),
            key="filtre_type_aco"
        )
    
    with col3:
        ordre_tri = st.selectbox(
            "Trier par:",
            options=["Score de risque", "Avancement", "Date création", "REM"],
            key="ordre_tri_aco"
        )
    
    # Appliquer les filtres
    operations_filtrees = operations_aco.copy()
    
    if filtre_statut != "Tous":
        operations_filtrees = [op for op in operations_filtrees if op.get('statut_principal') == filtre_statut]
    
    if filtre_type != "Tous":
        operations_filtrees = [op for op in operations_filtrees if op.get('type_operation') == filtre_type]
    
    # Trier les opérations
    if ordre_tri == "Score de risque":
        operations_filtrees.sort(key=lambda x: x.get('score_risque', 0), reverse=True)
    elif ordre_tri == "Avancement":
        operations_filtrees.sort(key=lambda x: x.get('pourcentage_avancement', 0), reverse=True)
    elif ordre_tri == "REM":
        operations_filtrees.sort(key=lambda x: x.get('rem_annuelle_prevue', 0), reverse=True)
    else:  # Date création
        operations_filtrees.sort(key=lambda x: x.get('date_creation', ''), reverse=True)
    
    # Afficher les opérations
    for operation in operations_filtrees:
        with st.expander(
            f"{operation.get('nom', 'N/A')} - {operation.get('statut_principal', 'N/A')} ({operation.get('pourcentage_avancement', 0):.1f}%)",
            expanded=False
        ):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Type:** {operation.get('type_operation', 'N/A')}")
                st.write(f"**Commune:** {operation.get('commune', 'N/A')}")
                st.write(f"**Logements:** {operation.get('nb_logements_total', 0)}")
                
                # Barre de progression
                avancement = operation.get('pourcentage_avancement', 0)
                color = "success" if avancement > 70 else "warning" if avancement > 30 else "danger"
                display_progress_bar(avancement, "Avancement", color)
                
            with col2:
                # Vérifier les alertes
                try:
                    alertes = utils.check_alerts(operation['id'], db)
                    if alertes:
                        st.markdown(f"""
                        <div class="alert-card">
                            🚨 {len(alertes)} alerte(s) active(s)
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for alerte in alertes[:2]:  # Top 2
                            st.markdown(f"• {alerte.get('icone', '⚠️')} {alerte.get('message', 'N/A')}")
                    else:
                        st.markdown("""
                        <div class="success-card">
                            ✅ Aucune alerte active
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur vérification alertes : {e}")
                
                # Phase actuelle
                try:
                    phases = db.get_phases_by_operation(operation['id'])
                    phase_actuelle = utils.get_current_phase(phases)
                    if phase_actuelle:
                        st.write(f"**Phase actuelle:** {phase_actuelle.get('sous_phase', 'N/A')}")
                        
                        # Prochaines phases
                        prochaines = utils.get_next_phases(phases, 2)
                        if prochaines:
                            st.write("**Prochaines phases:**")
                            for phase in prochaines:
                                icone = utils.get_phase_icon(phase)
                                st.write(f"• {icone} {phase.get('sous_phase', 'N/A')}")
                except Exception as e:
                    st.error(f"Erreur phases : {e}")
            
            with col3:
                create_action_buttons(operation['id'], show_detail=True)
                
                # REM si disponible
                if operation.get('rem_annuelle_prevue', 0) > 0:
                    st.markdown(f"""
                    <div class="info-card">
                        💰 REM: {utils.format_currency(operation['rem_annuelle_prevue'])}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Score de risque
                score_risque = operation.get('score_risque', 0)
                if score_risque > 50:
                    st.markdown(f"""
                    <div class="warning-card">
                        ⚠️ Risque: {score_risque:.1f}/100
                    </div>
                    """, unsafe_allow_html=True)

def render_aco_management(db, acos_disponibles):
    """Interface de gestion des ACO"""
    
    st.markdown("---")
    st.markdown("### ⚙️ Gestion des Chargés d'Opérations")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer", "📊 Statistiques"])
    
    with tab1:
        st.markdown("**Ajouter un nouveau ACO**")
        with st.form("add_aco_form"):
            nouveau_aco = st.text_input("Nom du nouvel ACO:", placeholder="Ex: Jean DUPONT")
            submitted = st.form_submit_button("Ajouter")
            
            if submitted:
                if nouveau_aco and nouveau_aco.strip():
                    try:
                        if db.add_aco(nouveau_aco.strip()):
                            add_notification(f"ACO '{nouveau_aco}' ajouté avec succès", "success")
                            st.rerun()
                        else:
                            add_notification("Erreur lors de l'ajout (nom déjà existant ?)", "error")
                    except Exception as e:
                        add_notification(f"Erreur : {e}", "error")
                else:
                    add_notification("Veuillez saisir un nom valide", "warning")
    
    with tab2:
        st.markdown("**Modifier un ACO existant**")
        with st.form("modify_aco_form"):
            aco_a_modifier = st.selectbox("ACO à modifier:", options=acos_disponibles)
            nouveau_nom = st.text_input("Nouveau nom:", placeholder="Nouveau nom")
            submitted = st.form_submit_button("Modifier")
            
            if submitted:
                if nouveau_nom and nouveau_nom.strip():
                    try:
                        if db.update_aco(aco_a_modifier, nouveau_nom.strip()):
                            add_notification(f"ACO renommé vers '{nouveau_nom}'", "success")
                            st.rerun()
                        else:
                            add_notification("Erreur lors de la modification", "error")
                    except Exception as e:
                        add_notification(f"Erreur : {e}", "error")
                else:
                    add_notification("Veuillez saisir un nouveau nom valide", "warning")
    
    with tab3:
        st.markdown("**Supprimer un ACO**")
        st.warning("⚠️ Attention : Cette action désactivera l'ACO (pas de suppression définitive)")
        
        with st.form("delete_aco_form"):
            aco_a_supprimer = st.selectbox("ACO à désactiver:", options=acos_disponibles)
            confirmation = st.checkbox("Je confirme vouloir désactiver cet ACO")
            submitted = st.form_submit_button("Désactiver", type="primary")
            
            if submitted:
                if confirmation:
                    try:
                        if db.remove_aco(aco_a_supprimer):
                            add_notification(f"ACO '{aco_a_supprimer}' désactivé", "success")
                            st.rerun()
                        else:
                            add_notification("Impossible de désactiver (opérations en cours ?)", "error")
                    except Exception as e:
                        add_notification(f"Erreur : {e}", "error")
                else:
                    add_notification("Veuillez confirmer l'action", "warning")
    
    with tab4:
        st.markdown("**Statistiques des ACO**")
        try:
            acos_stats = db.get_acos_list(actifs_seulement=False)
            
            if acos_stats:
                df_acos = pd.DataFrame(acos_stats)
                
                # Affichage sous forme de tableau
                st.dataframe(
                    df_acos[['nom_aco', 'actif', 'operations_actuelles', 'avancement_moyen', 'rem_totale_geree']],
                    column_config={
                        "nom_aco": "Nom ACO",
                        "actif": "Actif",
                        "operations_actuelles": "Ops. Actuelles",
                        "avancement_moyen": st.column_config.ProgressColumn(
                            "Avancement Moyen",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100
                        ),
                        "rem_totale_geree": st.column_config.NumberColumn(
                            "REM Gérée (€)",
                            format="%.0f €"
                        )
                    },
                    use_container_width=True
                )
            else:
                st.info("Aucune statistique ACO disponible")
                
        except Exception as e:
            st.error(f"Erreur récupération statistiques : {e}")

def render_operation_detail():
    """Page de détail d'une opération avec onglets épurés"""
    
    operation_id = st.session_state.get('operation_detail_id')
    if not operation_id:
        st.error("Aucune opération sélectionnée")
        return
    
    db = init_database()
    
    try:
        operation = db.get_operation_detail(operation_id)
        if not operation:
            st.error("Opération introuvable")
            return
    except Exception as e:
        st.error(f"Erreur lors de la récupération de l'opération : {e}")
        return
    
    # En-tête avec bouton retour
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.markdown(f"""
        <div class="main-header">
            <h1>🏗️ {operation.get("nom", "N/A")}</h1>
            <p>{operation.get("type_operation", "N/A")} - {operation.get("commune", "N/A")}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("← Retour", key="back_btn"):
            st.session_state.current_page = "aco_view"
            st.rerun()
    
    # Informations générales en cartes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card("Type", operation.get('type_operation', 'N/A'))
    
    with col2:
        display_status_badge(operation.get('statut_principal', 'N/A'))
    
    with col3:
        avancement = operation.get('pourcentage_avancement', 0)
        color = "success" if avancement > 70 else "warning" if avancement > 30 else "danger"
        display_metric_card("Avancement", f"{avancement:.1f}%")
    
    with col4:
        score_risque = operation.get('score_risque', 0)
        display_metric_card("Score Risque", f"{score_risque:.1f}/100")
    
    # Informations supplémentaires si disponibles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if operation.get('rem_annuelle_prevue', 0) > 0:
            display_metric_card("REM Annuelle", utils.format_currency(operation['rem_annuelle_prevue']))
    
    with col2:
        if operation.get('budget_total', 0) > 0:
            display_metric_card("Budget Total", utils.format_currency(operation['budget_total']))
    
    with col3:
        if operation.get('nb_logements_total', 0) > 0:
            display_metric_card("Logements", str(operation['nb_logements_total']))
    
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
    
    try:
        phases = db.get_phases_by_operation(operation_id)
        if not phases:
            st.warning("Aucune phase trouvée pour cette opération")
            return
    except Exception as e:
        st.error(f"Erreur lors de la récupération des phases : {e}")
        return
    
    # Statistiques rapides
    total_phases = len(phases)
    phases_validees = sum(1 for p in phases if p.get('est_validee', False))
    phases_bloquees = sum(1 for p in phases if p.get('blocage_actif', False))
    phases_retard = len(utils.detect_delays(phases))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        display_metric_card("Total Phases", str(total_phases))
    with col2:
        display_metric_card("Validées", str(phases_validees))
    with col3:
        display_metric_card("Bloquées", str(phases_bloquees))
    with col4:
        display_metric_card("En Retard", str(phases_retard))
    
    # Option d'ajout de phase custom
    with st.expander("➕ Ajouter une Phase Personnalisée"):
        with st.form("add_custom_phase"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom_phase = st.text_input("Nom de la phase:", placeholder="Ex: Validation technique spéciale")
                phase_principale = st.text_input("Groupe principal:", placeholder="Ex: ÉTUDES COMPLÉMENTAIRES")
                ordre_insertion = st.number_input("Insérer à l'ordre:", min_value=1, max_value=total_phases+1, value=total_phases+1)
            
            with col2:
                duree_mini = st.number_input("Durée minimale (jours):", min_value=1, value=7)
                duree_maxi = st.number_input("Durée maximale (jours):", min_value=1, value=30)
                domaine = st.selectbox("Domaine:", options=list(config.DOMAINES_OPERATIONNELS.keys()))
                responsable = st.text_input("Responsable:", placeholder="Nom du responsable")
            
            if st.form_submit_button("Ajouter la Phase"):
                if nom_phase and phase_principale:
                    try:
                        if db.add_custom_phase(operation_id, nom_phase, phase_principale, 
                                             ordre_insertion, duree_mini, duree_maxi, 
                                             responsable, domaine):
                            add_notification("Phase personnalisée ajoutée avec succès", "success")
                            st.rerun()
                        else:
                            add_notification("Erreur lors de l'ajout de la phase", "error")
                    except Exception as e:
                        add_notification(f"Erreur : {e}", "error")
                else:
                    add_notification("Veuillez remplir les champs obligatoires", "warning")
    
    st.markdown("---")
    
    # Affichage des phases par domaine avec couleurs
    phases_par_domaine = {}
    for phase in phases:
        domaine = phase.get('domaine', 'OPERATIONNEL')
        if domaine not in phases_par_domaine:
            phases_par_domaine[domaine] = []
        phases_par_domaine[domaine].append(phase)
    
    # Variable pour tracker les modifications
    phases_modifiees = []
    
    for domaine, phases_domaine in phases_par_domaine.items():
        domaine_info = config.DOMAINES_OPERATIONNELS.get(domaine, {})
        icone_domaine = domaine_info.get('icone', '📌')
        nom_domaine = domaine_info.get('nom', domaine)
        couleur_domaine = domaine_info.get('couleur', '#6b7280')
        
        st.markdown(f"#### {icone_domaine} {nom_domaine}")
        
        for phase in sorted(phases_domaine, key=lambda x: x.get('ordre_phase', 0)):
            with st.container():
                # Utiliser la fonction de création de carte
                card_html = utils.create_phase_summary_card(phase, show_details=True)
                st.markdown(card_html, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    # Checkbox pour validation
                    key_validation = f"phase_validee_{phase['id']}"
                    est_validee = st.checkbox(
                        "Validée",
                        value=phase.get('est_validee', False),
                        key=key_validation
                    )
                    
                    if est_validee != phase.get('est_validee', False):
                        phases_modifiees.append({
                            'id': phase['id'],
                            'est_validee': est_validee
                        })
                
                with col2:
                    # Gestion des durées modifiables
                    if st.checkbox("Modifier durées", key=f"modify_duration_{phase['id']}"):
                        duree_mini = st.number_input(
                            "Durée mini (j):",
                            min_value=1,
                            value=phase.get('duree_mini_jours', 7),
                            key=f"duree_mini_{phase['id']}"
                        )
                        duree_maxi = st.number_input(
                            "Durée maxi (j):",
                            min_value=1,
                            value=phase.get('duree_maxi_jours', 30),
                            key=f"duree_maxi_{phase['id']}"
                        )
                        
                        if st.button("💾 Sauver durées", key=f"save_duration_{phase['id']}"):
                            if duree_mini <= duree_maxi:
                                try:
                                    if db.update_phase(phase['id'], duree_mini_jours=duree_mini, duree_maxi_jours=duree_maxi):
                                        add_notification("Durées mises à jour", "success")
                                        st.rerun()
                                    else:
                                        add_notification("Erreur mise à jour durées", "error")
                                except Exception as e:
                                    add_notification(f"Erreur : {e}", "error")
                            else:
                                add_notification("Durée mini doit être ≤ durée maxi", "warning")
                
                with col3:
                    # Gestion des dates
                    if st.checkbox("Modifier dates", key=f"modify_dates_{phase['id']}"):
                        date_fin_prevue = st.date_input(
                            "Date fin prévue:",
                            value=datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date() if phase.get('date_fin_prevue') else None,
                            key=f"date_fin_{phase['id']}"
                        )
                        
                        if st.button("💾 Sauver date", key=f"save_date_{phase['id']}"):
                            try:
                                if db.update_phase(phase['id'], date_fin_prevue=date_fin_prevue.isoformat()):
                                    add_notification("Date mise à jour", "success")
                                    st.rerun()
                                else:
                                    add_notification("Erreur mise à jour date", "error")
                            except Exception as e:
                                add_notification(f"Erreur : {e}", "error")
                
                with col4:
                    # Gestion des blocages
                    if phase.get('blocage_actif', False):
                        if st.button(f"🔓 Débloquer", key=f"unblock_{phase['id']}"):
                            try:
                                if db.update_phase(phase['id'], blocage_actif=False):
                                    add_notification("Phase débloquée avec succès", "success")
                                    st.rerun()
                                else:
                                    add_notification("Erreur déblocage", "error")
                            except Exception as e:
                                add_notification(f"Erreur : {e}", "error")
                    else:
                        if st.button(f"🔒 Bloquer", key=f"block_{phase['id']}"): 
                            motif = st.text_input(f"Motif du blocage:", key=f"motif_{phase['id']}")
                            if motif:
                                try:
                                    if db.update_phase(phase['id'], blocage_actif=True, motif_blocage=motif):
                                        add_notification("Phase bloquée avec succès", "success")
                                        st.rerun()
                                    else:
                                        add_notification("Erreur blocage", "error")
                                except Exception as e:
                                    add_notification(f"Erreur : {e}", "error")
                
                st.markdown("---")
    
    # Bouton de sauvegarde global pour les validations
    if phases_modifiees:
        if st.button("💾 Sauvegarder les Validations", key="save_all_phases", type="primary"):
            try:
                success_count = 0
                for phase_modif in phases_modifiees:
                    if db.update_phase(phase_modif['id'], est_validee=phase_modif['est_validee']):
                        success_count += 1
                
                # Mise à jour automatique du statut et de l'avancement
                if db.update_operation_progress_and_status(operation_id):
                    add_notification(f"{success_count} phase(s) mise(s) à jour. Statut recalculé automatiquement.", "success")
                    st.rerun()
                else:
                    add_notification("Erreur lors de la mise à jour du statut", "error")
                    
            except Exception as e:
                add_notification(f"Erreur: {str(e)}", "error")

def render_journal_tab(operation_id: int, db):
    """Onglet journal avec gestion des blocages et alertes - SOURCE UNIQUE DES NOTES"""
    
    st.markdown("### 📝 Journal de Suivi")
    st.markdown("*Source unique pour toutes les notes, commentaires et signalement de blocages*")
    
    # Interface d'ajout d'entrée
    st.markdown("#### ➕ Nouvelle Entrée")
    
    with st.form("add_journal_entry"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            type_action = st.selectbox(
                "Type d'action:",
                options=["INFO", "ATTENTION", "BLOCAGE", "VALIDATION", "OBSERVATION"],
                help="INFO: Information générale | ATTENTION: Point d'attention | BLOCAGE: Blocage critique | VALIDATION: Validation obtenue"
            )
            
            contenu = st.text_area(
                "Contenu de l'entrée:",
                placeholder="Décrivez la situation, les actions menées, les problèmes rencontrés...",
                height=100
            )
            
            phase_concernee = st.text_input(
                "Phase concernée (optionnel):",
                placeholder="Ex: Travaux fondations"
            )
        
        with col2:
            auteur = st.text_input(
                "Auteur:",
                value=st.session_state.get('selected_aco', 'Utilisateur'),
                help="Nom de la personne qui saisit l'entrée"
            )
            
            niveau_urgence = st.selectbox(
                "Niveau d'urgence:",
                options=[1, 2, 3, 4, 5],
                index=0,
                format_func=lambda x: {
                    1: "1 - Faible",
                    2: "2 - Normal", 
                    3: "3 - Moyen",
                    4: "4 - Élevé",
                    5: "5 - Critique"
                }[x]
            )
            
            est_blocage = st.checkbox(
                "🔴 Signaler comme blocage",
                help="Cochez si cette entrée signale un blocage critique"
            )
        
        submitted = st.form_submit_button("📝 Ajouter l'entrée", type="primary")
        
        if submitted:
            if contenu.strip():
                try:
                    if db.add_journal_entry(
                        operation_id=operation_id,
                        auteur=auteur,
                        type_action=type_action,
                        contenu=contenu.strip(),
                        phase_concernee=phase_concernee if phase_concernee.strip() else None,
                        est_blocage=est_blocage or type_action == "BLOCAGE",
                        niveau_urgence=niveau_urgence
                    ):
                        add_notification("Entrée journal ajoutée avec succès", "success")
                        
                        # Si c'est un blocage, informer de la génération automatique d'alerte
                        if est_blocage or type_action == "BLOCAGE":
                            add_notification("Alerte automatique générée pour ce blocage", "warning")
                        
                        st.rerun()
                    else:
                        add_notification("Erreur lors de l'ajout de l'entrée", "error")
                except Exception as e:
                    add_notification(f"Erreur : {e}", "error")
            else:
                add_notification("Veuillez saisir un contenu", "warning")
    
    st.markdown("---")
    
    # Filtres pour le journal
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtre_type = st.selectbox(
            "Filtrer par type:",
            options=["Tous", "BLOCAGE", "ATTENTION", "VALIDATION", "INFO", "OBSERVATION"],
            key="filtre_type_journal"
        )
    
    with col2:
        inclure_resolus = st.checkbox(
            "Inclure blocages résolus",
            value=True,
            key="inclure_resolus"
        )
    
    with col3:
        limite_entries = st.selectbox(
            "Nombre d'entrées:",
            options=[10, 25, 50, 100],
            index=1,
            key="limite_journal"
        )
    
    # Récupération des entrées journal
    try:
        journal_entries = db.get_journal_by_operation(
            operation_id, 
            include_resolved=inclure_resolus,
            limit=limite_entries
        )
        
        # Appliquer le filtre type
        if filtre_type != "Tous":
            journal_entries = [entry for entry in journal_entries if entry.get('type_action') == filtre_type]
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération du journal : {e}")
        return
    
    # Affichage des entrées
    if journal_entries:
        st.markdown(f"#### 📚 Historique ({len(journal_entries)} entrées)")
        
        for entry in journal_entries:
            # Couleur selon le type et l'état
            if entry.get('est_blocage', False):
                if entry.get('est_resolu', False):
                    card_class = "success-card"
                    icone = "✅"
                    type_display = "BLOCAGE RÉSOLU"
                else:
                    card_class = "alert-card"
                    icone = "🔴"
                    type_display = "BLOCAGE ACTIF"
            elif entry.get('type_action') == 'ATTENTION':
                card_class = "warning-card"
                icone = "⚠️"
                type_display = "ATTENTION"
            elif entry.get('type_action') == 'VALIDATION':
                card_class = "success-card"
                icone = "✅"
                type_display = "VALIDATION"
            else:
                card_class = "info-card"
                icone = "ℹ️"
                type_display = entry.get('type_action', 'INFO')
            
            # Date formatée
            date_saisie = entry.get('date_saisie', '')
            if date_saisie:
                try:
                    date_obj = datetime.strptime(date_saisie, '%Y-%m-%d %H:%M:%S')
                    date_fr = date_obj.strftime('%d/%m/%Y à %H:%M')
                except:
                    date_fr = date_saisie
            else:
                date_fr = "Date inconnue"
            
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px;">{icone}</span>
                        <strong>{type_display}</strong>
                        {f"<span style='color: #6b7280; margin-left: 10px;'>Phase: {entry.get('phase_concernee', '')}</span>" if entry.get('phase_concernee') else ""}
                    </div>
                    <div style="text-align: right; color: #6b7280; font-size: 0.8rem;">
                        <div>{entry.get('auteur', 'N/A')}</div>
                        <div>{date_fr}</div>
                    </div>
                </div>
                
                <div style="margin: 10px 0; line-height: 1.4;">
                    {entry.get('contenu', 'N/A')}
                </div>
                
                {f"<div style='margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px; font-size: 0.9rem;'><strong>Résolution:</strong> {entry.get('commentaire_resolution', '')} <em>par {entry.get('resolu_par', '')}</em></div>" if entry.get('est_resolu') and entry.get('commentaire_resolution') else ""}
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                    <div style="color: #6b7280; font-size: 0.8rem;">
                        Urgence: {"🔥" * entry.get('niveau_urgence', 1)} ({entry.get('niveau_urgence', 1)}/5)
                    </div>
                    <div>
                        {f'<button style="background: #10b981; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">Résoudre</button>' if entry.get('est_blocage') and not entry.get('est_resolu') else ''}
                    </div>
                </div>
            </div>
            <br>
            """, unsafe_allow_html=True)
            
            # Bouton de résolution pour les blocages actifs
            if entry.get('est_blocage', False) and not entry.get('est_resolu', False):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"✅ Résoudre", key=f"resolve_{entry['id']}"):
                        st.session_state[f"resolving_{entry['id']}"] = True
                
                # Interface de résolution
                if st.session_state.get(f"resolving_{entry['id']}", False):
                    with st.form(f"resolve_form_{entry['id']}"):
                        commentaire_resolution = st.text_area(
                            "Commentaire de résolution:",
                            placeholder="Expliquez comment le blocage a été résolu...",
                            key=f"comment_resolve_{entry['id']}"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirmer résolution"):
                                if commentaire_resolution.strip():
                                    try:
                                        if db.resolve_blocage(
                                            entry['id'], 
                                            st.session_state.get('selected_aco', 'Utilisateur'),
                                            commentaire_resolution.strip()
                                        ):
                                            add_notification("Blocage résolu avec succès", "success")
                                            st.session_state[f"resolving_{entry['id']}"] = False
                                            st.rerun()
                                        else:
                                            add_notification("Erreur lors de la résolution", "error")
                                    except Exception as e:
                                        add_notification(f"Erreur : {e}", "error")
                                else:
                                    add_notification("Veuillez saisir un commentaire", "warning")
                        
                        with col2:
                            if st.form_submit_button("❌ Annuler"):
                                st.session_state[f"resolving_{entry['id']}"] = False
                                st.rerun()
                
                st.markdown("---")
    else:
        st.markdown("""
        <div class="info-card">
            📝 Aucune entrée de journal pour cette opération. Commencez par ajouter une entrée ci-dessus.
        </div>
        """, unsafe_allow_html=True)

def render_timeline_tab(operation_id: int, db):
    """Onglet timeline avec visualisations enrichies"""
    
    st.markdown("### 📊 Timeline Interactive")
    
    # Sélection du type de visualisation
    col1, col2 = st.columns([3, 1])
    
    with col1:
        type_timeline = st.radio(
            "Type de visualisation:",
            options=["chronologique", "mental_map"],
            format_func=lambda x: {
                "chronologique": "📅 Timeline Chronologique (Phases + Journal + Alertes)",
                "mental_map": "🧠 Carte Mentale par Domaines"
            }[x],
            key="timeline_type",
            horizontal=True
        )
    
    with col2:
        if st.button("🔄 Actualiser Timeline"):
            st.cache_data.clear()
            add_notification("Timeline actualisée", "success")
            st.rerun()
    
    # Récupération des données pour la timeline
    try:
        timeline_data = db.get_timeline_data(operation_id)
        if not timeline_data or not timeline_data.get('phases'):
            st.warning("Aucune donnée disponible pour la timeline")
            return
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données timeline : {e}")
        return
    
    # Statistiques rapides de la timeline
    nb_phases = len(timeline_data.get('phases', []))
    nb_journal = len(timeline_data.get('journal_entries', []))
    nb_alertes = len(timeline_data.get('alertes', []))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        display_metric_card("Phases", str(nb_phases))
    with col2:
        display_metric_card("Entrées Journal", str(nb_journal))
    with col3:
        display_metric_card("Alertes Actives", str(nb_alertes))
    
    # Génération et affichage de la timeline
    try:
        with st.spinner("Génération de la timeline..."):
            timeline_html = utils.generate_timeline(operation_id, timeline_data, type_timeline)
        
        if timeline_html:
            st.markdown("""
            <div class="timeline-container">
            """, unsafe_allow_html=True)
            
            if type_timeline == "chronologique":
                # Pour la timeline chronologique, utiliser st.plotly_chart si c'est du HTML plotly
                if "plotly" in timeline_html.lower():
                    st.components.v1.html(timeline_html, height=600, scrolling=True)
                else:
                    st.markdown(timeline_html, unsafe_allow_html=True)
            else:
                # Pour la carte mentale, affichage direct HTML
                st.markdown(timeline_html, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("Impossible de générer la timeline")
            
    except Exception as e:
        st.error(f"Erreur lors de la génération de la timeline : {e}")
    
    # Légende et informations
    st.markdown("---")
    
    if type_timeline == "chronologique":
        st.markdown("""
        #### 📖 Légende Timeline Chronologique
        
        **Couleurs des phases :**
        - 🟢 **Vert** : Phase validée
        - 🟡 **Jaune** : Phase en cours
        - 🔴 **Rouge** : Phase en retard ou bloquée
        - 🟠 **Orange** : Échéance proche (≤ 7 jours)
        
        **Éléments timeline :**
        - 📌 **Phases** : Barres horizontales avec durée
        - 📝 **Journal** : Événements importants
        - 🚨 **Alertes** : Notifications actives
        - 📅 **Ligne rouge** : Date actuelle
        """)
    else:
        st.markdown("""
        #### 🧠 Carte Mentale par Domaines
        
        **Domaines organisés :**
        - 🏗️ **Opérationnel** : Phases techniques et opérationnelles
        - ⚖️ **Juridique** : Autorisations, marchés, contrats
        - 💰 **Budgétaire** : Financement, REM, budget
        
        **États des phases :**
        - ✅ Validée | ⏳ En cours | ⏰ En retard | 🔴 Bloquée
        - 💰 Icône REM = Impact sur la rentabilité
        """)
    
    # Exportation des données timeline
    with st.expander("📊 Données Détaillées & Export"):
        
        if timeline_data.get('phases'):
            st.markdown("**Phases de l'opération :**")
            phases_df = pd.DataFrame(timeline_data['phases'])
            
            # Colonnes à afficher
            colonnes_phases = ['sous_phase', 'phase_principale', 'ordre_phase', 'est_validee', 
                             'domaine', 'responsable_principal', 'date_fin_prevue']
            colonnes_disponibles = [col for col in colonnes_phases if col in phases_df.columns]
            
            if colonnes_disponibles:
                st.dataframe(
                    phases_df[colonnes_disponibles],
                    column_config={
                        "sous_phase": "Phase",
                        "phase_principale": "Groupe",
                        "ordre_phase": "Ordre",
                        "est_validee": "Validée",
                        "domaine": "Domaine",
                        "responsable_principal": "Responsable",
                        "date_fin_prevue": "Échéance"
                    },
                    use_container_width=True
                )
        
        # Export Excel si demandé
        if st.button("📤 Exporter Timeline Excel"):
            try:
                with st.spinner("Génération du fichier Excel..."):
                    excel_data = utils.export_to_excel_streamlit(
                        [db.get_operation_detail(operation_id)],
                        {operation_id: timeline_data.get('phases', [])}
                    )
                
                if excel_data:
                    st.download_button(
                        label="📥 Télécharger le fichier Excel",
                        data=excel_data,
                        file_name=f"timeline_operation_{operation_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    add_notification("Fichier Excel généré avec succès", "success")
                else:
                    add_notification("Erreur lors de la génération Excel", "error")
            except Exception as e:
                add_notification(f"Erreur export : {e}", "error")

def render_creation_operation():
    """Page de création d'opération avec formulaire dynamique par type"""
    
    st.markdown("""
    <div class="main-header">
        <h1>➕ Créer une Nouvelle Opération</h1>
        <p>Formulaire adaptatif selon le type d'opération sélectionné</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = init_database()
    
    # Étape 1 : Sélection du type d'opération
    st.markdown("### 1️⃣ Type d'Opération")
    
    type_operation = st.radio(
        "Choisissez le type d'opération :",
        options=config.TYPES_OPERATIONS,
        format_func=lambda x: {
            "OPP": "🏗️ Opération Propre (OPP) - Construction en maîtrise d'ouvrage directe",
            "VEFA": "🏢 Vente État Futur Achèvement (VEFA) - Acquisition chez promoteur",
            "AMO": "🤝 Assistance Maîtrise Ouvrage (AMO) - Mission de conseil",
            "MANDAT": "📜 Opération en Mandat - Mandat de maîtrise d'ouvrage"
        }[x],
        key="type_operation_creation"
    )
    
    st.markdown("---")
    
    # Formulaire adaptatif selon le type
    with st.form("creation_operation_form"):
        
        # Étape 2 : Champs communs
        st.markdown("### 2️⃣ Informations Générales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nom_operation = st.text_input(
                "Nom de l'opération *",
                placeholder="Ex: 44 COUR CHARNEAU",
                help="Nom unique identifiant l'opération"
            )
            
            # Récupération des ACO disponibles
            try:
                acos_disponibles = [aco['nom_aco'] for aco in db.get_acos_list()]
                if not acos_disponibles:
                    st.error("Aucun ACO configuré. Veuillez d'abord ajouter des ACO.")
                    return
                
                responsable_aco = st.selectbox(
                    "Responsable ACO *",
                    options=acos_disponibles,
                    help="Chargé d'opération responsable"
                )
            except Exception as e:
                st.error(f"Erreur récupération ACO : {e}")
                return
            
            commune = st.text_input(
                "Commune",
                placeholder="Ex: LES ABYMES"
            )
        
        with col2:
            nb_logements_total = st.number_input(
                "Nombre total de logements",
                min_value=0,
                value=0,
                help="Nombre total de logements prévus"
            )
            
            phase_actuelle_ordre = st.number_input(
                "Phase actuelle (ordre) *",
                min_value=1,
                value=1,
                help="Ordre de la phase où se trouve actuellement l'opération (pour calcul statut automatique)"
            )
            
            date_livraison_cible = st.date_input(
                "Date livraison cible",
                value=None,
                help="Date de livraison prévue (optionnel)"
            )
        
        st.markdown("---")
        
        # Étape 3 : Champs spécifiques selon le type
        st.markdown("### 3️⃣ Informations Spécifiques")
        
        if type_operation == "OPP":
            render_opp_specific_fields()
        elif type_operation == "VEFA":
            render_vefa_specific_fields()
        elif type_operation == "AMO":
            render_amo_specific_fields()
        elif type_operation == "MANDAT":
            render_mandat_specific_fields()
        
        st.markdown("---")
        
        # Bouton de soumission
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Créer l'Opération",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            # Validation des champs obligatoires
            if not nom_operation or not nom_operation.strip():
                st.error("Le nom de l'opération est obligatoire")
                return
            
            if not responsable_aco:
                st.error("Le responsable ACO est obligatoire")
                return
            
            # Récupération des données du formulaire selon le type
            operation_data = {
                'nom': nom_operation.strip(),
                'type_operation': type_operation,
                'responsable_aco': responsable_aco,
                'commune': commune.strip() if commune else "",
                'nb_logements_total': nb_logements_total,
                'phase_actuelle_ordre': phase_actuelle_ordre,
                'date_livraison_cible': date_livraison_cible.isoformat() if date_livraison_cible else None
            }
            
            # Ajouter les champs spécifiques depuis session_state
            operation_data.update(get_specific_fields_data(type_operation))
            
            # Création de l'opération
            try:
                with st.spinner("Création de l'opération en cours..."):
                    operation_id = db.create_operation(**operation_data)
                
                if operation_id:
                    add_notification(f"Opération '{nom_operation}' créée avec succès (ID: {operation_id})", "success")
                    
                    # Redirection vers la vue détail
                    st.session_state.operation_detail_id = operation_id
                    st.session_state.current_page = "detail_operation"
                    
                    # Petit délai pour voir la notification
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erreur lors de la création de l'opération")
                    
            except Exception as e:
                st.error(f"Erreur création : {e}")

def render_opp_specific_fields():
    """Champs spécifiques pour les opérations OPP"""
    
    st.markdown("#### 🏗️ Spécifique Opération Propre (OPP)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏠 Programme**")
        
        nb_lls = st.number_input("Nb logements LLS", min_value=0, value=0, key="opp_nb_lls")
        nb_llts = st.number_input("Nb logements LLTS", min_value=0, value=0, key="opp_nb_llts")
        nb_pls = st.number_input("Nb logements PLS", min_value=0, value=0, key="opp_nb_pls")
        
        # Calcul automatique du total
        total_calcule = nb_lls + nb_llts + nb_pls
        if total_calcule > 0:
            st.info(f"Total calculé : {total_calcule} logements")
        
        st.markdown("**📍 Foncier**")
        adresse_terrain = st.text_input("Adresse du terrain", key="opp_adresse")
        surface_terrain = st.number_input("Surface terrain (m²)", min_value=0.0, value=0.0, key="opp_surface")
    
    with col2:
        st.markdown("**💰 Budget**")
        
        budget_total = st.number_input(
            "Budget total estimé (€)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="opp_budget_total",
            help="Budget total prévisionnel de l'opération"
        )
        
        cout_foncier = st.number_input(
            "Coût foncier (€)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="opp_cout_foncier"
        )
        
        cout_travaux = st.number_input(
            "Coût travaux estimé (€)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="opp_cout_travaux"
        )
        
        st.markdown("**📅 Planning Initial**")
        date_debut_etudes = st.date_input(
            "Date début études",
            value=None,
            key="opp_date_debut_etudes"
        )
        
        # Affichage projection REM si budget disponible
        if budget_total > 0 and (nb_lls + nb_llts + nb_pls) > 0:
            st.markdown("**💡 Projection REM**")
            try:
                rem_projection = config.calculate_rem_projection({
                    'nb_lls': nb_lls,
                    'nb_llts': nb_llts,
                    'nb_pls': nb_pls,
                    'budget_total': budget_total
                })
                
                if 'erreur' not in rem_projection:
                    st.success(f"REM annuelle estimée : {utils.format_currency(rem_projection.get('rem_annuelle', 0))}")
                    
                    # Détail par type
                    repartition = rem_projection.get('repartition', {})
                    if any(repartition.values()):
                        st.markdown("**Répartition :**")
                        for type_log, montant in repartition.items():
                            if montant > 0:
                                st.write(f"• {type_log}: {utils.format_currency(montant)}")
                else:
                    st.warning("Impossible de calculer la projection REM")
            except Exception as e:
                st.warning(f"Erreur calcul REM : {e}")

def render_vefa_specific_fields():
    """Champs spécifiques pour les opérations VEFA"""
    
    st.markdown("#### 🏢 Spécifique VEFA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👔 Promoteur**")
        
        promoteur = st.selectbox(
            "Nom promoteur *",
            options=[""] + config.INTERVENANTS_BASE.get('Promoteurs', []),
            key="vefa_promoteur",
            help="Sélectionnez le promoteur partenaire"
        )
        
        if promoteur == "":
            promoteur_autre = st.text_input(
                "Autre promoteur:",
                placeholder="Nom du promoteur",
                key="vefa_promoteur_autre"
            )
            if promoteur_autre:
                promoteur = promoteur_autre
        
        nom_programme = st.text_input(
            "Nom du programme",
            placeholder="Ex: Résidence du Parc",
            key="vefa_programme"
        )
        
        nb_logements_reserves = st.number_input(
            "Nb logements réservés *",
            min_value=0,
            value=0,
            key="vefa_nb_reserves",
            help="Nombre de logements réservés chez le promoteur"
        )
    
    with col2:
        st.markdown("**💰 Conditions VEFA**")
        
        prix_reservation = st.number_input(
            "Prix de réservation (€) *",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="vefa_prix",
            help="Prix total de la réservation VEFA"
        )
        
        st.markdown("**📅 Planning Promoteur**")
        
        date_signature_vefa = st.date_input(
            "Date signature VEFA prévue",
            value=None,
            key="vefa_date_signature"
        )
        
        date_pc_promoteur = st.date_input(
            "Date PC promoteur",
            value=None,
            key="vefa_date_pc"
        )
        
         # Estimation coût par logement
        if prix_reservation > 0 and nb_logements_reserves > 0:
            cout_par_logement = prix_reservation / nb_logements_reserves
            st.info(f"Coût par logement : {utils.format_currency(cout_par_logement)}")
        
        # Projection REM VEFA
        if prix_reservation > 0 and nb_logements_reserves > 0:
            st.markdown("**💡 Projection REM VEFA**")
            try:
                # Pour VEFA, estimation basée sur le prix et supposer une répartition type
                nb_lls_estime = int(nb_logements_reserves * 0.6)  # 60% LLS par défaut
                nb_llts_estime = int(nb_logements_reserves * 0.3)  # 30% LLTS
                nb_pls_estime = nb_logements_reserves - nb_lls_estime - nb_llts_estime
                
                rem_projection = config.calculate_rem_projection({
                    'nb_lls': nb_lls_estime,
                    'nb_llts': nb_llts_estime,
                    'nb_pls': nb_pls_estime,
                    'budget_total': prix_reservation
                })
                
                if 'erreur' not in rem_projection:
                    st.success(f"REM annuelle estimée : {utils.format_currency(rem_projection.get('rem_annuelle', 0))}")
                    st.caption("*Estimation basée sur une répartition type : 60% LLS, 30% LLTS, 10% PLS*")
                else:
                    st.warning("Impossible de calculer la projection REM")
            except Exception as e:
                st.warning(f"Erreur calcul REM : {e}")

def render_amo_specific_fields():
    """Champs spécifiques pour les missions AMO"""
    
    st.markdown("#### 🤝 Spécifique Mission AMO")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👤 Maître d'Ouvrage Client**")
        
        moa_cliente = st.text_input(
            "Nom MOA cliente *",
            placeholder="Ex: SEM GUADELOUPE AMENAGEMENT",
            key="amo_moa",
            help="Organisme pour lequel nous intervenons en AMO"
        )
        
        contact_principal = st.text_input(
            "Contact principal",
            placeholder="Nom et fonction du contact",
            key="amo_contact"
        )
        
        type_organisme = st.selectbox(
            "Type d'organisme",
            options=["", "SEM", "SPL", "Collectivité", "Bailleur social", "Privé", "Autre"],
            key="amo_type_organisme"
        )
        
        st.markdown("**🎯 Mission**")
        
        perimetre_mission = st.multiselect(
            "Périmètre mission *",
            options=[
                "Assistance programmation",
                "Assistance choix MOE", 
                "Assistance DCE",
                "Assistance consultation entreprises",
                "Suivi travaux",
                "Assistance réception",
                "Autre"
            ],
            key="amo_perimetre",
            help="Sélectionnez les phases couvertes par la mission"
        )
        
        if "Autre" in perimetre_mission:
            autre_perimetre = st.text_input(
                "Précisez autre périmètre:",
                key="amo_autre_perimetre"
            )
    
    with col2:
        st.markdown("**💰 Conditions Mission**")
        
        montant_honoraires = st.number_input(
            "Montant honoraires (€)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="amo_honoraires",
            help="Montant total des honoraires AMO"
        )
        
        mode_remuneration = st.selectbox(
            "Mode de rémunération",
            options=["", "Forfait", "Pourcentage travaux", "Régie", "Mixte"],
            key="amo_mode_remuneration"
        )
        
        st.markdown("**📅 Planning Mission**")
        
        date_debut_mission = st.date_input(
            "Date début mission",
            value=None,
            key="amo_date_debut"
        )
        
        date_fin_mission = st.date_input(
            "Date fin mission prévue",
            value=None,
            key="amo_date_fin"
        )
        
        # Calcul de la durée de mission
        if date_debut_mission and date_fin_mission:
            duree_mission = (date_fin_mission - date_debut_mission).days
            if duree_mission > 0:
                st.info(f"Durée mission : {duree_mission} jours ({duree_mission/30:.1f} mois)")
            elif duree_mission < 0:
                st.error("La date de fin doit être postérieure à la date de début")
        
        # Calcul REM pour mission AMO
        if montant_honoraires > 0:
            st.markdown("**💡 REM Mission AMO**")
            # Pour AMO, la REM est directement liée aux honoraires
            rem_amo_annuelle = montant_honoraires  # Simplification : honoraires = REM sur période
            if date_debut_mission and date_fin_mission:
                duree_mois = max(1, (date_fin_mission - date_debut_mission).days / 30)
                rem_amo_mensuelle = montant_honoraires / duree_mois
                st.success(f"REM mission : {utils.format_currency(montant_honoraires)}")
                st.info(f"REM mensuelle estimée : {utils.format_currency(rem_amo_mensuelle)}")
            else:
                st.success(f"REM mission : {utils.format_currency(rem_amo_annuelle)}")

def render_mandat_specific_fields():
    """Champs spécifiques pour les opérations en mandat"""
    
    st.markdown("#### 📜 Spécifique Opération en Mandat")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👥 Mandant**")
        
        organisme_mandant = st.text_input(
            "Nom organisme mandant *",
            placeholder="Ex: Conseil Départemental de Guadeloupe",
            key="mandat_organisme",
            help="Organisme qui nous confie le mandat"
        )
        
        contact_signataire = st.text_input(
            "Contact signataire",
            placeholder="Nom et fonction",
            key="mandat_contact"
        )
        
        type_mandant = st.selectbox(
            "Type de mandant",
            options=["", "Conseil Départemental", "Conseil Régional", "Commune", "EPCI", "État", "Autre collectivité", "Organisme public", "Autre"],
            key="mandat_type"
        )
        
        st.markdown("**📋 Convention Mandat**")
        
        objet_mandat = st.text_area(
            "Objet du mandat *",
            placeholder="Décrivez l'objet du mandat...",
            key="mandat_objet",
            help="Description précise de la mission confiée",
            height=100
        )
        
        etendue_mission = st.multiselect(
            "Étendue mission",
            options=[
                "Études préalables",
                "Montage opération", 
                "Maîtrise d'ouvrage complète",
                "Assistance technique",
                "Gestion administrative",
                "Suivi financier",
                "Autre"
            ],
            key="mandat_etendue"
        )
    
    with col2:
        st.markdown("**💰 Conditions Financières**")
        
        budget_operation = st.number_input(
            "Budget opération (€)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="mandat_budget",
            help="Budget total de l'opération mandatée"
        )
        
        remuneration_spic = st.number_input(
            "Rémunération SPIC (€)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="mandat_remuneration",
            help="Rémunération SPIC pour le mandat"
        )
        
        mode_remuneration = st.selectbox(
            "Mode rémunération",
            options=["", "Forfait", "Pourcentage budget", "Régie", "Mixte"],
            key="mandat_mode_remuneration"
        )
        
        st.markdown("**📅 Durée & Échéances**")
        
        date_signature_convention = st.date_input(
            "Date signature convention",
            value=None,
            key="mandat_date_signature"
        )
        
        duree_mandat_mois = st.number_input(
            "Durée du mandat (mois)",
            min_value=1,
            value=12,
            key="mandat_duree",
            help="Durée prévue du mandat en mois"
        )
        
        # Calcul date fin mandat
        if date_signature_convention and duree_mandat_mois:
            from datetime import timedelta
            date_fin_mandat = date_signature_convention + timedelta(days=duree_mandat_mois * 30)
            st.info(f"Fin mandat prévue : {utils.format_date_fr(date_fin_mandat.isoformat())}")
        
        # Calcul REM mandat
        if remuneration_spic > 0 and duree_mandat_mois > 0:
            st.markdown("**💡 REM Mandat**")
            rem_annuelle_mandat = (remuneration_spic / duree_mandat_mois) * 12
            rem_mensuelle = remuneration_spic / duree_mandat_mois
            
            st.success(f"REM annuelle équivalente : {utils.format_currency(rem_annuelle_mandat)}")
            st.info(f"REM mensuelle : {utils.format_currency(rem_mensuelle)}")
            
            # Pourcentage sur budget si disponible
            if budget_operation > 0:
                pourcentage_budget = (remuneration_spic / budget_operation) * 100
                st.info(f"Rémunération = {pourcentage_budget:.2f}% du budget opération")

def get_specific_fields_data(type_operation: str) -> dict:
    """Récupère les données des champs spécifiques depuis session_state"""
    
    data = {}
    
    if type_operation == "OPP":
        data.update({
            'nb_lls': st.session_state.get('opp_nb_lls', 0),
            'nb_llts': st.session_state.get('opp_nb_llts', 0),
            'nb_pls': st.session_state.get('opp_nb_pls', 0),
            'budget_total': st.session_state.get('opp_budget_total', 0.0),
            'cout_foncier': st.session_state.get('opp_cout_foncier', 0.0),
            'cout_travaux_estime': st.session_state.get('opp_cout_travaux', 0.0),
            'adresse_terrain': st.session_state.get('opp_adresse', ''),
            'surface_terrain_m2': st.session_state.get('opp_surface', 0.0),
            'date_debut_etudes': st.session_state.get('opp_date_debut_etudes').isoformat() if st.session_state.get('opp_date_debut_etudes') else None
        })
    
    elif type_operation == "VEFA":
        promoteur = st.session_state.get('vefa_promoteur', '')
        if not promoteur:
            promoteur = st.session_state.get('vefa_promoteur_autre', '')
        
        data.update({
            'promoteur': promoteur,
            'nb_logements_total': st.session_state.get('vefa_nb_reserves', 0),
            'budget_total': st.session_state.get('vefa_prix', 0.0)
        })
    
    elif type_operation == "AMO":
        data.update({
            'budget_total': st.session_state.get('amo_honoraires', 0.0),
            'date_debut_etudes': st.session_state.get('amo_date_debut').isoformat() if st.session_state.get('amo_date_debut') else None
        })
    
    elif type_operation == "MANDAT":
        data.update({
            'budget_total': st.session_state.get('mandat_budget', 0.0)
        })
    
    return data

# ============================================================================
# NAVIGATION ET ROUTING
# ============================================================================

def render_sidebar():
    """Sidebar de navigation moderne et intuitive"""
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; margin-bottom: 1rem;">
            <h2 style="margin: 0;">🏗️ SPIC 2.0</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Suivi Opérations</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu principal
        st.markdown("### 📊 Navigation")
        
        # Boutons de navigation avec icônes
        nav_buttons = [
            ("dashboard_manager", "📊 Dashboard Manager", "Vue d'ensemble et TOP 3 risques"),
            ("aco_view", "👤 Vue Chargé d'Op", "Interface personnalisée ACO"),
            ("creation_operation", "➕ Créer Opération", "Nouvelle opération"),
        ]
        
        for page_key, label, description in nav_buttons:
            is_current = st.session_state.current_page == page_key
            
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                st.session_state.current_page = page_key
                st.session_state.operation_detail_id = None  # Reset detail view
                st.rerun()
            
            if is_current:
                st.markdown(f"*{description}*")
        
        st.markdown("---")
        
        # Informations système
        st.markdown("### ⚙️ Système")
        
        # Statut base de données
        try:
            db = init_database()
            stats = db.get_database_stats()
            
            if stats:
                st.markdown("**📊 Statistiques Base**")
                st.metric("Opérations", stats.get('total_operations', 0))
                st.metric("Phases", stats.get('total_phases', 0))
                st.metric("Alertes", stats.get('total_alertes', 0))
                
                if stats.get('taille_db_mo', 0) > 0:
                    st.metric("Taille DB", f"{stats['taille_db_mo']:.1f} MB")
        except Exception as e:
            st.error(f"Erreur stats DB : {e}")
        
        # Cache et performance
        if st.button("🔄 Vider Cache", use_container_width=True):
            utils.clear_streamlit_cache()
            add_notification("Cache vidé", "success")
            st.rerun()
        
        # Raccourcis rapides
        st.markdown("### ⚡ Raccourcis")
        
        if st.button("🚨 Alertes Actives", use_container_width=True):
            # TODO: Implémenter vue alertes
            add_notification("Vue alertes en développement", "info")
        
        if st.button("📤 Export Données", use_container_width=True):
            # TODO: Implémenter export global
            add_notification("Export global en développement", "info")
        
        # Informations de session
        st.markdown("---")
        st.markdown("### 🔍 Session Info")
        
        if st.session_state.get('selected_aco'):
            st.markdown(f"**ACO:** {st.session_state.selected_aco}")
        
        if st.session_state.get('operation_detail_id'):
            st.markdown(f"**Op. Détail:** ID {st.session_state.operation_detail_id}")
        
        st.markdown(f"**Dernière MAJ:** {st.session_state.last_refresh.strftime('%H:%M')}")
        
        # Version et aide
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #6b7280; font-size: 0.8rem;">
            <p>Version 2.0.0<br>
            Interface épurée et collaborative</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Fonction principale de l'application Streamlit"""
    
    # Initialisation
    init_session_state()
    display_notifications()
    
    # Sidebar
    render_sidebar()
    
    # Contenu principal selon la page
    current_page = st.session_state.current_page
    
    try:
        if current_page == "dashboard_manager":
            render_dashboard_manager()
        
        elif current_page == "aco_view":
            render_aco_view()
        
        elif current_page == "creation_operation":
            render_creation_operation()
        
        elif current_page == "detail_operation":
            render_operation_detail()
        
        else:
            st.error(f"Page inconnue : {current_page}")
            st.session_state.current_page = "dashboard_manager"
            st.rerun()
    
    except Exception as e:
        st.error(f"Erreur lors du rendu de la page : {e}")
        st.markdown("**Détails de l'erreur :**")
        st.code(str(e))
        
        # Bouton de retour au dashboard
        if st.button("🏠 Retour au Dashboard"):
            st.session_state.current_page = "dashboard_manager"
            st.rerun()
    
    # Footer avec informations utiles
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("🔄 **Auto-refresh** : Toutes les 5 minutes")
    
    with col2:
        st.markdown(f"⏰ **Dernière actualisation** : {st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M')}")
    
    with col3:
        if st.button("🔄 Actualiser maintenant"):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            add_notification("Données actualisées", "success")
            st.rerun()
    
    # Auto-refresh toutes les 5 minutes
    if (datetime.now() - st.session_state.last_refresh).seconds > 300:  # 5 minutes
        st.session_state.last_refresh = datetime.now()
        st.cache_data.clear()
        st.rerun()

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()