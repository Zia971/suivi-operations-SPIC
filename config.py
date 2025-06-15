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
# RÉFÉRENTIELS PHASES COMPLETS PAR TYPE D'OPÉRATION
# ============================================================================

REFERENTIELS_PHASES = {
    "OPP": [
        # ======================= PHASE 1 : MONTAGE =======================
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
            "sous_phase": "1.2 Programmation validée",
            "ordre": 2,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 42,
            "responsable_principal": "ACO + Programmiste",
            "responsable_validation": "ACO + Direction",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pas validé après 4 semaines"
        },
        {
            "phase_principale": "1. MONTAGE",
            "sous_phase": "1.3 Foncier acquis/réservé",
            "ordre": 3,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 180,
            "responsable_principal": "ACO + Service Foncier",
            "responsable_validation": "Direction SPIC",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si négociation bloquée + 8 semaines"
        },
        
        # ======================= PHASE 2 : ÉTUDES =======================
        {
            "phase_principale": "2. ÉTUDES",
            "sous_phase": "2.1 ESQ - Esquisse",
            "ordre": 4,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 42,
            "responsable_principal": "Architecte",
            "responsable_validation": "ACO + MOA",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pas de livraison après 4 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES",
            "sous_phase": "2.2 APS - Avant-Projet Sommaire",
            "ordre": 5,
            "duree_mini_jours": 28,
            "duree_maxi_jours": 56,
            "responsable_principal": "Architecte + BET",
            "responsable_validation": "ACO + Direction",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si retard sur planning + 6 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES",
            "sous_phase": "2.3 APD - Avant-Projet Détaillé",
            "ordre": 6,
            "duree_mini_jours": 42,
            "duree_maxi_jours": 84,
            "responsable_principal": "Architecte + BET + Économiste",
            "responsable_validation": "ACO + Direction",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si dépassement budget + 8 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES",
            "sous_phase": "2.4 PRO - Projet",
            "ordre": 7,
            "duree_mini_jours": 56,
            "duree_maxi_jours": 112,
            "responsable_principal": "Architecte + BET complet",
            "responsable_validation": "ACO + Direction + Financeurs",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si études non finalisées + 12 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES",
            "sous_phase": "2.5 DCE - Dossier Consultation",
            "ordre": 8,
            "duree_mini_jours": 28,
            "duree_maxi_jours": 56,
            "responsable_principal": "Architecte + Économiste",
            "responsable_validation": "ACO + Gestionnaire marchés",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si DCE incomplet + 6 semaines"
        },
        
        # ======================= PHASE 3 : AUTORISATIONS =======================
        {
            "phase_principale": "3. AUTORISATIONS",
            "sous_phase": "3.1 Dépôt PC - Permis de Construire",
            "ordre": 9,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Architecte",
            "responsable_validation": "Mairie",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si dépôt tardif + 2 semaines"
        },
        {
            "phase_principale": "3. AUTORISATIONS",
            "sous_phase": "3.2 Instruction PC",
            "ordre": 10,
            "duree_mini_jours": 90,
            "duree_maxi_jours": 180,
            "responsable_principal": "Mairie + DDT",
            "responsable_validation": "Services instructeurs",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si dépassement délai légal + 2 semaines"
        },
        {
            "phase_principale": "3. AUTORISATIONS",
            "sous_phase": "3.3 PC accordé + purge recours",
            "ordre": 11,
            "duree_mini_jours": 60,
            "duree_maxi_jours": 90,
            "responsable_principal": "ACO + Notaire",
            "responsable_validation": "ACO",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si recours déposé"
        },
        
        # ======================= PHASE 4 : FINANCEMENT =======================
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.1 LBU - Ligne de Crédit validée",
            "ordre": 12,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "Direction + ACO",
            "responsable_validation": "Conseil d'Administration",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si validation retardée + 6 semaines"
        },
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.2 Contrat prêt CDC signé",
            "ordre": 13,
            "duree_mini_jours": 45,
            "duree_maxi_jours": 120,
            "responsable_principal": "Direction Financière",
            "responsable_validation": "CDC + SPIC",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si négociation bloquée + 8 semaines"
        },
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.3 Cofinancements CAF/Action Logement",
            "ordre": 14,
            "duree_mini_jours": 60,
            "duree_maxi_jours": 180,
            "responsable_principal": "ACO + Direction",
            "responsable_validation": "CAF + Action Logement",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si refus ou retard + 10 semaines"
        },
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.4 Garanties et sûretés",
            "ordre": 15,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 60,
            "responsable_principal": "Direction Financière",
            "responsable_validation": "Banques + Assureurs",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si garanties insuffisantes + 4 semaines"
        },
        
        # ======================= PHASE 5 : CONSULTATION =======================
        {
            "phase_principale": "5. CONSULTATION",
            "sous_phase": "5.1 Lancement consultation entreprises",
            "ordre": 16,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "Gestionnaire marchés",
            "responsable_validation": "ACO",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si publication retardée + 1 semaine"
        },
        {
            "phase_principale": "5. CONSULTATION",
            "sous_phase": "5.2 Période de consultation",
            "ordre": 17,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 52,
            "responsable_principal": "Gestionnaire marchés",
            "responsable_validation": "Commission d'appel d'offres",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si peu d'offres reçues"
        },
        {
            "phase_principale": "5. CONSULTATION",
            "sous_phase": "5.3 Réception et analyse offres",
            "ordre": 18,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 35,
            "responsable_principal": "ACO + Économiste + Architecte",
            "responsable_validation": "Commission technique",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si analyse tardive + 3 semaines"
        },
        {
            "phase_principale": "5. CONSULTATION",
            "sous_phase": "5.4 Négociation si autorisée",
            "ordre": 19,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 28,
            "responsable_principal": "ACO + Équipe projet",
            "responsable_validation": "Direction",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si négociation infructueuse"
        },
        {
            "phase_principale": "5. CONSULTATION",
            "sous_phase": "5.5 CAO - Commission d'Appel d'Offres",
            "ordre": 20,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 14,
            "responsable_principal": "Président CAO",
            "responsable_validation": "CAO",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si décision négative ou report"
        },
        
        # ======================= PHASE 6 : ATTRIBUTION =======================
        {
            "phase_principale": "6. ATTRIBUTION",
            "sous_phase": "6.1 Notification marché attributaire",
            "ordre": 21,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 10,
            "responsable_principal": "Gestionnaire marchés",
            "responsable_validation": "Entreprise attributaire",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si refus entreprise"
        },
        {
            "phase_principale": "6. ATTRIBUTION",
            "sous_phase": "6.2 Constitution dossier marché",
            "ordre": 22,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "Entreprise + ACO",
            "responsable_validation": "ACO + Services juridiques",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si dossier incomplet + 4 semaines"
        },
        {
            "phase_principale": "6. ATTRIBUTION",
            "sous_phase": "6.3 Signature marché de travaux",
            "ordre": 23,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Direction SPIC",
            "responsable_validation": "Direction + Entreprise",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si signature retardée + 2 semaines"
        },
        {
            "phase_principale": "6. ATTRIBUTION",
            "sous_phase": "6.4 OS - Ordre de Service",
            "ordre": 24,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "ACO",
            "responsable_validation": "ACO + Entreprise",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si délai OS dépassé"
        },
        
        # ======================= PHASE 7 : TRAVAUX =======================
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.1 DOC - Date Ouverture Chantier",
            "ordre": 25,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 7,
            "responsable_principal": "Entreprise",
            "responsable_validation": "ACO + Maîtrise d'œuvre",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si retard ouverture"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.2 Travaux fondations",
            "ordre": 26,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "Entreprise gros œuvre",
            "responsable_validation": "Maîtrise d'œuvre + Contrôleur technique",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si retard planning + 2 semaines"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.3 Élévation - Hors d'eau",
            "ordre": 27,
            "duree_mini_jours": 60,
            "duree_maxi_jours": 180,
            "responsable_principal": "Entreprise gros œuvre",
            "responsable_validation": "Maîtrise d'œuvre",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si retard hors d'eau + 3 semaines"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.4 Second œuvre - Hors d'air",
            "ordre": 28,
            "duree_mini_jours": 90,
            "duree_maxi_jours": 240,
            "responsable_principal": "Entreprises tous corps d'état",
            "responsable_validation": "Maîtrise d'œuvre",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si coordination défaillante"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.5 Finitions et équipements",
            "ordre": 29,
            "duree_mini_jours": 60,
            "duree_maxi_jours": 120,
            "responsable_principal": "Entreprises spécialisées",
            "responsable_validation": "Maîtrise d'œuvre + ACO",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si finitions non conformes"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.6 Réunions de chantier",
            "ordre": 30,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 7,
            "responsable_principal": "Maîtrise d'œuvre",
            "responsable_validation": "Toutes parties prenantes",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si absence répétée entreprises"
        },
        {
            "phase_principale": "7. TRAVAUX",
            "sous_phase": "7.7 DACT - Date Achèvement Travaux",
            "ordre": 31,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 3,
            "responsable_principal": "Entreprise générale",
            "responsable_validation": "Maîtrise d'œuvre",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si DACT non déclarée"
        },
        
        # ======================= PHASE 8 : RÉCEPTION =======================
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.1 Pré-réception technique",
            "ordre": 32,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Maîtrise d'œuvre + ACO",
            "responsable_validation": "Équipe SPIC",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réserves importantes"
        },
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.2 Réception technique officielle",
            "ordre": 33,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 14,
            "responsable_principal": "Direction SPIC",
            "responsable_validation": "Direction + Maîtrise d'œuvre",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réception refusée"
        },
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.3 Début GPA - Garantie Parfait Achèvement",
            "ordre": 34,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 7,
            "responsable_principal": "Entreprises",
            "responsable_validation": "SPIC",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si entreprises non joignables"
        },
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.4 DOE - Dossier Ouvrages Exécutés",
            "ordre": 35,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "Entreprises + Maîtrise d'œuvre",
            "responsable_validation": "ACO + Services techniques",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si DOE incomplet + 6 semaines"
        },
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.5 DIUO - Dossier Intervention Ultérieure",
            "ordre": 36,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 60,
            "responsable_principal": "Coordonnateur SPS",
            "responsable_validation": "ACO + Service maintenance",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si DIUO manquant + 4 semaines"
        },
        {
            "phase_principale": "8. RÉCEPTION",
            "sous_phase": "8.6 Levée réserves GPA",
            "ordre": 37,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 365,
            "responsable_principal": "Entreprises",
            "responsable_validation": "ACO + Maîtrise d'œuvre",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si réserves non levées + 2 mois"
        },
        
        # ======================= PHASE 9 : LIVRAISON =======================
        {
            "phase_principale": "9. LIVRAISON",
            "sous_phase": "9.1 Livraison aux locataires",
            "ordre": 38,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 60,
            "responsable_principal": "Service gestion locative",
            "responsable_validation": "Locataires + SPIC",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si livraison retardée"
        },
        {
            "phase_principale": "9. LIVRAISON",
            "sous_phase": "9.2 Mise en gestion locative",
            "ordre": 39,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "Service gestion",
            "responsable_validation": "Direction",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si mise en gestion retardée"
        },
        {
            "phase_principale": "9. LIVRAISON",
            "sous_phase": "9.3 Bilan de commercialisation",
            "ordre": 40,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "Service commercial + ACO",
            "responsable_validation": "Direction",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si logements vacants"
        },
        
        # ======================= PHASE 10 : CLÔTURE =======================
        {
            "phase_principale": "10. CLÔTURE",
            "sous_phase": "10.1 Fin GPA - 1 an",
            "ordre": 41,
            "duree_mini_jours": 365,
            "duree_maxi_jours": 365,
            "responsable_principal": "Entreprises",
            "responsable_validation": "SPIC",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si réclamations post-GPA"
        },
        {
            "phase_principale": "10. CLÔTURE",
            "sous_phase": "10.2 Clôture administrative",
            "ordre": 42,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "ACO + Services administratifs",
            "responsable_validation": "Direction",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si documents manquants"
        },
        {
            "phase_principale": "10. CLÔTURE",
            "sous_phase": "10.3 Clôture financière",
            "ordre": 43,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 120,
            "responsable_principal": "Direction financière",
            "responsable_validation": "Conseil d'administration",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si écarts budgétaires"
        },
        {
            "phase_principale": "10. CLÔTURE",
            "sous_phase": "10.4 Solde final opération",
            "ordre": 44,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "Direction",
            "responsable_validation": "Conseil d'administration",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si solde non finalisé"
        },
        {
            "phase_principale": "10. CLÔTURE",
            "sous_phase": "10.5 Archivage dossier complet",
            "ordre": 45,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 60,
            "responsable_principal": "ACO + Services généraux",
            "responsable_validation": "Direction",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si archivage incomplet"
        }
    ],

 # ======================= RÉFÉRENTIEL VEFA =======================
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
        {
            "phase_principale": "1. PROSPECTION",
            "sous_phase": "1.2 Analyse programme promoteur",
            "ordre": 2,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "ACO + Programmiste",
            "responsable_validation": "Direction SPIC",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si programme inadéquat"
        },
        {
            "phase_principale": "1. PROSPECTION",
            "sous_phase": "1.3 Négociation prix VEFA",
            "ordre": 3,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 84,
            "responsable_principal": "ACO + Direction",
            "responsable_validation": "Direction + Conseil",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si négociation bloquée + 6 semaines"
        },
        {
            "phase_principale": "2. CONTRACTUALISATION",
            "sous_phase": "2.1 Signature VEFA",
            "ordre": 4,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "Direction + Notaire",
            "responsable_validation": "Direction + Promoteur",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si signature retardée"
        },
        {
            "phase_principale": "2. CONTRACTUALISATION",
            "sous_phase": "2.2 Conditions suspensives",
            "ordre": 5,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 120,
            "responsable_principal": "Promoteur + SPIC",
            "responsable_validation": "Toutes parties",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si conditions non levées"
        },
        {
            "phase_principale": "3. AUTORISATIONS",
            "sous_phase": "3.1 Dépôt PC promoteur",
            "ordre": 6,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 14,
            "responsable_principal": "Promoteur",
            "responsable_validation": "Mairie",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si dépôt tardif promoteur"
        },
        {
            "phase_principale": "3. AUTORISATIONS",
            "sous_phase": "3.2 PC accordé + purge",
            "ordre": 7,
            "duree_mini_jours": 90,
            "duree_maxi_jours": 180,
            "responsable_principal": "Services instructeurs",
            "responsable_validation": "Mairie + Promoteur",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si refus PC ou recours"
        },
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.1 Signature prêt CDC",
            "ordre": 8,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "Direction Financière",
            "responsable_validation": "CDC + SPIC",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si financement refusé"
        },
        {
            "phase_principale": "4. FINANCEMENT",
            "sous_phase": "4.2 Garanties financières",
            "ordre": 9,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 60,
            "responsable_principal": "Promoteur + SPIC",
            "responsable_validation": "Organismes financiers",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si garanties insuffisantes"
        },
        {
            "phase_principale": "5. LANCEMENT PROMOTEUR",
            "sous_phase": "5.1 Lancement travaux promoteur",
            "ordre": 10,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "Promoteur",
            "responsable_validation": "Promoteur",
            "statut_global_associe": "🚧 Travaux promoteur",
            "alerte_automatique": "Si démarrage retardé"
        },
        {
            "phase_principale": "6. SUIVI TRAVAUX",
            "sous_phase": "6.1 Suivi avancement promoteur",
            "ordre": 11,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "ACO",
            "responsable_validation": "ACO",
            "statut_global_associe": "🚧 Travaux promoteur",
            "alerte_automatique": "Si retard constaté planning"
        },
        {
            "phase_principale": "6. SUIVI TRAVAUX",
            "sous_phase": "6.2 Contrôles qualité SPIC",
            "ordre": 12,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "ACO + Expert externe",
            "responsable_validation": "SPIC",
            "statut_global_associe": "🚧 Travaux promoteur",
            "alerte_automatique": "Si non-conformités détectées"
        },
        {
            "phase_principale": "6. SUIVI TRAVAUX",
            "sous_phase": "6.3 Réunions suivi périodiques",
            "ordre": 13,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 30,
            "responsable_principal": "Promoteur + SPIC",
            "responsable_validation": "Toutes parties",
            "statut_global_associe": "🚧 Travaux promoteur",
            "alerte_automatique": "Si absence réunions"
        },
        {
            "phase_principale": "6. SUIVI TRAVAUX",
            "sous_phase": "6.4 Gestion des non-conformités",
            "ordre": 14,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 28,
            "responsable_principal": "ACO",
            "responsable_validation": "Promoteur",
            "statut_global_associe": "🚧 Travaux promoteur",
            "alerte_automatique": "Si non-conformités non traitées"
        },
        {
            "phase_principale": "7. LIVRAISON",
            "sous_phase": "7.1 Pré-réception SPIC",
            "ordre": 15,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "ACO + Expert",
            "responsable_validation": "SPIC",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réserves importantes"
        },
        {
            "phase_principale": "7. LIVRAISON",
            "sous_phase": "7.2 Réception définitive",
            "ordre": 16,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "Direction SPIC",
            "responsable_validation": "SPIC + Promoteur",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réception refusée"
        },
        {
            "phase_principale": "7. LIVRAISON",
            "sous_phase": "7.3 Remise clés MOA",
            "ordre": 17,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 7,
            "responsable_principal": "Promoteur",
            "responsable_validation": "SPIC",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si remise retardée"
        },
        {
            "phase_principale": "8. GARANTIES",
            "sous_phase": "8.1 Garanties promoteur actives",
            "ordre": 18,
            "duree_mini_jours": 365,
            "duree_maxi_jours": 3650,
            "responsable_principal": "Promoteur",
            "responsable_validation": "Assureurs",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si défaut garantie"
        },
        {
            "phase_principale": "8. GARANTIES",
            "sous_phase": "8.2 Suivi garanties décennale/biennale",
            "ordre": 19,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 60,
            "responsable_principal": "Service maintenance",
            "responsable_validation": "Direction",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si sinistres non couverts"
        },
        {
            "phase_principale": "9. CLÔTURE",
            "sous_phase": "9.1 Fin garanties",
            "ordre": 20,
            "duree_mini_jours": 3650,
            "duree_maxi_jours": 3650,
            "responsable_principal": "Service juridique",
            "responsable_validation": "Direction",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si litiges en cours"
        },
        {
            "phase_principale": "9. CLÔTURE",
            "sous_phase": "9.2 Clôture administrative",
            "ordre": 21,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "ACO",
            "responsable_validation": "Direction",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si documents manquants"
        },
        {
            "phase_principale": "9. CLÔTURE",
            "sous_phase": "9.3 Archivage dossier VEFA",
            "ordre": 22,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Services généraux",
            "responsable_validation": "Direction",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si archivage incomplet"
        }
    ],
    
    # ======================= RÉFÉRENTIEL AMO =======================
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
        {
            "phase_principale": "1. ASSISTANCE ÉTUDES",
            "sous_phase": "1.2 Assistance programmation",
            "ordre": 2,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "AMO + Programmiste",
            "responsable_validation": "MOA",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si programme non validé + 4 semaines"
        },
        {
            "phase_principale": "1. ASSISTANCE ÉTUDES",
            "sous_phase": "1.3 Assistance choix MOE",
            "ordre": 3,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 56,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si MOE non désignée + 6 semaines"
        },
        {
            "phase_principale": "2. SUIVI CONSULTATION MOE",
            "sous_phase": "2.1 Rédaction consultation MOE",
            "ordre": 4,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 28,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si consultation incomplète"
        },
        {
            "phase_principale": "2. SUIVI CONSULTATION MOE",
            "sous_phase": "2.2 Analyse offres MOE",
            "ordre": 5,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO + Commission",
            "responsable_validation": "MOA",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si analyse tardive"
        },
        {
            "phase_principale": "3. ASSISTANCE DCE",
            "sous_phase": "3.1 Relecture pièces DCE",
            "ordre": 6,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 35,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA + MOE",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si DCE non validé + 3 semaines"
        },
        {
            "phase_principale": "3. ASSISTANCE DCE",
            "sous_phase": "3.2 Rédaction pièces complémentaires",
            "ordre": 7,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si pièces manquantes"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.1 Assistance lancement consultation",
            "ordre": 8,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "AMO + Gestionnaire marchés",
            "responsable_validation": "MOA",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si lancement retardé"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.2 Analyse offres entreprises",
            "ordre": 9,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 35,
            "responsable_principal": "AMO + MOE",
            "responsable_validation": "Commission d'analyse",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si analyse insuffisante"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.3 Assistance négociation",
            "ordre": 10,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si négociation infructueuse"
        },
        {
            "phase_principale": "5. SUIVI TRAVAUX",
            "sous_phase": "5.1 Assistance ordre de service",
            "ordre": 11,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 14,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si OS retardé"
        },
        {
            "phase_principale": "5. SUIVI TRAVAUX",
            "sous_phase": "5.2 Suivi planning travaux",
            "ordre": 12,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "AMO + MOE",
            "responsable_validation": "MOA",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si retards importants"
        },
        {
            "phase_principale": "5. SUIVI TRAVAUX",
            "sous_phase": "5.3 Rédaction avenants",
            "ordre": 13,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA + Services juridiques",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si avenant nécessaire urgent"
        },
        {
            "phase_principale": "5. SUIVI TRAVAUX",
            "sous_phase": "5.4 Rédaction mises en demeure",
            "ordre": 14,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 7,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si MED urgente"
        },
        {
            "phase_principale": "5. SUIVI TRAVAUX",
            "sous_phase": "5.5 Alertes MOA sur dysfonctionnements",
            "ordre": 15,
            "duree_mini_jours": 1,
            "duree_maxi_jours": 3,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si dysfonctionnement majeur"
        },
        {
            "phase_principale": "6. RÉCEPTION",
            "sous_phase": "6.1 Assistance pré-réception",
            "ordre": 16,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "AMO + MOE",
            "responsable_validation": "MOA",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réserves importantes"
        },
        {
            "phase_principale": "6. RÉCEPTION",
            "sous_phase": "6.2 Assistance réception définitive",
            "ordre": 17,
            "duree_mini_jours": 3,
            "duree_maxi_jours": 7,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réception compromise"
        },
        {
            "phase_principale": "7. SUIVI GPA",
            "sous_phase": "7.1 Suivi levée réserves",
            "ordre": 18,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 365,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si réserves non levées + 2 mois"
        },
        {
            "phase_principale": "7. SUIVI GPA",
            "sous_phase": "7.2 Assistance gestion sinistres",
            "ordre": 19,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA + Assureurs",
            "statut_global_associe": "📄 En GPA",
            "alerte_automatique": "Si sinistre non traité"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.1 Bilan final mission",
            "ordre": 20,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si bilan non finalisé"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.2 Remise dossier complet",
            "ordre": 21,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "AMO",
            "responsable_validation": "MOA",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si dossier incomplet"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.3 Solde honoraires AMO",
            "ordre": 22,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "MOA",
            "responsable_validation": "Services financiers",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si solde non réglé"
        }
    ],
    
    # ======================= RÉFÉRENTIEL MANDAT =======================
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
        {
            "phase_principale": "1. CONVENTION MANDAT",
            "sous_phase": "1.2 Signature convention",
            "ordre": 2,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Direction SPIC",
            "responsable_validation": "Toutes parties",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si signature retardée"
        },
        {
            "phase_principale": "1. CONVENTION MANDAT",
            "sous_phase": "1.3 Conditions suspensives",
            "ordre": 3,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 120,
            "responsable_principal": "SPIC + MOA mandante",
            "responsable_validation": "Toutes parties",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si conditions non levées"
        },
        {
            "phase_principale": "2. ÉTUDES PRÉALABLES",
            "sous_phase": "2.1 Programme détaillé",
            "ordre": 4,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 42,
            "responsable_principal": "SPIC + Programmiste",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si programme non validé + 4 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES PRÉALABLES",
            "sous_phase": "2.2 Choix architecte",
            "ordre": 5,
            "duree_mini_jours": 28,
            "duree_maxi_jours": 56,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si architecte non choisi + 6 semaines"
        },
        {
            "phase_principale": "2. ÉTUDES PRÉALABLES",
            "sous_phase": "2.3 Études de faisabilité",
            "ordre": 6,
            "duree_mini_jours": 42,
            "duree_maxi_jours": 84,
            "responsable_principal": "Architecte + SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si faisabilité négative"
        },
        {
            "phase_principale": "3. PROCÉDURES MOA",
            "sous_phase": "3.1 Demandes autorisations",
            "ordre": 7,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "SPIC + Architecte",
            "responsable_validation": "Services instructeurs",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si demandes incomplètes"
        },
        {
            "phase_principale": "3. PROCÉDURES MOA",
            "sous_phase": "3.2 Montage financier",
            "ordre": 8,
            "duree_mini_jours": 30,
            "duree_maxi_jours": 90,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante + Financeurs",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si financement insuffisant"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.1 Préparation DCE",
            "ordre": 9,
            "duree_mini_jours": 28,
            "duree_maxi_jours": 56,
            "responsable_principal": "Architecte + SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🟡 À l'étude",
            "alerte_automatique": "Si DCE non finalisé + 6 semaines"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.2 Lancement consultation",
            "ordre": 10,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "SPIC",
            "responsable_validation": "Commission d'appel d'offres",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si lancement retardé"
        },
        {
            "phase_principale": "4. CONSULTATION ENTREPRISES",
            "sous_phase": "4.3 Analyse offres",
            "ordre": 11,
            "duree_mini_jours": 21,
            "duree_maxi_jours": 42,
            "responsable_principal": "SPIC + Architecte",
            "responsable_validation": "Commission",
            "statut_global_associe": "🛠️ En consultation",
            "alerte_automatique": "Si analyse tardive + 4 semaines"
        },
        {
            "phase_principale": "5. PASSATION MARCHÉS",
            "sous_phase": "5.1 Attribution marchés",
            "ordre": 12,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si attribution retardée"
        },
        {
            "phase_principale": "5. PASSATION MARCHÉS",
            "sous_phase": "5.2 Signature marchés",
            "ordre": 13,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "SPIC",
            "responsable_validation": "Entreprises + MOA mandante",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si signature retardée + 3 semaines"
        },
        {
            "phase_principale": "5. PASSATION MARCHÉS",
            "sous_phase": "5.3 Ordre de service",
            "ordre": 14,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "SPIC",
            "responsable_validation": "Entreprises",
            "statut_global_associe": "📋 Marché attribué",
            "alerte_automatique": "Si OS non émis + 2 semaines"
        },
        {
            "phase_principale": "6. SUIVI CHANTIER",
            "sous_phase": "6.1 Lancement travaux",
            "ordre": 15,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "Entreprises",
            "responsable_validation": "SPIC + Architecte",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si démarrage retardé"
        },
        {
            "phase_principale": "6. SUIVI CHANTIER",
            "sous_phase": "6.2 Pilotage planning",
            "ordre": 16,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "SPIC + Architecte",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si retards importants planning"
        },
        {
            "phase_principale": "6. SUIVI CHANTIER",
            "sous_phase": "6.3 Réunions de chantier",
            "ordre": 17,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 7,
            "responsable_principal": "SPIC + Architecte",
            "responsable_validation": "Toutes parties",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si absences répétées"
        },
        {
            "phase_principale": "6. SUIVI CHANTIER",
            "sous_phase": "6.4 Gestion avenants",
            "ordre": 18,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 42,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si avenant urgent nécessaire"
        },
        {
            "phase_principale": "6. SUIVI CHANTIER",
            "sous_phase": "6.5 Contrôle qualité",
            "ordre": 19,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "SPIC + Contrôleur technique",
            "responsable_validation": "SPIC",
            "statut_global_associe": "🚧 En travaux",
            "alerte_automatique": "Si non-conformités détectées"
        },
        {
            "phase_principale": "7. RÉCEPTION",
            "sous_phase": "7.1 Pré-réception",
            "ordre": 20,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 21,
            "responsable_principal": "SPIC + Architecte",
            "responsable_validation": "SPIC",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réserves importantes"
        },
        {
            "phase_principale": "7. RÉCEPTION",
            "sous_phase": "7.2 Réception définitive",
            "ordre": 21,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 14,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "📦 Livré (non soldé)",
            "alerte_automatique": "Si réception refusée"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.1 Remise à la MOA",
            "ordre": 22,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si remise retardée"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.2 Bilan final mandat",
            "ordre": 23,
            "duree_mini_jours": 14,
            "duree_maxi_jours": 30,
            "responsable_principal": "SPIC",
            "responsable_validation": "MOA mandante",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si bilan non finalisé"
        },
        {
            "phase_principale": "8. CLÔTURE MISSION",
            "sous_phase": "8.3 Solde mission",
            "ordre": 24,
            "duree_mini_jours": 7,
            "duree_maxi_jours": 30,
            "responsable_principal": "MOA mandante",
            "responsable_validation": "Services financiers",
            "statut_global_associe": "✅ Clôturé (soldé)",
            "alerte_automatique": "Si solde non réglé + 2 semaines"
        }
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
        "📄 En GPA", "✅ Clôturé (soldé)", "🔴 Bloqué"
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

def get_phase_by_order(type_operation: str, ordre: int) -> Dict:
    """Récupère une phase spécifique par son ordre"""
    phases = get_phases_for_type(type_operation)
    for phase in phases:
        if phase.get('ordre') == ordre:
            return phase
    return {}

def get_next_phases(type_operation: str, current_ordre: int, nb_phases: int = 3) -> List[Dict]:
    """Récupère les prochaines phases à partir d'un ordre donné"""
    phases = get_phases_for_type(type_operation)
    next_phases = []
    
    for phase in phases:
        if phase.get('ordre', 0) > current_ordre:
            next_phases.append(phase)
            if len(next_phases) >= nb_phases:
                break
    
    return next_phases

def get_phase_color(est_validee: bool, date_fin_prevue: str = None) -> str:
    """Retourne la couleur d'une phase selon son état"""
    if est_validee:
        return "🟢"  # Vert - Validée
    
    if date_fin_prevue:
        try:
            from datetime import datetime
            date_fin = datetime.strptime(date_fin_prevue, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if today > date_fin:
                return "🔴"  # Rouge - En retard
            elif (date_fin - today).days <= 7:
                return "🟠"  # Orange - Échéance proche
        except:
            pass
    
    return "🟡"  # Jaune - En cours

def calculate_phase_progress(phases: List[Dict]) -> float:
    """Calcule le pourcentage d'avancement basé sur les phases validées"""
    if not phases:
        return 0.0
    
    total_phases = len(phases)
    phases_validees = sum(1 for phase in phases if phase.get('est_validee', False))
    
    return round((phases_validees / total_phases) * 100, 1)

def get_current_phase(phases: List[Dict]) -> Dict:
    """Récupère la phase actuelle (première non validée)"""
    for phase in sorted(phases, key=lambda x: x.get('ordre', 0)):
        if not phase.get('est_validee', False):
            return phase
    
    # Si toutes les phases sont validées, retourner la dernière
    if phases:
        return max(phases, key=lambda x: x.get('ordre', 0))
    
    return {}

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
        
        # Vérifier l'ordre des phases
        for type_op, phases in REFERENTIELS_PHASES.items():
            ordres = [phase.get('ordre', 0) for phase in phases]
            if len(ordres) != len(set(ordres)):  # Vérifier unicité
                return False
            if ordres != sorted(ordres):  # Vérifier ordre croissant
                return False
                
        return True
    except Exception as e:
        print(f"Erreur validation config: {e}")
        return False

def get_statut_from_phases(phases: List[Dict], type_operation: str) -> str:
    """Détermine le statut global basé sur l'avancement des phases"""
    if not phases:
        return "🟡 À l'étude"
    
    # Phase actuelle (première non validée)
    current_phase = get_current_phase(phases)
    if not current_phase:
        return "✅ Clôturé (soldé)"
    
    # Mapping des phases vers les statuts
    phase_to_status = {
        "MONTAGE": "🟡 À l'étude",
        "ÉTUDES": "🟡 À l'étude", 
        "AUTORISATIONS": "🟡 À l'étude",
        "FINANCEMENT": "🟡 À l'étude",
        "CONSULTATION": "🛠️ En consultation",
        "ATTRIBUTION": "📋 Marché attribué",
        "PASSATION": "📋 Marché attribué",
        "TRAVAUX": "🚧 En travaux",
        "SUIVI": "🚧 En travaux",
        "RÉCEPTION": "📦 Livré (non soldé)",
        "LIVRAISON": "📦 Livré (non soldé)",
        "GARANTIES": "📄 En GPA",
        "GPA": "📄 En GPA",
        "CLÔTURE": "✅ Clôturé (soldé)"
    }
    
    phase_principale = current_phase.get('phase_principale', '').upper()
    
    # Recherche du statut correspondant
    for keyword, statut in phase_to_status.items():
        if keyword in phase_principale:
            return statut
    
    # Statut par défaut selon le type
    if type_operation == "VEFA" and "TRAVAUX" in phase_principale:
        return "🚧 Travaux promoteur"
    
    return "🟡 À l'étude"

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
    "default_timeout_days": 30,
    "backup_retention_days": 90,
    "alert_advance_days": 7
}

# ============================================================================
# DONNÉES DE TEST (OPTIONNEL)
# ============================================================================

OPERATIONS_TEST = [
    {
        "nom": "Résidence Les Palmiers",
        "type_operation": "OPP",
        "responsable_aco": "MSL",
        "commune": "Les Abymes",
        "promoteur": "",
        "nb_logements_total": 24,
        "nb_lls": 12,
        "nb_llts": 8,
        "nb_pls": 4,
        "budget_total": 3200000.0
    },
    {
        "nom": "44 Cour Charneau",
        "type_operation": "OPP", 
        "responsable_aco": "MARIO M",
        "commune": "Sainte-Anne",
        "promoteur": "",
        "nb_logements_total": 18,
        "nb_lls": 10,
        "nb_llts": 6,
        "nb_pls": 2,
        "budget_total": 2800000.0
    }
]

# Validation de la configuration au chargement
if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration valide")
        print(f"📊 OPP: {len(REFERENTIELS_PHASES['OPP'])} phases")
        print(f"📊 VEFA: {len(REFERENTIELS_PHASES['VEFA'])} phases") 
        print(f"📊 AMO: {len(REFERENTIELS_PHASES['AMO'])} phases")
        print(f"📊 MANDAT: {len(REFERENTIELS_PHASES['MANDAT'])} phases")
    else:
        print("❌ Erreur dans la configuration")