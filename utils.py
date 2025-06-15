# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour l'application SPIC
Gestion des calculs, visualisations, alertes et formatage
"""

import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import base64
import io
from typing import List, Dict, Optional
try:
    from pyvis.network import Network
except ImportError:
    Network = None

import config
import database


def calculate_progress(phases_data: List[Dict]) -> float:
    """
    Calcule le pourcentage d'avancement d'une opération
    basé sur les phases validées
    """
    try:
        if not phases_data:
            return 0.0
        
        total_phases = len(phases_data)
        phases_validees = sum(1 for phase in phases_data if phase.get('est_validee', False))
        
        return round((phases_validees / total_phases) * 100, 1)
    
    except Exception as e:
        st.error(f"Erreur calcul avancement: {e}")
        return 0.0


def format_currency(amount: float) -> str:
    """
    Formate un montant en euros avec séparateurs
    """
    try:
        if amount == 0:
            return "0 €"
        return f"{amount:,.0f} €".replace(",", " ")
    except:
        return "0 €"


def format_dates(date_obj) -> str:
    """
    Formate une date pour affichage
    """
    try:
        if date_obj is None:
            return "-"
        
        if isinstance(date_obj, str):
            date_obj = datetime.datetime.strptime(date_obj, "%Y-%m-%d").date()
        
        return date_obj.strftime("%d/%m/%Y")
    except:
        return "-"


def get_status_color(statut: str) -> str:
    """
    Retourne la couleur associée à un statut
    """
    colors = {
        "🟡 À l'étude": "#FEF3C7",
        "🛠️ En consultation": "#DBEAFE",
        "📋 Marché attribué": "#E0E7FF",
        "🚧 En travaux": "#FED7AA",
        "📦 Livré (non soldé)": "#BBF7D0",
        "📄 En GPA": "#C7D2FE",
        "✅ Clôturé (soldé)": "#D1FAE5",
        "🔴 Bloqué": "#FECACA"
    }
    return colors.get(statut, "#F3F4F6")


def create_kpi_chart(operations_data: List[Dict]):
    """
    Crée un graphique des KPI pour la vue manager
    """
    try:
        if not operations_data:
            return None
        
        df = pd.DataFrame(operations_data)
        
        # Graphique répartition par statut
        status_counts = df['statut_principal'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Répartition des opérations par statut",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erreur création graphique: {e}")
        return None


def create_timeline_chart(phases_data: List[Dict]):
    """
    Crée un diagramme de Gantt pour les phases
    """
    try:
        if not phases_data:
            return None
        
        df = pd.DataFrame(phases_data)
        df = df[df['date_debut_prevue'].notna() & df['date_fin_prevue'].notna()]
        
        if df.empty:
            return None
        
        fig = px.timeline(
            df,
            x_start="date_debut_prevue",
            x_end="date_fin_prevue",
            y="sous_phase",
            color="est_validee",
            title="Planning des phases",
            color_discrete_map={True: "green", False: "orange"}
        )
        
        fig.update_layout(height=600)
        return fig
        
    except Exception as e:
        st.error(f"Erreur création timeline: {e}")
        return None


def generate_timeline(operation_id: int, db: database.DatabaseManager):
    """
    Génère une frise chronologique interactive avec PyVis
    """
    try:
        if Network is None:
            st.warning("PyVis non disponible. Installez avec: pip install pyvis")
            return None
        
        phases_data = db.get_phases_by_operation(operation_id)
        if not phases_data:
            return None
        
        net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
        
        for i, phase in enumerate(phases_data):
            color = "#28a745" if phase['est_validee'] else "#ffc107"
            size = 30 if phase['est_validee'] else 20
            
            net.add_node(
                i,
                label=phase['sous_phase'],
                color=color,
                size=size,
                title=f"Phase: {phase['sous_phase']}\nStatut: {'Validée' if phase['est_validee'] else 'En attente'}"
            )
            
            if i > 0:
                net.add_edge(i-1, i, arrows="to")
        
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          },
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "LR"
            }
          }
        }
        """)
        
        return net
        
    except Exception as e:
        st.error(f"Erreur génération timeline: {e}")
        return None


def create_mental_map(phases_data: List[Dict]):
    """
    Crée une carte mentale des phases
    """
    try:
        if Network is None or not phases_data:
            return None
        
        net = Network(height="400px", width="100%", bgcolor="#f8f9fa")
        
        phases_by_main = {}
        for phase in phases_data:
            main_phase = phase['phase_principale']
            if main_phase not in phases_by_main:
                phases_by_main[main_phase] = []
            phases_by_main[main_phase].append(phase)
        
        # Ajouter les nœuds des phases principales
        for main_phase in phases_by_main.keys():
            net.add_node(
                main_phase,
                label=main_phase,
                color="#007bff",
                size=40,
                font={'size': 16, 'color': 'white'}
            )
        
        # Ajouter les sous-phases
        for main_phase, sub_phases in phases_by_main.items():
            for sub_phase in sub_phases:
                color = "#28a745" if sub_phase['est_validee'] else "#ffc107"
                net.add_node(
                    sub_phase['id'],
                    label=sub_phase['sous_phase'],
                    color=color,
                    size=25
                )
                net.add_edge(main_phase, sub_phase['id'])
        
        return net
        
    except Exception as e:
        st.error(f"Erreur création carte mentale: {e}")
        return None


def check_alerts(operation_id: int, db: database.DatabaseManager) -> List[Dict]:
    """
    Vérifie et génère les alertes pour une opération
    """
    try:
        alerts = []
        phases_data = db.get_phases_by_operation(operation_id)
        
        for phase in phases_data:
            if not phase['est_validee'] and phase['date_fin_prevue']:
                date_fin = datetime.datetime.strptime(phase['date_fin_prevue'], "%Y-%m-%d").date()
                today = datetime.date.today()
                
                if date_fin < today:
                    alerts.append({
                        'type': 'retard',
                        'niveau': 5,
                        'message': f"Phase '{phase['sous_phase']}' en retard depuis {(today - date_fin).days} jours",
                        'phase_id': phase['id']
                    })
                elif date_fin <= today + datetime.timedelta(days=7):
                    alerts.append({
                        'type': 'deadline_proche',
                        'niveau': 3,
                        'message': f"Phase '{phase['sous_phase']}' à finaliser avant {format_dates(date_fin)}",
                        'phase_id': phase['id']
                    })
        
        return alerts
        
    except Exception as e:
        st.error(f"Erreur vérification alertes: {e}")
        return []


def validate_file_upload(uploaded_file) -> bool:
    """
    Valide un fichier uploadé
    """
    try:
        if uploaded_file is None:
            return False
        
        # Taille max: 10MB
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            st.error("Fichier trop volumineux (max 10MB)")
            return False
        
        # Types autorisés
        allowed_types = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xlsx']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_types:
            st.error(f"Type de fichier non autorisé: {file_extension}")
            return False
        
        return True
        
    except Exception as e:
        st.error(f"Erreur validation fichier: {e}")
        return False


def export_to_excel(operations_data: List[Dict], phases_data: List[Dict] = None) -> bytes:
    """
    Exporte les données vers Excel
    """
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Feuille opérations
            df_ops = pd.DataFrame(operations_data)
            df_ops.to_excel(writer, sheet_name='Opérations', index=False)
            
            # Feuille phases si fournie
            if phases_data:
                df_phases = pd.DataFrame(phases_data)
                df_phases.to_excel(writer, sheet_name='Phases', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Erreur export Excel: {e}")
        return b""


def get_operations_at_risk(operations_data: List[Dict], db: database.DatabaseManager) -> List[Dict]:
    """
    Identifie les opérations à risque
    """
    try:
        operations_at_risk = []
        
        for operation in operations_data:
            alerts = check_alerts(operation['id'], db)
            
            # Opération à risque si alertes niveau 4 ou 5
            high_priority_alerts = [a for a in alerts if a['niveau'] >= 4]
            
            if high_priority_alerts:
                operation_copy = operation.copy()
                operation_copy['alerts_count'] = len(high_priority_alerts)
                operation_copy['max_alert_level'] = max(a['niveau'] for a in high_priority_alerts)
                operations_at_risk.append(operation_copy)
        
        # Trier par niveau d'alerte décroissant
        operations_at_risk.sort(key=lambda x: x['max_alert_level'], reverse=True)
        
        return operations_at_risk[:3]  # Top 3
        
    except Exception as e:
        st.error(f"Erreur identification opérations à risque: {e}")
        return []


def display_phase_status(phase: Dict) -> str:
    """
    Retourne le HTML pour afficher le statut d'une phase
    """
    if phase['est_validee']:
        return '✅ Validée'
    else:
        return '⏳ En attente'


def calculate_duration_days(duration_str: str) -> int:
    """
    Convertit une durée en string vers nombre de jours
    """
    try:
        if 'semaine' in duration_str.lower():
            weeks = int(duration_str.split()[0])
            return weeks * 7
        elif 'mois' in duration_str.lower():
            months = int(duration_str.split()[0])
            return months * 30
        elif 'jour' in duration_str.lower():
            return int(duration_str.split()[0])
        else:
            return 30  # Défaut
    except:
        return 30
