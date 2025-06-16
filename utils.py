"""
Module utilitaires pour SPIC 2.0 - VERSION AMÉLIORÉE
Fonctions de calcul, visualisation et gestion des alertes
Intégration timeline colorée, frises chronologiques et alertes intelligentes
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import base64
from io import BytesIO
import json
import config

# ============================================================================
# CALCULS D'AVANCEMENT ET STATUTS
# ============================================================================

def calculate_progress(phases: List[Dict]) -> float:
    """Calcule le pourcentage d'avancement basé sur les phases validées"""
    
    if not phases:
        return 0.0
    
    total_phases = len(phases)
    phases_validees = sum(1 for phase in phases if phase.get('est_validee', False))
    
    return round((phases_validees / total_phases) * 100, 1)

def calculate_status_from_phases(phases: List[Dict], type_operation: str) -> str:
    """Calcule le statut automatique basé sur l'avancement des phases"""
    
    if not phases:
        return "🟡 À l'étude"
    
    # Vérifier s'il y a des blocages actifs
    for phase in phases:
        if phase.get('blocage_actif', False):
            return "🔴 Bloqué"
    
    # Calcul du pourcentage d'avancement
    pourcentage = calculate_progress(phases)
    
    # Logique de statut selon l'avancement (utilise config.py)
    return config.calculate_status_from_phases(phases, type_operation)

def get_current_phase(phases: List[Dict]) -> Dict:
    """Récupère la phase actuelle (première non validée)"""
    
    phases_triees = sorted(phases, key=lambda x: x.get('ordre_phase', 0))
    
    for phase in phases_triees:
        if not phase.get('est_validee', False):
            return phase
    
    # Si toutes les phases sont validées, retourner la dernière
    if phases_triees:
        return phases_triees[-1]
    
    return {}

def get_next_phases(phases: List[Dict], nb_phases: int = 3) -> List[Dict]:
    """Récupère les prochaines phases à traiter"""
    
    phases_triees = sorted(phases, key=lambda x: x.get('ordre_phase', 0))
    prochaines_phases = []
    
    phase_actuelle_trouvee = False
    
    for phase in phases_triees:
        if not phase.get('est_validee', False):
            if not phase_actuelle_trouvee:
                phase_actuelle_trouvee = True
                continue  # Skip la phase actuelle
            
            prochaines_phases.append(phase)
            if len(prochaines_phases) >= nb_phases:
                break
    
    return prochaines_phases

def detect_delays(phases: List[Dict]) -> List[Dict]:
    """Détecte les phases en retard"""
    
    phases_en_retard = []
    today = datetime.now().date()
    
    for phase in phases:
        if (not phase.get('est_validee', False) and 
            phase.get('date_fin_prevue')):
            
            try:
                date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                if today > date_fin:
                    jours_retard = (today - date_fin).days
                    phase_retard = phase.copy()
                    phase_retard['jours_retard'] = jours_retard
                    phases_en_retard.append(phase_retard)
            except:
                continue
    
    return sorted(phases_en_retard, key=lambda x: x.get('jours_retard', 0), reverse=True)

# ============================================================================
# SYSTÈME D'ALERTES ET CALCUL DE RISQUES
# ============================================================================

def check_alerts(operation_id: int, db_manager, include_suggestions: bool = True) -> List[Dict]:
    """Vérifie et génère les alertes pour une opération"""
    
    try:
        # Récupérer les données de l'opération
        operation = db_manager.get_operation_detail(operation_id)
        phases = db_manager.get_phases_by_operation(operation_id)
        
        if not operation or not phases:
            return []
        
        alertes = []
        today = datetime.now().date()
        
        # 1. Alertes de retard sur phases
        phases_retard = detect_delays(phases)
        for phase in phases_retard:
            alertes.append({
                'type_alerte': 'RETARD',
                'niveau_urgence': min(5, max(1, phase['jours_retard'] // 7 + 1)),
                'message': f"Phase '{phase['sous_phase']}' en retard de {phase['jours_retard']} jour(s)",
                'phase_concernee': phase['sous_phase'],
                'couleur': config.TYPES_ALERTES['RETARD']['couleur'],
                'icone': config.TYPES_ALERTES['RETARD']['icone']
            })
        
        # 2. Alertes de blocage actif
        phases_bloquees = [p for p in phases if p.get('blocage_actif', False)]
        for phase in phases_bloquees:
            alertes.append({
                'type_alerte': 'BLOCAGE',
                'niveau_urgence': 5,
                'message': f"Blocage actif sur '{phase['sous_phase']}' - {phase.get('motif_blocage', 'Motif non spécifié')}",
                'phase_concernee': phase['sous_phase'],
                'couleur': config.TYPES_ALERTES['BLOCAGE']['couleur'],
                'icone': config.TYPES_ALERTES['BLOCAGE']['icone']
            })
        
        # 3. Alertes d'échéance proche
        for phase in phases:
            if (not phase.get('est_validee', False) and 
                phase.get('date_fin_prevue')):
                
                try:
                    date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                    jours_restants = (date_fin - today).days
                    
                    if 0 <= jours_restants <= 7:
                        alertes.append({
                            'type_alerte': 'ATTENTION',
                            'niveau_urgence': 3,
                            'message': f"Échéance proche pour '{phase['sous_phase']}' dans {jours_restants} jour(s)",
                            'phase_concernee': phase['sous_phase'],
                            'couleur': config.TYPES_ALERTES['ATTENTION']['couleur'],
                            'icone': config.TYPES_ALERTES['ATTENTION']['icone']
                        })
                except:
                    continue
        
        # 4. Alertes de performance (suggestions)
        if include_suggestions:
            avancement = operation.get('pourcentage_avancement', 0)
            
            if avancement == 0 and operation.get('statut_principal') != '🟡 À l'étude':
                alertes.append({
                    'type_alerte': 'ATTENTION',
                    'niveau_urgence': 2,
                    'message': "Aucune phase validée - Vérifiez l'avancement réel",
                    'phase_concernee': None,
                    'couleur': config.TYPES_ALERTES['ATTENTION']['couleur'],
                    'icone': '📊'
                })
            
            if avancement < 30 and '🚧 En travaux' in operation.get('statut_principal', ''):
                alertes.append({
                    'type_alerte': 'ATTENTION',
                    'niveau_urgence': 3,
                    'message': "Travaux peu avancés par rapport au statut déclaré",
                    'phase_concernee': None,
                    'couleur': config.TYPES_ALERTES['ATTENTION']['couleur'],
                    'icone': '🚧'
                })
        
        # Trier par niveau d'urgence décroissant
        alertes.sort(key=lambda x: x['niveau_urgence'], reverse=True)
        
        return alertes
        
    except Exception as e:
        print(f"❌ Erreur vérification alertes : {e}")
        return []

def calculate_risk_score(operation: Dict, phases: List[Dict], alertes: List[Dict] = None) -> float:
    """Calcule le score de risque d'une opération (utilise config.py)"""
    
    return config.calculate_risk_score(operation, phases, alertes)

def get_top_risk_operations(operations: List[Dict], db_manager, limit: int = 3) -> List[Dict]:
    """Identifie les opérations les plus à risque avec justifications détaillées"""
    
    operations_avec_risque = []
    
    for operation in operations:
        if operation.get('statut_principal') == '✅ Clôturé (soldé)':
            continue
        
        try:
            # Calculer le score de risque
            phases = db_manager.get_phases_by_operation(operation['id'])
            alertes = check_alerts(operation['id'], db_manager, include_suggestions=False)
            
            score_risque = calculate_risk_score(operation, phases, alertes)
            
            # Ajouter les justifications
            justifications = []
            
            if operation.get('has_active_blocage', False):
                justifications.append("🔴 Blocage actif")
            
            phases_retard = detect_delays(phases)
            if phases_retard:
                justifications.append(f"⏰ {len(phases_retard)} phase(s) en retard")
            
            if len(alertes) > 0:
                justifications.append(f"🚨 {len(alertes)} alerte(s)")
            
            avancement = operation.get('pourcentage_avancement', 0)
            if avancement == 0:
                justifications.append("📊 Aucun avancement")
            elif avancement < 30 and '🚧 En travaux' in operation.get('statut_principal', ''):
                justifications.append("🚧 Travaux peu avancés")
            
            if not justifications:
                justifications.append("📈 Risque calculé selon critères")
            
            operation_risk = operation.copy()
            operation_risk['score_risque'] = score_risque
            operation_risk['justifications'] = justifications
            operation_risk['nb_alertes'] = len(alertes)
            operation_risk['nb_phases_retard'] = len(phases_retard)
            
            operations_avec_risque.append(operation_risk)
            
        except Exception as e:
            print(f"⚠️ Erreur calcul risque pour {operation.get('nom', 'N/A')} : {e}")
            continue
    
    # Trier par score de risque décroissant
    operations_avec_risque.sort(key=lambda x: x['score_risque'], reverse=True)
    
    return operations_avec_risque[:limit]

# ============================================================================
# VISUALISATIONS TIMELINE ET FRISES CHRONOLOGIQUES
# ============================================================================

def generate_timeline(operation_id: int, db_manager, type_viz: str = "chronologique") -> str:
    """Génère une timeline colorée et interactive"""
    
    try:
        operation = db_manager.get_operation_detail(operation_id)
        phases = db_manager.get_phases_by_operation(operation_id)
        
        if not phases:
            return "<p>Aucune phase trouvée pour cette opération</p>"
        
        if type_viz == "chronologique":
            return _generate_chronological_timeline(phases, operation)
        elif type_viz == "gantt":
            return _generate_gantt_timeline(phases, operation)
        else:
            return _generate_mental_map(phases, operation)
            
    except Exception as e:
        print(f"❌ Erreur génération timeline : {e}")
        return f"<p>Erreur lors de la génération : {str(e)}</p>"

def _generate_chronological_timeline(phases: List[Dict], operation: Dict) -> str:
    """Génère une frise chronologique horizontale colorée"""
    
    try:
        # Préparer les données pour Plotly
        timeline_data = []
        today = datetime.now().date()
        
        for phase in phases:
            # Déterminer les dates
            date_debut = None
            date_fin = None
            
            if phase.get('date_debut_prevue'):
                try:
                    date_debut = datetime.strptime(phase['date_debut_prevue'], '%Y-%m-%d').date()
                except:
                    pass
            
            if phase.get('date_fin_prevue'):
                try:
                    date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Si pas de dates, estimer
            if not date_debut and not date_fin:
                duree = phase.get('duree_maxi_jours', 30)
                if timeline_data:
                    derniere_fin = timeline_data[-1].get('Finish', today)
                    date_debut = derniere_fin + timedelta(days=1)
                else:
                    date_debut = today
                date_fin = date_debut + timedelta(days=duree)
            elif date_debut and not date_fin:
                duree = phase.get('duree_maxi_jours', 30)
                date_fin = date_debut + timedelta(days=duree)
            elif not date_debut and date_fin:
                duree = phase.get('duree_maxi_jours', 30)
                date_debut = date_fin - timedelta(days=duree)
            
            # Déterminer la couleur selon l'état
            if phase.get('blocage_actif', False):
                couleur = '#dc2626'  # Rouge - Bloqué
                statut_text = "🔴 BLOQUÉ"
            elif phase.get('est_validee', False):
                couleur = '#10b981'  # Vert - Validé
                statut_text = "✅ VALIDÉ"
            elif date_fin and today > date_fin and not phase.get('est_validee', False):
                couleur = '#ef4444'  # Rouge - En retard
                statut_text = "⏰ EN RETARD"
            elif date_fin and (date_fin - today).days <= 7 and not phase.get('est_validee', False):
                couleur = '#f59e0b'  # Orange - Échéance proche
                statut_text = "⚡ URGENT"
            else:
                couleur = '#6b7280'  # Gris - En attente
                statut_text = "⏳ EN ATTENTE"
            
            timeline_data.append({
                'Task': f"{phase.get('sous_phase', 'Phase')}",
                'Start': date_debut,
                'Finish': date_fin,
                'Resource': phase.get('responsable_principal', 'Non défini'),
                'Statut': statut_text,
                'Description': f"{phase.get('phase_principale', '')} - {phase.get('responsable_principal', '')}",
                'Couleur': couleur
            })
        
        # Créer le graphique Plotly
        if not timeline_data:
            return "<p>Impossible de générer la timeline</p>"
        
        df = pd.DataFrame(timeline_data)
        
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Statut",
            title=f"📅 Timeline - {operation.get('nom', 'Opération')}",
            hover_data=["Resource", "Description"],
            color_discrete_map={
                "🔴 BLOQUÉ": "#dc2626",
                "✅ VALIDÉ": "#10b981", 
                "⏰ EN RETARD": "#ef4444",
                "⚡ URGENT": "#f59e0b",
                "⏳ EN ATTENTE": "#6b7280"
            }
        )
        
        # Personnaliser l'affichage
        fig.update_layout(
            height=max(400, len(timeline_data) * 25),
            xaxis_title="Période",
            yaxis_title="Phases",
            font=dict(size=10),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(autorange="reversed")
        
        # Ajouter une ligne verticale pour aujourd'hui
        fig.add_vline(
            x=today,
            line_dash="dash",
            line_color="red",
            annotation_text="Aujourd'hui",
            annotation_position="top"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id=f"timeline_{operation_id}")
        
    except Exception as e:
        print(f"❌ Erreur timeline chronologique : {e}")
        return f"<p>Erreur génération timeline : {str(e)}</p>"

def _generate_gantt_timeline(phases: List[Dict], operation: Dict) -> str:
    """Génère un diagramme de Gantt interactif"""
    
    try:
        # Données similaires à la timeline chronologique mais avec plus de détails
        gantt_data = []
        today = datetime.now().date()
        
        for phase in phases:
            date_debut = today
            date_fin = today + timedelta(days=phase.get('duree_maxi_jours', 30))
            
            # Utiliser les vraies dates si disponibles
            if phase.get('date_debut_prevue'):
                try:
                    date_debut = datetime.strptime(phase['date_debut_prevue'], '%Y-%m-%d').date()
                except:
                    pass
            
            if phase.get('date_fin_prevue'):
                try:
                    date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                except:
                    pass
            
            # Calcul du pourcentage de completion
            if phase.get('est_validee', False):
                completion = 100
            elif date_debut <= today <= date_fin:
                total_days = (date_fin - date_debut).days
                elapsed_days = (today - date_debut).days
                completion = min(100, max(0, (elapsed_days / total_days) * 100)) if total_days > 0 else 0
            else:
                completion = 0
            
            gantt_data.append({
                'Task': phase.get('sous_phase', 'Phase'),
                'Start': date_debut,
                'Finish': date_fin,
                'Completion': completion,
                'Resource': phase.get('responsable_principal', 'Non défini'),
                'Phase_Principale': phase.get('phase_principale', ''),
                'Duree_Prevue': (date_fin - date_debut).days,
                'Statut': "Validé" if phase.get('est_validee', False) else "En cours"
            })
        
        df = pd.DataFrame(gantt_data)
        
        # Créer le Gantt avec Plotly
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Completion",
            title=f"📊 Diagramme de Gantt - {operation.get('nom', 'Opération')}",
            hover_data=["Resource", "Duree_Prevue", "Statut"],
            color_continuous_scale="RdYlGn"
        )
        
        fig.update_layout(
            height=max(500, len(gantt_data) * 30),
            xaxis_title="Période",
            yaxis_title="Phases",
            coloraxis_colorbar=dict(title="% Avancement")
        )
        
        fig.update_yaxes(autorange="reversed")
        
        # Ligne aujourd'hui
        fig.add_vline(x=today, line_dash="dash", line_color="red", annotation_text="Aujourd'hui")
        
        return fig.to_html(include_plotlyjs='cdn', div_id=f"gantt_{operation['id']}")
        
    except Exception as e:
        print(f"❌ Erreur Gantt : {e}")
        return f"<p>Erreur génération Gantt : {str(e)}</p>"

def _generate_mental_map(phases: List[Dict], operation: Dict) -> str:
    """Génère une carte mentale interactive avec PyVis"""
    
    try:
        # Regrouper par phase principale
        phases_groupees = {}
        for phase in phases:
            phase_principale = phase.get('phase_principale', 'Autres')
            if phase_principale not in phases_groupees:
                phases_groupees[phase_principale] = []
            phases_groupees[phase_principale].append(phase)
        
        # Générer HTML de carte mentale simplifiée mais colorée
        html_content = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3 style="text-align: center; margin-bottom: 20px;">🧠 Carte Mentale - {operation.get('nom', 'Opération')}</h3>
            <div style="display: grid; gap: 15px;">
        """
        
        for phase_principale, sous_phases in phases_groupees.items():
            phases_validees = sum(1 for p in sous_phases if p.get('est_validee', False))
            total_phases = len(sous_phases)
            pourcentage = (phases_validees / total_phases) * 100 if total_phases > 0 else 0
            
            # Couleur selon avancement
            if pourcentage == 100:
                couleur_fond = "#10b981"  # Vert
                icone = "✅"
            elif pourcentage >= 50:
                couleur_fond = "#f59e0b"  # Orange
                icone = "⚡"
            elif pourcentage > 0:
                couleur_fond = "#3b82f6"  # Bleu
                icone = "🔄"
            else:
                couleur_fond = "#6b7280"  # Gris
                icone = "⏳"
            
            html_content += f"""
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {couleur_fond};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: white;">{icone} {phase_principale}</h4>
                    <span style="background: {couleur_fond}; padding: 5px 10px; border-radius: 15px; font-weight: bold;">
                        {phases_validees}/{total_phases} ({pourcentage:.0f}%)
                    </span>
                </div>
                <div style="display: grid; gap: 8px; margin-left: 15px;">
            """
            
            for sous_phase in sous_phases:
                if sous_phase.get('blocage_actif', False):
                    statut_icone = "🔴"
                    statut_couleur = "#ef4444"
                elif sous_phase.get('est_validee', False):
                    statut_icone = "✅"
                    statut_couleur = "#10b981"
                else:
                    statut_icone = "⏳"
                    statut_couleur = "#6b7280"
                
                html_content += f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 5px;">
                    <span style="color: {statut_couleur}; font-size: 14px;">{statut_icone}</span>
                    <span style="color: rgba(255,255,255,0.9);">{sous_phase.get('sous_phase', 'Phase')}</span>
                </div>
                """
            
            html_content += "</div></div>"
        
        html_content += """
            </div>
        </div>
        """
        
        return html_content
        
    except Exception as e:
        print(f"❌ Erreur carte mentale : {e}")
        return f"<p>Erreur génération carte mentale : {str(e)}</p>"

def create_mental_map(phases: List[Dict], operation: Dict = None) -> str:
    """Fonction publique pour créer une carte mentale"""
    return _generate_mental_map(phases, operation or {})

# ============================================================================
# GRAPHIQUES ET KPI POUR MANAGER
# ============================================================================

def generate_kpi_charts(kpi_data: Dict) -> Dict[str, str]:
    """Génère les graphiques KPI pour la vue Manager"""
    
    charts = {}
    
    try:
        # 1. Graphique répartition statuts
        if 'repartition_statuts' in kpi_data and kpi_data['repartition_statuts']:
            statuts = list(kpi_data['repartition_statuts'].keys())
            valeurs = list(kpi_data['repartition_statuts'].values())
            
            # Couleurs selon les statuts
            couleurs = []
            for statut in statuts:
                couleurs.append(config.STATUTS_GLOBAUX.get(statut, {}).get('couleur', '#6b7280'))
            
            fig_statuts = px.pie(
                values=valeurs,
                names=statuts,
                title="📊 Répartition par Statut",
                color_discrete_sequence=couleurs
            )
            
            fig_statuts.update_traces(textposition='inside', textinfo='percent+label')
            fig_statuts.update_layout(
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5),
                height=400
            )
            
            charts['statuts'] = fig_statuts.to_html(include_plotlyjs=False, div_id="chart_statuts")
        
        # 2. Graphique répartition types
        if 'repartition_types' in kpi_data and kpi_data['repartition_types']:
            types = list(kpi_data['repartition_types'].keys())
            valeurs = list(kpi_data['repartition_types'].values())
            
            fig_types = px.bar(
                x=types,
                y=valeurs,
                title="📈 Opérations par Type",
                color=types,
                color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
            )
            
            fig_types.update_layout(
                xaxis_title="Type d'opération",
                yaxis_title="Nombre",
                showlegend=False,
                height=400
            )
            
            charts['types'] = fig_types.to_html(include_plotlyjs=False, div_id="chart_types")
        
        # 3. Graphique avancement global (jauge)
        if 'avancement_moyen' in kpi_data:
            avancement = kpi_data['avancement_moyen']
            
            fig_avancement = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = avancement,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "📊 Avancement Moyen"},
                delta = {'reference': 50, 'position': "top"},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "darkblue"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 25], 'color': '#ef4444'},
                        {'range': [25, 50], 'color': '#f59e0b'},
                        {'range': [50, 75], 'color': '#3b82f6'},
                        {'range': [75, 100], 'color': '#10b981'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_avancement.update_layout(height=400)
            charts['avancement'] = fig_avancement.to_html(include_plotlyjs=False, div_id="chart_avancement")
        
        return charts
        
    except Exception as e:
        print(f"❌ Erreur génération graphiques KPI : {e}")
        return {}

def create_risk_analysis_chart(operations_risk: List[Dict]) -> str:
    """Crée un graphique d'analyse des risques"""
    
    try:
        if not operations_risk:
            return "<p>Aucune donnée de risque disponible</p>"
        
        # Préparer les données
        noms = [op.get('nom', 'N/A')[:20] + '...' if len(op.get('nom', '')) > 20 else op.get('nom', 'N/A') for op in operations_risk]
        scores = [op.get('score_risque', 0) for op in operations_risk]
        statuts = [op.get('statut_principal', '') for op in operations_risk]
        
                # Couleurs selon le niveau de risque
        couleurs = []
        for score in scores:
            if score >= 80:
                couleurs.append('#dc2626')  # Rouge - Risque très élevé
            elif score >= 60:
                couleurs.append('#f59e0b')  # Orange - Risque élevé
            elif score >= 40:
                couleurs.append('#3b82f6')  # Bleu - Risque modéré
            else:
                couleurs.append('#10b981')  # Vert - Risque faible
        
        fig = px.bar(
            x=noms,
            y=scores,
            title="🚨 Analyse des Risques par Opération",
            labels={'x': 'Opérations', 'y': 'Score de Risque'},
            color=scores,
            color_continuous_scale=['#10b981', '#3b82f6', '#f59e0b', '#dc2626'],
            text=scores
        )
        
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig.update_layout(
            xaxis_title="Opérations",
            yaxis_title="Score de Risque (0-100)",
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        
        # Ligne de seuil critique
        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                      annotation_text="Seuil critique", annotation_position="bottom right")
        
        return fig.to_html(include_plotlyjs=False, div_id="chart_risk_analysis")
        
    except Exception as e:
        print(f"❌ Erreur graphique analyse risques : {e}")
        return f"<p>Erreur génération graphique : {str(e)}</p>"

def create_progress_distribution_chart(operations: List[Dict]) -> str:
    """Crée un histogramme de distribution des avancements"""
    
    try:
        if not operations:
            return "<p>Aucune donnée d'avancement disponible</p>"
        
        # Préparer les données d'avancement
        avancements = [op.get('pourcentage_avancement', 0) for op in operations]
        
        # Créer des bins pour l'histogramme
        bins = [0, 20, 40, 60, 80, 100]
        labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        
        # Compter les opérations par tranche
        counts = []
        for i in range(len(bins)-1):
            count = sum(1 for av in avancements if bins[i] <= av < bins[i+1])
            counts.append(count)
        
        # Traiter le cas 100% séparément
        counts[-1] += sum(1 for av in avancements if av == 100)
        
        fig = px.bar(
            x=labels,
            y=counts,
            title="📊 Distribution des Avancements",
            labels={'x': 'Tranches d\'avancement', 'y': 'Nombre d\'opérations'},
            color=counts,
            color_continuous_scale='Viridis',
            text=counts
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(
            xaxis_title="Avancement (%)",
            yaxis_title="Nombre d'opérations",
            height=400,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="chart_progress_distribution")
        
    except Exception as e:
        print(f"❌ Erreur graphique distribution : {e}")
        return f"<p>Erreur génération graphique : {str(e)}</p>"

# ============================================================================
# FORMATAGE ET UTILITAIRES GÉNÉRAUX
# ============================================================================

def format_currency(montant: float, devise: str = "€") -> str:
    """Formate un montant en devise avec séparateurs"""
    
    try:
        if montant == 0:
            return f"0 {devise}"
        
        # Formatage français avec espaces comme séparateurs de milliers
        montant_formate = f"{montant:,.2f}".replace(",", " ").replace(".", ",")
        
        # Supprimer les décimales si montant entier
        if montant == int(montant):
            montant_formate = f"{int(montant):,}".replace(",", " ")
        
        return f"{montant_formate} {devise}"
        
    except:
        return f"{montant} {devise}"

def format_date_fr(date_str: str, format_sortie: str = "long") -> str:
    """Formate une date en français"""
    
    if not date_str:
        return "Date non définie"
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_obj = date_str
        
        mois_fr = [
            "", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"
        ]
        
        if format_sortie == "long":
            return f"{date_obj.day} {mois_fr[date_obj.month]} {date_obj.year}"
        else:
            return f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
            
    except Exception as e:
        print(f"⚠️ Erreur formatage date {date_str} : {e}")
        return str(date_str)

def calculate_duration_working_days(date_debut: str, date_fin: str) -> int:
    """Calcule la durée en jours ouvrés entre deux dates"""
    
    try:
        if not date_debut or not date_fin:
            return 0
        
        debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
        
        if fin < debut:
            return 0
        
        # Calcul simple sans jours fériés (peut être amélioré)
        total_days = (fin - debut).days
        
        # Approximation : retirer ~22% pour weekends (5/7 jours ouvrés)
        working_days = int(total_days * 5/7)
        
        return working_days
        
    except Exception as e:
        print(f"⚠️ Erreur calcul durée : {e}")
        return 0

def estimate_completion_date(phases: List[Dict], current_date: date = None) -> Optional[date]:
    """Estime la date de fin d'opération basée sur les phases restantes"""
    
    try:
        if not phases:
            return None
        
        if current_date is None:
            current_date = datetime.now().date()
        
        # Trouver la dernière phase non validée
        phases_restantes = [p for p in phases if not p.get('est_validee', False)]
        
        if not phases_restantes:
            # Toutes les phases sont validées
            return current_date
        
        # Prendre la date de fin prévue la plus tardive
        dates_fin = []
        
        for phase in phases_restantes:
            if phase.get('date_fin_prevue'):
                try:
                    date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                    dates_fin.append(date_fin)
                except:
                    continue
        
        if dates_fin:
            return max(dates_fin)
        
        # Si pas de dates, estimer basé sur les durées
        duree_restante = sum(phase.get('duree_maxi_jours', 30) for phase in phases_restantes)
        return current_date + timedelta(days=duree_restante)
        
    except Exception as e:
        print(f"⚠️ Erreur estimation date fin : {e}")
        return None

def get_phase_icon(phase: Dict) -> str:
    """Retourne l'icône appropriée pour une phase"""
    
    try:
        # Icônes selon l'état
        if phase.get('blocage_actif', False):
            return "🔴"
        elif phase.get('est_validee', False):
            return "✅"
        
        # Icônes selon le type de phase
        phase_nom = phase.get('sous_phase', '').lower()
        
        if any(word in phase_nom for word in ['montage', 'opportunité']):
            return "🎯"
        elif any(word in phase_nom for word in ['études', 'esq', 'aps', 'apd', 'pro']):
            return "📐"
        elif any(word in phase_nom for word in ['autorisation', 'pc', 'permis']):
            return "📋"
        elif any(word in phase_nom for word in ['financement', 'prêt', 'cdc']):
            return "💰"
        elif any(word in phase_nom for word in ['consultation', 'cao', 'offres']):
            return "📢"
        elif any(word in phase_nom for word in ['attribution', 'marché', 'signature']):
            return "✍️"
        elif any(word in phase_nom for word in ['travaux', 'chantier', 'construction']):
            return "🚧"
        elif any(word in phase_nom for word in ['réception', 'livraison']):
            return "🎁"
        elif any(word in phase_nom for word in ['gpa', 'garantie']):
            return "🛡️"
        elif any(word in phase_nom for word in ['clôture', 'solde', 'archivage']):
            return "📁"
        else:
            return "📌"
            
    except Exception as e:
        print(f"⚠️ Erreur icône phase : {e}")
        return "📌"

def generate_operation_summary(operation: Dict, phases: List[Dict], alertes: List[Dict] = None) -> Dict:
    """Génère un résumé complet d'une opération"""
    
    try:
        summary = {
            'nom': operation.get('nom', 'N/A'),
            'type_operation': operation.get('type_operation', 'N/A'),
            'statut_principal': operation.get('statut_principal', 'N/A'),
            'responsable_aco': operation.get('responsable_aco', 'N/A'),
            'avancement': operation.get('pourcentage_avancement', 0),
        }
        
        # Analyse des phases
        if phases:
            total_phases = len(phases)
            phases_validees = sum(1 for p in phases if p.get('est_validee', False))
            phases_bloquees = sum(1 for p in phases if p.get('blocage_actif', False))
            phases_retard = len(detect_delays(phases))
            
            summary.update({
                'total_phases': total_phases,
                'phases_validees': phases_validees,
                'phases_bloquees': phases_bloquees,
                'phases_en_retard': phases_retard,
                'phase_actuelle': get_current_phase(phases).get('sous_phase', 'N/A'),
                'prochaines_phases': [p.get('sous_phase', 'N/A') for p in get_next_phases(phases, 2)]
            })
            
            # Estimation date de fin
            date_fin_estimee = estimate_completion_date(phases)
            if date_fin_estimee:
                summary['date_fin_estimee'] = format_date_fr(date_fin_estimee.isoformat())
        
        # Analyse des alertes
        if alertes:
            alertes_par_niveau = {}
            for alerte in alertes:
                niveau = alerte.get('niveau_urgence', 1)
                alertes_par_niveau[niveau] = alertes_par_niveau.get(niveau, 0) + 1
            
            summary.update({
                'total_alertes': len(alertes),
                'alertes_par_niveau': alertes_par_niveau,
                'alerte_max_urgence': max([a.get('niveau_urgence', 1) for a in alertes]) if alertes else 0
            })
        
        # Score de risque
        summary['score_risque'] = calculate_risk_score(operation, phases, alertes)
        
        return summary
        
    except Exception as e:
        print(f"❌ Erreur génération résumé : {e}")
        return {'erreur': str(e)}

def export_to_excel(operations: List[Dict], phases_data: Dict = None, filename: str = None) -> str:
    """Exporte les données vers Excel (retourne le chemin du fichier)"""
    
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        if filename is None:
            filename = f"export_spic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = openpyxl.Workbook()
        
        # Feuille 1 : Vue d'ensemble des opérations
        ws1 = wb.active
        ws1.title = "Vue d'ensemble"
        
        if operations:
            df_operations = pd.DataFrame(operations)
            
            # Colonnes à inclure
            colonnes_export = [
                'nom', 'type_operation', 'statut_principal', 'responsable_aco',
                'commune', 'pourcentage_avancement', 'date_creation', 'score_risque'
            ]
            
            colonnes_presentes = [col for col in colonnes_export if col in df_operations.columns]
            df_export = df_operations[colonnes_presentes]
            
            # Renommer les colonnes en français
            renommage = {
                'nom': 'Nom de l\'opération',
                'type_operation': 'Type',
                'statut_principal': 'Statut',
                'responsable_aco': 'Responsable ACO',
                'commune': 'Commune',
                'pourcentage_avancement': 'Avancement (%)',
                'date_creation': 'Date de création',
                'score_risque': 'Score de risque'
            }
            
            df_export = df_export.rename(columns=renommage)
            
            # Écrire dans Excel
            for r in dataframe_to_rows(df_export, index=False, header=True):
                ws1.append(r)
            
            # Mise en forme
            for col in ws1.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws1.column_dimensions[column].width = adjusted_width
            
            # En-tête en gras
            for cell in ws1[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Feuille 2 : Statistiques
        ws2 = wb.create_sheet("Statistiques")
        
        if operations:
            # Statistiques par statut
            statuts = {}
            for op in operations:
                statut = op.get('statut_principal', 'Non défini')
                statuts[statut] = statuts.get(statut, 0) + 1
            
            ws2.append(['Répartition par statut', ''])
            ws2.append(['Statut', 'Nombre'])
            for statut, count in statuts.items():
                ws2.append([statut, count])
            
            ws2.append(['', ''])  # Ligne vide
            
            # Statistiques par type
            types = {}
            for op in operations:
                type_op = op.get('type_operation', 'Non défini')
                types[type_op] = types.get(type_op, 0) + 1
            
            ws2.append(['Répartition par type', ''])
            ws2.append(['Type', 'Nombre'])
            for type_op, count in types.items():
                ws2.append([type_op, count])
        
        # Sauvegarder
        wb.save(filename)
        print(f"✅ Export Excel créé : {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Erreur export Excel : {e}")
        return ""

def validate_phase_data(phase: Dict) -> List[str]:
    """Valide les données d'une phase et retourne les erreurs"""
    
    erreurs = []
    
    try:
        # Vérifications obligatoires
        if not phase.get('sous_phase'):
            erreurs.append("Le nom de la sous-phase est obligatoire")
        
        if not phase.get('phase_principale'):
            erreurs.append("La phase principale est obligatoire")
        
        # Vérifications des dates
        date_debut = phase.get('date_debut_prevue')
        date_fin = phase.get('date_fin_prevue')
        
        if date_debut and date_fin:
            try:
                debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
                fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
                
                if fin < debut:
                    erreurs.append("La date de fin ne peut pas être antérieure à la date de début")
                    
                if (fin - debut).days > 365:
                    erreurs.append("La durée de la phase semble excessive (> 1 an)")
                    
            except ValueError:
                erreurs.append("Format de date invalide (attendu: YYYY-MM-DD)")
        
        # Vérifications des durées
        duree_mini = phase.get('duree_mini_jours')
        duree_maxi = phase.get('duree_maxi_jours')
        
        if duree_mini and duree_maxi:
            if duree_mini > duree_maxi:
                erreurs.append("La durée minimale ne peut pas être supérieure à la durée maximale")
            
            if duree_maxi > 730:  # 2 ans
                erreurs.append("La durée maximale semble excessive (> 2 ans)")
        
        return erreurs
        
    except Exception as e:
        return [f"Erreur de validation : {str(e)}"]

# ============================================================================
# FONCTIONS SPÉCIALES POUR LA VUE CHARGÉ
# ============================================================================

def get_weekly_focus_tasks(operations: List[Dict], db_manager) -> List[Dict]:
    """Récupère les tâches prioritaires de la semaine pour un chargé d'opération"""
    
    try:
        taches_prioritaires = []
        today = datetime.now().date()
        fin_semaine = today + timedelta(days=7)
        
        for operation in operations:
            # Récupérer les phases de l'opération
            phases = db_manager.get_phases_by_operation(operation['id'])
            
            # Phases à échéance cette semaine
            for phase in phases:
                if (not phase.get('est_validee', False) and 
                    phase.get('date_fin_prevue')):
                    
                    try:
                        date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                        
                        if today <= date_fin <= fin_semaine:
                            taches_prioritaires.append({
                                'operation_nom': operation.get('nom', 'N/A'),
                                'operation_id': operation.get('id'),
                                'phase_nom': phase.get('sous_phase', 'N/A'),
                                'date_echeance': date_fin,
                                'jours_restants': (date_fin - today).days,
                                'priorite': 'URGENT' if (date_fin - today).days <= 2 else 'IMPORTANT',
                                'responsable': phase.get('responsable_principal', 'Non défini'),
                                'icone': get_phase_icon(phase)
                            })
                    except:
                        continue
            
            # Phases bloquées (priorité absolue)
            phases_bloquees = [p for p in phases if p.get('blocage_actif', False)]
            for phase in phases_bloquees:
                taches_prioritaires.append({
                    'operation_nom': operation.get('nom', 'N/A'),
                    'operation_id': operation.get('id'),
                    'phase_nom': phase.get('sous_phase', 'N/A'),
                    'date_echeance': today,
                    'jours_restants': 0,
                    'priorite': 'BLOQUÉ',
                    'responsable': phase.get('responsable_principal', 'Non défini'),
                    'icone': '🔴',
                    'motif_blocage': phase.get('motif_blocage', 'Non spécifié')
                })
        
        # Trier par priorité puis par échéance
        ordre_priorite = {'BLOQUÉ': 0, 'URGENT': 1, 'IMPORTANT': 2}
        taches_prioritaires.sort(key=lambda x: (ordre_priorite.get(x['priorite'], 3), x['jours_restants']))
        
        return taches_prioritaires[:10]  # Top 10
        
    except Exception as e:
        print(f"❌ Erreur récupération tâches semaine : {e}")
        return []

def generate_aco_performance_summary(aco_nom: str, operations: List[Dict], db_manager) -> Dict:
    """Génère un résumé de performance pour un ACO"""
    
    try:
        if not operations:
            return {'erreur': 'Aucune opération trouvée'}
        
        # Statistiques de base
        total_operations = len(operations)
        operations_actives = len([op for op in operations if op.get('statut_principal') != '✅ Clôturé (soldé)'])
        
        # Avancement moyen
        avancements = [op.get('pourcentage_avancement', 0) for op in operations]
        avancement_moyen = sum(avancements) / len(avancements) if avancements else 0
        
        # Répartition par statut
        statuts = {}
        for op in operations:
            statut = op.get('statut_principal', 'Non défini')
            statuts[statut] = statuts.get(statut, 0) + 1
        
        # Opérations à risque
        operations_a_risque = []
        total_alertes = 0
        
        for operation in operations:
            if operation.get('statut_principal') == '✅ Clôturé (soldé)':
                continue
                
            alertes = check_alerts(operation['id'], db_manager, include_suggestions=False)
            total_alertes += len(alertes)
            
            if (operation.get('has_active_blocage', False) or 
                len(alertes) > 0 or 
                operation.get('score_risque', 0) > 50):
                operations_a_risque.append(operation.get('nom', 'N/A'))
        
        # Tendance (simulation - peut être améliorée avec historique)
        operations_en_avancement = len([op for op in operations if op.get('pourcentage_avancement', 0) > 30])
        tendance = "positive" if operations_en_avancement > total_operations * 0.6 else "neutre"
        
        return {
            'aco_nom': aco_nom,
            'total_operations': total_operations,
            'operations_actives': operations_actives,
            'avancement_moyen': round(avancement_moyen, 1),
            'repartition_statuts': statuts,
            'operations_a_risque': operations_a_risque,
            'nb_operations_a_risque': len(operations_a_risque),
            'total_alertes': total_alertes,
            'tendance': tendance,
            'date_maj': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
    except Exception as e:
        print(f"❌ Erreur résumé performance ACO : {e}")
        return {'erreur': str(e)}

# ============================================================================
# FONCTIONS DE TEST ET VALIDATION
# ============================================================================

def validate_utils_functions() -> bool:
    """Valide le bon fonctionnement des fonctions utilitaires"""
    
    try:
        print("🧪 Validation des fonctions utilitaires...")
        
        # Test formatage devise
        assert format_currency(1234.56) == "1 234,56 €"
        assert format_currency(1000000) == "1 000 000 €"
        print("✅ Formatage devise OK")
        
        # Test formatage date
        assert format_date_fr("2024-03-15") == "15 mars 2024"
        print("✅ Formatage date OK")
        
        # Test calcul avancement
        phases_test = [
            {'est_validee': True},
            {'est_validee': True},
            {'est_validee': False},
            {'est_validee': False}
        ]
        assert calculate_progress(phases_test) == 50.0
        print("✅ Calcul avancement OK")
        
        # Test icônes phases
        phase_test = {'sous_phase': 'travaux fondations'}
        assert get_phase_icon(phase_test) == "🚧"
        print("✅ Icônes phases OK")
        
        print("✅ Validation complète des utils terminée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur validation utils : {e}")
        return False

# Test des fonctions si le module est exécuté directement
if __name__ == "__main__":
    print("🧪 Test du module utils SPIC 2.0")
    
    # Validation des fonctions
    validation_ok = validate_utils_functions()
    
    if validation_ok:
        print("✅ Module utils SPIC 2.0 opérationnel")
    else:
        print("❌ Erreurs détectées dans le module utils")
    
    # Test de génération de timeline simple
    phases_demo = [
        {
            'sous_phase': 'Montage projet',
            'est_validee': True,
            'couleur_statut': '🟢'
        },
        {
            'sous_phase': 'Études techniques',
            'est_validee': False,
            'couleur_statut': '🟡'
        }
    ]
    
    print(f"📊 Phases démo préparées : {len(phases_demo)} phases")
    print("📈 Module prêt pour intégration avec database.py et app.py")