# -*- coding: utf-8 -*-
"""
Configuration centralisée pour l'application SPIC
Gestion des opérations immobilières (OPP, VEFA, AMO, MANDAT)
"""

from typing import Dict, List, Any
import datetime

# ============================================================================
# TYPES D'OPÉRATIONS
# ============================================================================

TYPES_OPERATIONS = [
    "OPP",      # Opérations Propres
    "VEFA",     # Vente en État Futur d'Achèvement
    "AMO",      # Assistance à Maîtrise d'Ouvrage
    "MANDAT"    # Opérations en Mandat
]

# ============================================================================
# STATUTS GLOBAUX DYNAMIQUES
# ============================================================================

STATUTS_GLOBAUX = {
    "🟡 À l'étude": {
        "couleur": "#fbbf24",
        "description": "Montage, programmation, études",
        "phases_concernees": ["MONTAGE", "ÉTUDES", "AUTORISATIONS", "FINANCEMENT"]
    },
    "🛠️ En consultation": {
        "couleur": "#f97316",
        "description": "Lancement consultation, relances, CAO",
        "phases_concernees": ["CONSULTATION"]
    },
    "📋 Marché attribué": {
        "couleur": "#3b82f6",
        "description": "Attribution, OS, signature marché",
        "phases_concernees": ["ATTRIBUTION"]
    },
    "🚧 En travaux": {
        "couleur": "#8b5cf6",
        "description": "Suivi chantier, réunions, alertes",
        "phases_concernees": ["TRAVAUX", "SUIVI_CHANTIER"]
    },
    "📦 Livré (non soldé)": {
        "couleur": "#06b6d4",
        "description": "GPA, DOE, levées réserves",
        "phases_concernees": ["RÉCEPTION", "LIVRAISON"]
    },
    "📄 En GPA": {
        "couleur": "#10b981",
        "description": "Suivi GPA, relances entreprise",
        "phases_concernees": ["GPA"]
    },
    "✅ Clôturé (soldé)": {
        "couleur": "#22c55e",
        "description": "Clôture technique + financière",
        "phases_concernees": ["CLÔTURE"]
    },
    "🔴 Bloqué": {
        "couleur": "#ef4444",
        "description": "Blocage temporaire",
        "phases_concernees": ["*"]  # Peut s'appliquer à toute phase
    }
}

# ============================================================================
# INTERVENANTS PAR RÔLE
# ============================================================================

INTERVENANTS = {
    "ACO": [
        "MSL", "MARIO M", "MARLENE SL", "AA", "IF", 
        "WR", "DM", "Merezia CALVADOS", "MORINO ROS"
    ],
    "Assistantes": [
        "NA", "LU", "MCC"
    ],
    "Gestionnaire_Marches": [
        "PF", "CSA", "Néant"
    ],
    "Architectes": [
        "FOMI", "MPH", "MAGMA", "HALLEY", 
        "COLORADO", "D. FRAIR", "THEOPHILE", "HIRTH",
        "L. MARTZ", "V. BIGEARD", "H. ROSTAL", "F. SAINT MARTIN",
        "CHARRIER", "à désigner"
    ],
    "Promoteurs": [
        "SEMAG", "LARIFLA", "GADDARKHAN", "SODIM",
        "BRIZZARD", "HELISSEY"
    ]
}

# ============================================================================
# RÉFÉRENTIELS PHASES PAR TYPE D'OPÉRATION
# ============================================================================

REFERENTIELS_PHASES = {
    "OPP": [
        {
            "phase_principale": "1. MONTAGE",
            "sous_phase": "1.1 Opportunité repérée",
            "ordre": 1,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "ACO",
            "responsable_validation": "Direction SPIC",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pas validé après 2 semaines"
        },
        {
            "phase_principale": "1. MONTAGE",
            "sous_phase": "1.2 Programmation",
            "ordre": 2,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 42,
            "responsable_principal": "ACO + Programmiste",
            "responsable_validation": "ACO + Direction",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pas validé après 4 semaines"
        },
        # ... Continuer avec toutes les phases OPP
    ],
    
    "VEFA": [
        {
            "phase_principale": "1. PROSPECTION",
            "sous_phase": "1.1 Identification promoteur",
            "ordre": 1,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 56,
            "responsable_principal": "ACO",
            "responsable_validation": "ACO",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pas de contact après 4 semaines"
        },
        # ... Continuer avec toutes les phases VEFA
    ],
    
    "AMO": [
        {
            "phase_principale": "1. ASSISTANCE ÉTUDES",
            "sous_phase": "1.1 Analyse besoin MOA",
            "ordre": 1,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si analyse pas finalisée + 2 semaines"
        },
        # ... Continuer avec toutes les phases AMO
    ],
    
    "MANDAT": [
        {
            "phase_principale": "1. CONVENTION MANDAT",
            "sous_phase": "1.1 Négociation convention",
            "ordre": 1,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si négociation bloquée + 4 semaines"
        },
        # ... Continuer avec toutes les phases MANDAT
    ]
}

# ============================================================================
# STATUTS VALIDES PAR TYPE D'OPÉRATION
# ============================================================================

STATUTS_PAR_TYPE = {
    "OPP": [
        "🟡 À l'étude", "🛠️ En consultation", "📋 Marché attribué",
        "🚧 En travaux", "📦 Livré (non soldé)", "📄 En GPA",
        "✅ Clôturé (soldé)", "🔴 Bloqué"
    ],
    "VEFA": [
        "🟡 À l'étude", "🚧 Travaux promoteur", "📦 Livré (non soldé)",
        "✅ Clôturé (soldé)", "🔴 Bloqué"
    ],
    "AMO": [
        "🟡 À l'étude", "🛠️ En consultation", "📋 Marché attribué",
        "🚧 En travaux", "📦 Livré (non soldé)", "📄 En GPA",
        "✅ Clôturé (soldé)", "🔴 Bloqué"
    ],
    "MANDAT": [
        "🟡 À l'étude", "🛠️ En consultation", "📋 Marché attribué",
        "🚧 En travaux", "📦 Livré (non soldé)",
        "✅ Clôturé (soldé)", "🔴 Bloqué"
    ]
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_phases_for_type(type_operation: str) -> List[Dict]:
    """Récupère les phases pour un type d'opération donné"""
    return REFERENTIELS_PHASES.get(type_operation, [])

def get_statuts_valides(type_operation: str) -> List[str]:
    """Récupère les statuts valides pour un type d'opération"""
    return STATUTS_PAR_TYPE.get(type_operation, list(STATUTS_GLOBAUX.keys()))

def validate_config() -> bool:
    """Valide la cohérence de la configuration"""
    try:
        # Vérifier que tous les types ont des phases
        for type_op in TYPES_OPERATIONS:
            if type_op not in REFERENTIELS_PHASES:
                return False
                
        # Vérifier la cohérence des statuts
        for type_op, statuts in STATUTS_PAR_TYPE.items():
            for statut in statuts:
                if statut not in STATUTS_GLOBAUX:
                    return False
                    
        return True
    except Exception:
        return False

# ============================================================================
# PARAMÈTRES APPLICATION
# ============================================================================

APP_CONFIG = {
    "app_title": "SPIC - Suivi Opérations Immobilières",
    "app_icon": "🏗️",
    "version": "1.0.0",
    "db_path": "spic_operations.db",
    "max_file_size_mb": 10,
    "date_format": "%d/%m/%Y",
    "datetime_format": "%d/%m/%Y %H:%M",
    "currency_symbol": "€",
    "default_timeout_days": 30
}

# Validation de la configuration au chargement
if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration valide")
    else:
        print("❌ Erreur dans la configuration")