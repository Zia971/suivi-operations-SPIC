"""
Module de gestion de la base de données SQLite pour SPIC 2.0 - VERSION STREAMLIT
Classe DatabaseManager avec gestion des alertes, blocages, statuts dynamiques et module REM
Intégration complète avec la logique journal → TOP 3 risques + phases custom
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import config

class DatabaseManager:
    """Gestionnaire de base de données SQLite pour SPIC 2.0 avec alertes intelligentes et REM"""
    
    def __init__(self, db_path: str = "spic_operations.db"):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Retourne une connexion à la base de données avec support concurrent"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
        # Activer WAL mode pour améliorer la concurrence
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        return conn
    
    def init_database(self):
        """Initialise les tables de la base de données avec structure complète"""
        conn = self.get_connection()
        try:
            # Table operations - Structure enrichie avec REM
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL UNIQUE,
                    type_operation TEXT NOT NULL CHECK (type_operation IN ('OPP', 'VEFA', 'AMO', 'MANDAT')),
                    statut_principal TEXT NOT NULL DEFAULT '🟡 À l''étude',
                    responsable_aco TEXT NOT NULL,
                    commune TEXT,
                    promoteur TEXT,
                    nb_logements_total INTEGER DEFAULT 0,
                    nb_lls INTEGER DEFAULT 0,
                    nb_llts INTEGER DEFAULT 0,
                    nb_pls INTEGER DEFAULT 0,
                    budget_total REAL DEFAULT 0,
                    cout_foncier REAL DEFAULT 0,
                    cout_travaux_estime REAL DEFAULT 0,
                    adresse_terrain TEXT,
                    surface_terrain_m2 REAL DEFAULT 0,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_debut_etudes DATE,
                    date_livraison_cible DATE,
                    pourcentage_avancement REAL DEFAULT 0,
                    score_risque REAL DEFAULT 0,
                    has_active_blocage BOOLEAN DEFAULT FALSE,
                    derniere_alerte TEXT,
                    date_derniere_alerte TIMESTAMP,
                    rem_annuelle_prevue REAL DEFAULT 0,
                    rem_annuelle_realisee REAL DEFAULT 0,
                    phase_actuelle TEXT,
                    infos_complementaires TEXT
                )
            """)
            
            # Table phases - Enrichie avec gestion custom et domaines
            conn.execute("""
                CREATE TABLE IF NOT EXISTS phases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    phase_principale TEXT NOT NULL,
                    sous_phase TEXT NOT NULL,
                    ordre_phase INTEGER NOT NULL,
                    est_validee BOOLEAN NOT NULL DEFAULT FALSE,
                    date_debut_prevue DATE,
                    date_fin_prevue DATE,
                    date_debut_reelle DATE,
                    date_fin_reelle DATE,
                    duree_mini_jours INTEGER,
                    duree_maxi_jours INTEGER,
                    responsable_principal TEXT,
                    responsable_validation TEXT,
                    commentaire TEXT,
                    blocage_actif BOOLEAN DEFAULT FALSE,
                    date_blocage TIMESTAMP,
                    motif_blocage TEXT,
                    alerte_activee BOOLEAN NOT NULL DEFAULT TRUE,
                    couleur_statut TEXT DEFAULT '🟡',
                    domaine TEXT DEFAULT 'OPERATIONNEL' CHECK (domaine IN ('OPERATIONNEL', 'JURIDIQUE', 'BUDGETAIRE')),
                    impact_rem BOOLEAN DEFAULT FALSE,
                    rem_impact_desc TEXT,
                    phase_financiere TEXT,
                    is_custom_phase BOOLEAN DEFAULT FALSE,
                    created_by TEXT,
                    date_creation_custom TIMESTAMP,
                    FOREIGN KEY (operation_id) REFERENCES operations (id),
                    UNIQUE(operation_id, ordre_phase)
                )
            """)
            
            # Table journal - Source unique des notes et commentaires
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    date_saisie TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    auteur TEXT NOT NULL,
                    type_action TEXT NOT NULL DEFAULT 'INFO',
                    contenu TEXT NOT NULL,
                    phase_concernee TEXT,
                    niveau_urgence INTEGER DEFAULT 1 CHECK (niveau_urgence BETWEEN 1 AND 5),
                    est_blocage BOOLEAN DEFAULT FALSE,
                    est_resolu BOOLEAN DEFAULT FALSE,
                    date_resolution TIMESTAMP,
                    resolu_par TEXT,
                    commentaire_resolution TEXT,
                    impact_planning BOOLEAN DEFAULT FALSE,
                    mots_cles TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table alertes - Génération automatique depuis journal
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alertes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    phase_id INTEGER,
                    journal_id INTEGER,
                    type_alerte TEXT NOT NULL CHECK (type_alerte IN ('BLOCAGE', 'RETARD', 'ATTENTION', 'INFO', 'VALIDATION')),
                    niveau_urgence INTEGER NOT NULL CHECK (niveau_urgence BETWEEN 1 AND 5) DEFAULT 3,
                    message TEXT NOT NULL,
                    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    date_echeance DATE,
                    est_traitee BOOLEAN NOT NULL DEFAULT FALSE,
                    date_traitement TIMESTAMP,
                    traite_par TEXT,
                    impact_score INTEGER DEFAULT 0,
                    visible_timeline BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (operation_id) REFERENCES operations (id),
                    FOREIGN KEY (phase_id) REFERENCES phases (id),
                    FOREIGN KEY (journal_id) REFERENCES journal (id)
                )
            """)
            
            # Table configuration_aco - Gestion dynamique des ACO
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_aco (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_aco TEXT UNIQUE NOT NULL,
                    actif BOOLEAN DEFAULT TRUE,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operations_en_cours INTEGER DEFAULT 0,
                    operations_total INTEGER DEFAULT 0,
                    rem_annuelle_gere REAL DEFAULT 0,
                    performance_score REAL DEFAULT 0
                )
            """)
            
            # Table projections_rem - Suivi des projections REM
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projections_rem (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    date_calcul TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rem_annuelle_prevue REAL NOT NULL,
                    rem_semestrielle_prevue REAL NOT NULL,
                    date_livraison_estimee DATE,
                    facteur_correction REAL DEFAULT 1.0,
                    rem_lls REAL DEFAULT 0,
                    rem_llts REAL DEFAULT 0,
                    rem_pls REAL DEFAULT 0,
                    statut_calcul TEXT DEFAULT 'PREVISIONNEL',
                    commentaires TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table phases_templates - Templates pour phases custom
            conn.execute("""
                CREATE TABLE IF NOT EXISTS phases_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_template TEXT UNIQUE NOT NULL,
                    type_operation TEXT NOT NULL,
                    phase_principale TEXT NOT NULL,
                    sous_phase TEXT NOT NULL,
                    duree_mini_jours INTEGER,
                    duree_maxi_jours INTEGER,
                    responsable_type TEXT,
                    domaine TEXT DEFAULT 'OPERATIONNEL',
                    impact_rem BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    utilisation_count INTEGER DEFAULT 0,
                    created_by TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index optimisés pour performance Streamlit
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_operations_type ON operations (type_operation)",
                "CREATE INDEX IF NOT EXISTS idx_operations_statut ON operations (statut_principal)",
                "CREATE INDEX IF NOT EXISTS idx_operations_aco ON operations (responsable_aco)",
                "CREATE INDEX IF NOT EXISTS idx_operations_risque ON operations (score_risque DESC)",
                "CREATE INDEX IF NOT EXISTS idx_operations_blocage ON operations (has_active_blocage)",
                "CREATE INDEX IF NOT EXISTS idx_operations_rem ON operations (rem_annuelle_prevue DESC)",
                
                "CREATE INDEX IF NOT EXISTS idx_phases_operation ON phases (operation_id)",
                "CREATE INDEX IF NOT EXISTS idx_phases_validee ON phases (est_validee)",
                "CREATE INDEX IF NOT EXISTS idx_phases_blocage ON phases (blocage_actif)",
                "CREATE INDEX IF NOT EXISTS idx_phases_ordre ON phases (operation_id, ordre_phase)",
                "CREATE INDEX IF NOT EXISTS idx_phases_domaine ON phases (domaine)",
                "CREATE INDEX IF NOT EXISTS idx_phases_custom ON phases (is_custom_phase)",
                
                "CREATE INDEX IF NOT EXISTS idx_journal_operation ON journal (operation_id)",
                "CREATE INDEX IF NOT EXISTS idx_journal_date ON journal (date_saisie DESC)",
                "CREATE INDEX IF NOT EXISTS idx_journal_blocage ON journal (est_blocage, est_resolu)",
                "CREATE INDEX IF NOT EXISTS idx_journal_urgence ON journal (niveau_urgence DESC)",
                
                "CREATE INDEX IF NOT EXISTS idx_alertes_operation ON alertes (operation_id)",
                "CREATE INDEX IF NOT EXISTS idx_alertes_urgence ON alertes (niveau_urgence DESC)",
                "CREATE INDEX IF NOT EXISTS idx_alertes_actives ON alertes (est_traitee, date_creation)",
                "CREATE INDEX IF NOT EXISTS idx_alertes_timeline ON alertes (visible_timeline, date_creation)",
                
                "CREATE INDEX IF NOT EXISTS idx_aco_actif ON configuration_aco (actif)",
                "CREATE INDEX IF NOT EXISTS idx_rem_operation ON projections_rem (operation_id, date_calcul DESC)"
            ]
            
            for index in indexes:
                conn.execute(index)
            
            # Triggers pour mise à jour automatique
            self._create_triggers(conn)
            
            # Initialiser les ACO par défaut
            self._init_default_acos(conn)
            
            conn.commit()
            print("✅ Base de données SPIC 2.0 Streamlit initialisée avec succès")
            
        except Exception as e:
            print(f"❌ Erreur initialisation base : {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _create_triggers(self, conn):
        """Crée les triggers pour mise à jour automatique"""
        try:
            # Trigger mise à jour date_maj sur operations
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS update_operation_timestamp 
                AFTER UPDATE ON operations
                BEGIN
                    UPDATE operations SET date_maj = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)
            
            # Trigger pour mise à jour automatique de la phase actuelle
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS update_phase_actuelle 
                AFTER UPDATE OF est_validee ON phases
                WHEN NEW.est_validee = 1
                BEGIN
                    UPDATE operations 
                    SET phase_actuelle = (
                        SELECT sous_phase 
                        FROM phases 
                        WHERE operation_id = NEW.operation_id 
                        AND est_validee = 0 
                        ORDER BY ordre_phase ASC 
                        LIMIT 1
                    )
                    WHERE id = NEW.operation_id;
                END
            """)
            
            # Trigger génération alerte automatique pour blocages
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS auto_generate_alert_from_journal
                AFTER INSERT ON journal
                WHEN NEW.est_blocage = 1
                BEGIN
                    INSERT INTO alertes (operation_id, journal_id, type_alerte, niveau_urgence, message, visible_timeline)
                    VALUES (NEW.operation_id, NEW.id, 'BLOCAGE', NEW.niveau_urgence, 
                           'Blocage signalé: ' || NEW.contenu, 1);
                END
            """)
            
        except Exception as e:
            print(f"⚠️ Erreur création triggers : {e}")
    
    def _init_default_acos(self, conn):
        """Initialise les ACO par défaut s'ils n'existent pas"""
        try:
            for aco in config.INTERVENANTS_BASE['ACO']:
                conn.execute("""
                    INSERT OR IGNORE INTO configuration_aco (nom_aco)
                    VALUES (?)
                """, (aco,))
        except Exception as e:
            print(f"⚠️ Erreur initialisation ACO par défaut : {e}")
    
    # ============================================================================
    # GESTION DES OPÉRATIONS
    # ============================================================================
    
    def create_operation(self, nom: str, type_operation: str, responsable_aco: str, 
                        commune: str = "", promoteur: str = "", nb_logements_total: int = 0,
                        nb_lls: int = 0, nb_llts: int = 0, nb_pls: int = 0, 
                        budget_total: float = 0.0, cout_foncier: float = 0.0,
                        cout_travaux_estime: float = 0.0, adresse_terrain: str = "",
                        surface_terrain_m2: float = 0.0, date_debut_etudes: str = None,
                        date_livraison_cible: str = None, phase_actuelle_ordre: int = 1) -> int:
        """Crée une nouvelle opération avec génération automatique des phases"""
        
        conn = self.get_connection()
        try:
            # Calculer la projection REM initiale
            rem_initial = config.calculate_rem_projection({
                'nb_lls': nb_lls,
                'nb_llts': nb_llts,
                'nb_pls': nb_pls,
                'budget_total': budget_total
            })
            
            rem_annuelle = rem_initial.get('rem_annuelle', 0) if 'erreur' not in rem_initial else 0
            
            # Déterminer la phase actuelle et le statut selon l'avancement
            phases_ref = config.get_phases_for_type(type_operation)
            phase_actuelle = phases_ref[phase_actuelle_ordre - 1]['sous_phase'] if phase_actuelle_ordre <= len(phases_ref) else None
            
            # Calculer le pourcentage selon la phase actuelle
            pourcentage_initial = ((phase_actuelle_ordre - 1) / len(phases_ref)) * 100 if phases_ref else 0
            
            # Calculer le statut automatique
            phases_simulees = [{'est_validee': i < phase_actuelle_ordre, 'blocage_actif': False} for i in range(len(phases_ref))]
            statut_initial = config.calculate_status_from_phases(phases_simulees, type_operation)
            
            # Insertion de l'opération
            cursor = conn.execute("""
                INSERT INTO operations (
                    nom, type_operation, responsable_aco, commune, promoteur,
                    nb_logements_total, nb_lls, nb_llts, nb_pls, budget_total,
                    cout_foncier, cout_travaux_estime, adresse_terrain, surface_terrain_m2,
                    date_debut_etudes, date_livraison_cible, pourcentage_avancement,
                    statut_principal, phase_actuelle, rem_annuelle_prevue
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nom, type_operation, responsable_aco, commune, promoteur,
                  nb_logements_total, nb_lls, nb_llts, nb_pls, budget_total,
                  cout_foncier, cout_travaux_estime, adresse_terrain, surface_terrain_m2,
                  date_debut_etudes, date_livraison_cible, pourcentage_initial,
                  statut_initial, phase_actuelle, rem_annuelle))
            
            operation_id = cursor.lastrowid
            
            # Génération automatique des phases selon le type
            self._generate_phases_for_operation(operation_id, type_operation, conn, phase_actuelle_ordre)
            
            # Créer projection REM initiale
            if rem_annuelle > 0:
                self._create_rem_projection(operation_id, rem_initial, conn)
            
            # Ajout entrée journal de création
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu, niveau_urgence)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_id, "Système", "VALIDATION", 
                  f"Opération '{nom}' créée avec {len(phases_ref)} phases automatiques. Phase actuelle: {phase_actuelle}", 2))
            
            # Mise à jour compteur ACO
            conn.execute("""
                UPDATE configuration_aco 
                SET operations_en_cours = operations_en_cours + 1,
                    operations_total = operations_total + 1,
                    rem_annuelle_gere = rem_annuelle_gere + ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE nom_aco = ?
            """, (rem_annuelle, responsable_aco))
            
            conn.commit()
            print(f"✅ Opération '{nom}' créée avec ID {operation_id}")
            return operation_id
            
        except Exception as e:
            print(f"❌ Erreur création opération : {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _generate_phases_for_operation(self, operation_id: int, type_operation: str, conn, phase_actuelle_ordre: int = 1):
        """Génère les phases automatiquement selon le type d'opération"""
        
        try:
            phases_referentiel = config.get_phases_for_type(type_operation)
            print(f"DEBUG: Génération de {len(phases_referentiel)} phases pour {type_operation}")
            
            for phase in phases_referentiel:
                ordre = phase.get('ordre', 0)
                
                # Marquer comme validée si ordre < phase actuelle
                est_validee = ordre < phase_actuelle_ordre
                
                # Couleur selon l'état
                couleur = config.get_phase_color(est_validee)
                
                conn.execute("""
                    INSERT INTO phases (
                        operation_id, phase_principale, sous_phase, ordre_phase,
                        duree_mini_jours, duree_maxi_jours, responsable_principal,
                        responsable_validation, est_validee, couleur_statut,
                        domaine, impact_rem, rem_impact_desc, phase_financiere
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    phase.get('phase_principale', ''),
                    phase.get('sous_phase', ''),
                    ordre,
                    phase.get('duree_mini_jours', 30),
                    phase.get('duree_maxi_jours', 60),
                    phase.get('responsable_principal', ''),
                    phase.get('responsable_validation', ''),
                    est_validee,
                    couleur,
                    phase.get('domaine', 'OPERATIONNEL'),
                    phase.get('impact_rem', False),
                    phase.get('rem_impact_desc', ''),
                    phase.get('phase_financiere', '')
                ))
            
            print(f"✅ {len(phases_referentiel)} phases générées pour l'opération {operation_id}")
            
        except Exception as e:
            print(f"❌ Erreur génération phases : {e}")
            raise
    
    def _create_rem_projection(self, operation_id: int, rem_data: Dict, conn):
        """Crée une projection REM pour une opération"""
        try:
            if 'erreur' in rem_data:
                return
                
            conn.execute("""
                INSERT INTO projections_rem (
                    operation_id, rem_annuelle_prevue, rem_semestrielle_prevue,
                    facteur_correction, rem_lls, rem_llts, rem_pls, commentaires
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_id,
                rem_data.get('rem_annuelle', 0),
                rem_data.get('rem_annuelle', 0) / 2,
                rem_data.get('facteur_correction', 1.0),
                rem_data.get('repartition', {}).get('LLS', 0),
                rem_data.get('repartition', {}).get('LLTS', 0),
                rem_data.get('repartition', {}).get('PLS', 0),
                f"Projection initiale - {rem_data.get('nb_logements', {}).get('total', 0)} logements"
            ))
        except Exception as e:
            print(f"⚠️ Erreur création projection REM : {e}")
    
    def get_operations(self, responsable: str = None, type_op: str = None, 
                      statut: str = None, with_risk_score: bool = True,
                      limit: int = None, offset: int = 0) -> List[Dict]:
        """Récupère la liste des opérations avec pagination optimisée pour Streamlit"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT o.*, 
                       COALESCE(pr.rem_annuelle_prevue, 0) as rem_projection,
                       (SELECT COUNT(*) FROM alertes a WHERE a.operation_id = o.id AND a.est_traitee = 0) as alertes_actives
                FROM operations o
                LEFT JOIN projections_rem pr ON o.id = pr.operation_id 
                    AND pr.id = (SELECT MAX(id) FROM projections_rem WHERE operation_id = o.id)
                WHERE 1=1
            """
            params = []
            
            if responsable:
                query += " AND o.responsable_aco = ?"
                params.append(responsable)
            
            if type_op:
                query += " AND o.type_operation = ?"
                params.append(type_op)
            
            if statut:
                query += " AND o.statut_principal = ?"
                params.append(statut)
            
            query += " ORDER BY o.score_risque DESC, o.date_maj DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor = conn.execute(query, params)
            operations = [dict(row) for row in cursor.fetchall()]
            
            # Calcul du score de risque si demandé (optimisé)
            if with_risk_score:
                for operation in operations:
                    if operation['score_risque'] == 0:  # Recalculer seulement si nécessaire
                        operation['score_risque'] = self._calculate_operation_risk_score(operation['id'], conn)
            
            return operations
            
        except Exception as e:
            print(f"❌ Erreur récupération opérations : {e}")
            return []
        finally:
            conn.close()
    
    def get_operation_detail(self, operation_id: int) -> Optional[Dict]:
        """Récupère les détails complets d'une opération"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT o.*, 
                       pr.rem_annuelle_prevue,
                       pr.rem_semestrielle_prevue,
                       pr.facteur_correction,
                       (SELECT COUNT(*) FROM alertes a WHERE a.operation_id = o.id AND a.est_traitee = 0) as alertes_actives,
                       (SELECT COUNT(*) FROM journal j WHERE j.operation_id = o.id AND j.est_blocage = 1 AND j.est_resolu = 0) as blocages_actifs
                FROM operations o
                LEFT JOIN projections_rem pr ON o.id = pr.operation_id 
                    AND pr.id = (SELECT MAX(id) FROM projections_rem WHERE operation_id = o.id)
                WHERE o.id = ?
            """, (operation_id,))
            
            row = cursor.fetchone()
            
            if row:
                operation = dict(row)
                return operation
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération détail opération : {e}")
            return None
        finally:
            conn.close()
    
    # ============================================================================
    # GESTION DES PHASES
    # ============================================================================
    
    def get_phases_by_operation(self, operation_id: int, include_custom: bool = True) -> List[Dict]:
        """Récupère toutes les phases d'une opération avec couleurs mises à jour"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT * FROM phases 
                WHERE operation_id = ?
            """
            
            if not include_custom:
                query += " AND is_custom_phase = 0"
                
            query += " ORDER BY ordre_phase"
            
            cursor = conn.execute(query, (operation_id,))
            phases = [dict(row) for row in cursor.fetchall()]
            
            # Mise à jour des couleurs selon l'état actuel
            for phase in phases:
                phase['couleur_statut'] = config.get_phase_color(
                    phase.get('est_validee', False),
                    phase.get('date_fin_prevue'),
                    phase.get('blocage_actif', False)
                )
            
            return phases
            
        except Exception as e:
            print(f"❌ Erreur récupération phases : {e}")
            return []
        finally:
            conn.close()
    
    def update_phase(self, phase_id: int, est_validee: bool = None, 
                    date_debut_prevue: str = None, date_fin_prevue: str = None,
                    date_debut_reelle: str = None, date_fin_reelle: str = None,
                    duree_mini_jours: int = None, duree_maxi_jours: int = None,
                    blocage_actif: bool = None, motif_blocage: str = None) -> bool:
        """Met à jour une phase avec gestion des blocages et durées dynamiques"""
        
        conn = self.get_connection()
        try:
            # Construction dynamique de la requête
            updates = []
            params = []
            
            if est_validee is not None:
                updates.append("est_validee = ?")
                params.append(est_validee)
                if est_validee:
                    updates.append("date_fin_reelle = ?")
                    params.append(datetime.now().date().isoformat())
            
            if date_debut_prevue is not None:
                updates.append("date_debut_prevue = ?")
                params.append(date_debut_prevue)
            
            if date_fin_prevue is not None:
                updates.append("date_fin_prevue = ?")
                params.append(date_fin_prevue)
            
            if date_debut_reelle is not None:
                updates.append("date_debut_reelle = ?")
                params.append(date_debut_reelle)
            
            if date_fin_reelle is not None:
                updates.append("date_fin_reelle = ?")
                params.append(date_fin_reelle)
            
            if duree_mini_jours is not None:
                updates.append("duree_mini_jours = ?")
                params.append(duree_mini_jours)
            
            if duree_maxi_jours is not None:
                updates.append("duree_maxi_jours = ?")
                params.append(duree_maxi_jours)
            
            if blocage_actif is not None:
                updates.append("blocage_actif = ?")
                params.append(blocage_actif)
                if blocage_actif:
                    updates.append("date_blocage = ?")
                    params.append(datetime.now().isoformat())
            
            if motif_blocage is not None:
                updates.append("motif_blocage = ?")
                params.append(motif_blocage)
            
            if not updates:
                return True
            
            # Mise à jour de la couleur statut
            couleur = config.get_phase_color(est_validee or False, date_fin_prevue, blocage_actif or False)
            updates.append("couleur_statut = ?")
            params.append(couleur)
            
            params.append(phase_id)
            
            query = f"UPDATE phases SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour phase : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_custom_phase(self, operation_id: int, nom_phase: str, phase_principale: str,
                        ordre_insertion: int, duree_mini: int = 7, duree_maxi: int = 30,
                        responsable: str = "", domaine: str = "OPERATIONNEL",
                        created_by: str = "Utilisateur") -> bool:
        """Ajoute une phase personnalisée à une opération"""
        
        conn = self.get_connection()
        try:
            # Décaler les phases existantes
            conn.execute("""
                UPDATE phases 
                SET ordre_phase = ordre_phase + 1 
                WHERE operation_id = ? AND ordre_phase >= ?
            """, (operation_id, ordre_insertion))
            
              # Décaler les phases existantes
            conn.execute("""
                UPDATE phases 
                SET ordre_phase = ordre_phase + 1 
                WHERE operation_id = ? AND ordre_phase >= ?
            """, (operation_id, ordre_insertion))
            
            # Insérer la nouvelle phase
            conn.execute("""
                INSERT INTO phases (
                    operation_id, phase_principale, sous_phase, ordre_phase,
                    duree_mini_jours, duree_maxi_jours, responsable_principal,
                    domaine, is_custom_phase, created_by, date_creation_custom,
                    couleur_statut
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_id, phase_principale, nom_phase, ordre_insertion,
                duree_mini, duree_maxi, responsable, domaine, True, created_by,
                datetime.now().isoformat(), config.PHASE_MANAGEMENT["phase_colors"]["en_cours"]
            ))
            
            # Ajouter entrée journal
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu, niveau_urgence)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_id, created_by, "INFO", f"Phase personnalisée ajoutée: '{nom_phase}' (ordre {ordre_insertion})", 2))
            
            conn.commit()
            print(f"✅ Phase custom '{nom_phase}' ajoutée à l'opération {operation_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout phase custom : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def reorder_phases(self, operation_id: int, new_order_list: List[int]) -> bool:
        """Réorganise l'ordre des phases selon une nouvelle liste d'IDs"""
        
        conn = self.get_connection()
        try:
            # Vérifier que tous les IDs appartiennent à l'opération
            cursor = conn.execute("""
                SELECT COUNT(*) FROM phases WHERE operation_id = ? AND id IN ({})
            """.format(','.join('?' * len(new_order_list))), [operation_id] + new_order_list)
            
            if cursor.fetchone()[0] != len(new_order_list):
                raise ValueError("Certains IDs de phases n'appartiennent pas à cette opération")
            
            # Mettre à jour l'ordre
            for nouveau_ordre, phase_id in enumerate(new_order_list, 1):
                conn.execute("""
                    UPDATE phases SET ordre_phase = ? WHERE id = ?
                """, (nouveau_ordre, phase_id))
            
            # Ajouter entrée journal
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu, niveau_urgence)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_id, "Utilisateur", "INFO", f"Ordre des phases réorganisé ({len(new_order_list)} phases)", 1))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur réorganisation phases : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_operation_progress_and_status(self, operation_id: int) -> bool:
        """Met à jour l'avancement ET le statut d'une opération automatiquement"""
        
        conn = self.get_connection()
        try:
            # Récupérer les phases
            phases = self.get_phases_by_operation(operation_id)
            if not phases:
                return False
            
            # Calculer le pourcentage d'avancement
            total_phases = len(phases)
            phases_validees = sum(1 for phase in phases if phase.get('est_validee', False))
            pourcentage = (phases_validees / total_phases) * 100
            
            # Obtenir les informations de l'opération
            operation = self.get_operation_detail(operation_id)
            if not operation:
                return False
            
            # Calculer le nouveau statut
            nouveau_statut = config.calculate_status_from_phases(phases, operation['type_operation'])
            
            # Calculer le score de risque
            score_risque = self._calculate_operation_risk_score(operation_id, conn)
            
            # Vérifier s'il y a des blocages actifs
            has_blocage = any(phase.get('blocage_actif', False) for phase in phases)
            
            # Déterminer la phase actuelle (première non validée)
            phase_actuelle = None
            for phase in sorted(phases, key=lambda x: x.get('ordre_phase', 0)):
                if not phase.get('est_validee', False):
                    phase_actuelle = phase.get('sous_phase')
                    break
            
            # Mettre à jour l'opération
            conn.execute("""
                UPDATE operations 
                SET pourcentage_avancement = ?, 
                    statut_principal = ?,
                    score_risque = ?,
                    has_active_blocage = ?,
                    phase_actuelle = ?,
                    date_maj = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (pourcentage, nouveau_statut, score_risque, has_blocage, phase_actuelle, operation_id))
            
            # Mettre à jour la projection REM si nécessaire
            self._update_rem_projection(operation_id, pourcentage, nouveau_statut, conn)
            
            conn.commit()
            
            print(f"✅ Opération {operation_id} mise à jour: {pourcentage:.1f}% - {nouveau_statut}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour opération : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def _update_rem_projection(self, operation_id: int, pourcentage: float, statut: str, conn):
        """Met à jour la projection REM selon l'avancement"""
        try:
            # Appliquer facteur de correction selon l'avancement
            facteur = 1.0
            
            if pourcentage < 60 and "🚧 En travaux" in statut:
                facteur += config.REM_CONFIG["facteurs_correction"]["retard_livraison"]
            elif pourcentage > 80:
                facteur += config.REM_CONFIG["facteurs_correction"]["avance_livraison"]
            
            if facteur != 1.0:
                conn.execute("""
                    UPDATE projections_rem 
                    SET facteur_correction = ?,
                        commentaires = COALESCE(commentaires, '') || ' | Correction avancement: ' || ?
                    WHERE operation_id = ? 
                    AND id = (SELECT MAX(id) FROM projections_rem WHERE operation_id = ?)
                """, (facteur, f"{(facteur-1)*100:+.1f}%", operation_id, operation_id))
                
        except Exception as e:
            print(f"⚠️ Erreur mise à jour REM : {e}")
    
    # ============================================================================
    # GESTION DU JOURNAL
    # ============================================================================
    
    def add_journal_entry(self, operation_id: int, auteur: str, type_action: str,
                         contenu: str, phase_concernee: str = None, 
                         est_blocage: bool = False, niveau_urgence: int = 1) -> bool:
        """Ajoute une entrée dans le journal avec génération automatique d'alertes"""
        
        conn = self.get_connection()
        try:
            # Détecter automatiquement s'il s'agit d'un blocage par mots-clés
            mots_cles_blocage = ["bloqué", "arrêt", "problème", "échec", "refus", "litige", "retard important"]
            contenu_lower = contenu.lower()
            
            est_blocage_auto = est_blocage or any(mot in contenu_lower for mot in mots_cles_blocage)
            
            if est_blocage_auto and not est_blocage:
                niveau_urgence = max(niveau_urgence, 3)  # Augmenter l'urgence
            
            # Extraire mots-clés pour recherche
            mots_cles = " ".join([mot for mot in mots_cles_blocage if mot in contenu_lower])
            
            cursor = conn.execute("""
                INSERT INTO journal (
                    operation_id, auteur, type_action, contenu, phase_concernee,
                    est_blocage, niveau_urgence, mots_cles
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (operation_id, auteur, type_action, contenu, phase_concernee, 
                  est_blocage_auto, niveau_urgence, mots_cles))
            
            journal_id = cursor.fetchone()[0]
            
            # Génération automatique d'alerte si blocage ou urgence élevée
            if est_blocage_auto or niveau_urgence >= 4:
                type_alerte = 'BLOCAGE' if est_blocage_auto else 'ATTENTION'
                self._create_automatic_alert(
                    operation_id, None, type_alerte, niveau_urgence,
                    f"Journal: {contenu[:100]}{'...' if len(contenu) > 100 else ''}",
                    conn, journal_id
                )
                
                # Mettre à jour le statut de l'opération si blocage critique
                if est_blocage_auto and type_action == "BLOCAGE":
                    conn.execute("""
                        UPDATE operations 
                        SET statut_principal = '🔴 Bloqué',
                            has_active_blocage = TRUE,
                            derniere_alerte = ?,
                            date_derniere_alerte = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (contenu[:200], operation_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout journal : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_journal_by_operation(self, operation_id: int, include_resolved: bool = True, 
                                limit: int = None) -> List[Dict]:
        """Récupère le journal d'une opération avec pagination"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT j.*, 
                       CASE WHEN j.est_blocage = 1 AND j.est_resolu = 0 THEN 'ACTIF'
                            WHEN j.est_blocage = 1 AND j.est_resolu = 1 THEN 'RÉSOLU'
                            ELSE 'NORMAL' END as statut_blocage
                FROM journal j
                WHERE j.operation_id = ?
            """
            
            if not include_resolved:
                query += " AND (j.est_blocage = 0 OR j.est_resolu = 0)"
            
            query += " ORDER BY j.date_saisie DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, (operation_id,))
            journal = [dict(row) for row in cursor.fetchall()]
            return journal
            
        except Exception as e:
            print(f"❌ Erreur récupération journal : {e}")
            return []
        finally:
            conn.close()
    
    def resolve_blocage(self, journal_id: int, resolu_par: str, commentaire_resolution: str = "") -> bool:
        """Marque un blocage comme résolu"""
        
        conn = self.get_connection()
        try:
            # Marquer le blocage comme résolu
            conn.execute("""
                UPDATE journal 
                SET est_resolu = TRUE,
                    date_resolution = CURRENT_TIMESTAMP,
                    resolu_par = ?,
                    commentaire_resolution = ?
                WHERE id = ? AND est_blocage = TRUE
            """, (resolu_par, commentaire_resolution, journal_id))
            
            # Récupérer l'operation_id pour mise à jour
            cursor = conn.execute("SELECT operation_id FROM journal WHERE id = ?", (journal_id,))
            result = cursor.fetchone()
            
            if result:
                operation_id = result[0]
                
                # Ajouter une entrée journal de résolution
                conn.execute("""
                    INSERT INTO journal (operation_id, auteur, type_action, contenu, niveau_urgence)
                    VALUES (?, ?, ?, ?, ?)
                """, (operation_id, resolu_par, "VALIDATION", f"Blocage résolu - {commentaire_resolution}", 2))
                
                # Marquer les alertes associées comme traitées
                conn.execute("""
                    UPDATE alertes 
                    SET est_traitee = TRUE, 
                        date_traitement = CURRENT_TIMESTAMP,
                        traite_par = ?
                    WHERE journal_id = ?
                """, (resolu_par, journal_id))
                
                # Vérifier s'il reste des blocages actifs
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM journal 
                    WHERE operation_id = ? AND est_blocage = TRUE AND est_resolu = FALSE
                """, (operation_id,))
                
                blocages_restants = cursor.fetchone()[0]
                
                # Si plus de blocages, remettre le statut automatique
                if blocages_restants == 0:
                    self.update_operation_progress_and_status(operation_id)
                    conn.execute("""
                        UPDATE operations 
                        SET has_active_blocage = FALSE
                        WHERE id = ?
                    """, (operation_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur résolution blocage : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============================================================================
    # GESTION DES ALERTES ET TOP 3 RISQUES
    # ============================================================================
    
    def get_operations_at_risk(self, limit: int = 3) -> List[Dict]:
        """Récupère le TOP des opérations à risque avec score détaillé"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT o.*, 
                       (SELECT COUNT(*) FROM alertes a WHERE a.operation_id = o.id AND a.est_traitee = FALSE) as alertes_actives,
                       (SELECT COUNT(*) FROM journal j WHERE j.operation_id = o.id AND j.est_blocage = TRUE AND j.est_resolu = FALSE) as blocages_actifs,
                       (SELECT COUNT(*) FROM phases p WHERE p.operation_id = o.id AND p.est_validee = FALSE 
                        AND p.date_fin_prevue IS NOT NULL AND p.date_fin_prevue < date('now')) as phases_en_retard
                FROM operations o
                WHERE o.statut_principal != '✅ Clôturé (soldé)'
                ORDER BY o.has_active_blocage DESC, o.score_risque DESC, o.date_maj ASC
                LIMIT ?
            """, (limit,))
            
            operations = []
            for row in cursor.fetchall():
                operation = dict(row)
                
                # Calculer le score de risque mis à jour
                operation['score_risque'] = self._calculate_operation_risk_score(operation['id'], conn)
                
                # Ajouter les raisons du risque
                raisons_risque = []
                
                if operation['has_active_blocage'] or operation['blocages_actifs'] > 0:
                    raisons_risque.append("🔴 Blocage actif")
                
                if operation['phases_en_retard'] > 0:
                    raisons_risque.append(f"⏰ {operation['phases_en_retard']} phase(s) en retard")
                
                if operation['alertes_actives'] > 0:
                    raisons_risque.append(f"🚨 {operation['alertes_actives']} alerte(s)")
                
                if operation['pourcentage_avancement'] == 0:
                    raisons_risque.append("📊 Aucun avancement")
                elif operation['pourcentage_avancement'] < 30 and '🚧 En travaux' in operation.get('statut_principal', ''):
                    raisons_risque.append("🚧 Travaux peu avancés")
                
                if not raisons_risque:
                    raisons_risque.append("📈 Risque calculé selon critères")
                
                operation['raisons_risque'] = raisons_risque
                operations.append(operation)
            
            return operations
            
        except Exception as e:
            print(f"❌ Erreur récupération opérations à risque : {e}")
            return []
        finally:
            conn.close()
    
    def _calculate_operation_risk_score(self, operation_id: int, conn) -> float:
        """Calcule le score de risque d'une opération selon la logique config"""
        
        try:
            # Récupérer les données nécessaires avec une seule requête optimisée
            cursor = conn.execute("""
                SELECT o.*,
                       (SELECT COUNT(*) FROM phases p WHERE p.operation_id = o.id) as total_phases,
                       (SELECT COUNT(*) FROM phases p WHERE p.operation_id = o.id AND p.est_validee = 1) as phases_validees,
                       (SELECT COUNT(*) FROM phases p WHERE p.operation_id = o.id AND p.blocage_actif = 1) as phases_bloquees,
                       (SELECT COUNT(*) FROM phases p WHERE p.operation_id = o.id AND p.est_validee = 0 
                        AND p.date_fin_prevue IS NOT NULL AND p.date_fin_prevue < date('now')) as phases_retard,
                       (SELECT COUNT(*) FROM alertes a WHERE a.operation_id = o.id AND a.est_traitee = 0) as alertes_actives
                FROM operations o
                WHERE o.id = ?
            """, (operation_id,))
            
            operation_data = cursor.fetchone()
            if not operation_data:
                return 0.0
            
            operation = dict(operation_data)
            
            # Utiliser la fonction de calcul de config.py (version simplifiée)
            score_risque = 0.0
            
            # 1. Score basé sur l'avancement
            avancement = operation.get('pourcentage_avancement', 0)
            score_avancement = max(0, (100 - avancement) * 0.3)
            
            # 2. Score basé sur le statut
            statut = operation.get('statut_principal', '')
            if '🔴 Bloqué' in statut or operation.get('has_active_blocage', False):
                score_statut = 50
            elif '🚧 En travaux' in statut and avancement < 70:
                score_statut = 20
            elif '🛠️ En consultation' in statut and avancement < 30:
                score_statut = 15
            else:
                score_statut = 0
            
            # 3. Score basé sur les alertes actives
            score_alertes = operation.get('alertes_actives', 0) * 5
            
            # 4. Score basé sur les phases en retard
            score_retard = operation.get('phases_retard', 0) * 5
            
            # 5. Score basé sur les phases bloquées
            score_blocage = operation.get('phases_bloquees', 0) * 10
            
            score_risque = score_avancement + score_statut + score_alertes + score_retard + score_blocage
            
            # Mettre à jour le score dans la base
            conn.execute("UPDATE operations SET score_risque = ? WHERE id = ?", 
                        (min(100, score_risque), operation_id))
            
            return min(100, score_risque)
            
        except Exception as e:
            print(f"❌ Erreur calcul score risque : {e}")
            return 0.0
    
    def _create_automatic_alert(self, operation_id: int, phase_id: int = None, 
                               type_alerte: str = "ATTENTION", niveau_urgence: int = 3,
                               message: str = "", conn = None, journal_id: int = None) -> bool:
        """Crée une alerte automatique avec calcul d'impact"""
        
        try:
            if conn is None:
                conn = self.get_connection()
                should_close = True
            else:
                should_close = False
            
            # Calculer l'impact score selon le type d'alerte
            impact_score = config.TYPES_ALERTES.get(type_alerte, {}).get('priorite', 1) * niveau_urgence
            
            # Créer l'alerte
            conn.execute("""
                INSERT INTO alertes (
                    operation_id, phase_id, journal_id, type_alerte, 
                    niveau_urgence, message, impact_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (operation_id, phase_id, journal_id, type_alerte, niveau_urgence, message, impact_score))
            
            if should_close:
                conn.commit()
                conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création alerte automatique : {e}")
            return False
    
    def get_alerts_by_operation(self, operation_id: int, non_traitees_seulement: bool = True) -> List[Dict]:
        """Récupère les alertes d'une opération avec détails enrichis"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT a.*, 
                       p.sous_phase,
                       j.contenu as journal_contenu,
                       j.auteur as journal_auteur
                FROM alertes a
                LEFT JOIN phases p ON a.phase_id = p.id
                LEFT JOIN journal j ON a.journal_id = j.id
                WHERE a.operation_id = ?
            """
            params = [operation_id]
            
            if non_traitees_seulement:
                query += " AND a.est_traitee = FALSE"
            
            query += " ORDER BY a.niveau_urgence DESC, a.date_creation DESC"
            
            cursor = conn.execute(query, params)
            alertes = [dict(row) for row in cursor.fetchall()]
            
            # Enrichir avec les informations de config
            for alerte in alertes:
                type_info = config.TYPES_ALERTES.get(alerte['type_alerte'], {})
                alerte['couleur'] = type_info.get('couleur', '#6b7280')
                alerte['icone'] = type_info.get('icone', 'ℹ️')
                alerte['description_type'] = type_info.get('description', 'Information')
            
            return alertes
            
        except Exception as e:
            print(f"❌ Erreur récupération alertes : {e}")
            return []
        finally:
            conn.close()
    
    # ============================================================================
    # MODULE REM - RENTABILITÉ
    # ============================================================================
    
    def get_rem_portfolio_summary(self, responsable_aco: str = None, 
                                 periode: str = "annuelle") -> Dict:
        """Calcule le résumé REM d'un portfolio d'opérations"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT o.*, pr.rem_annuelle_prevue, pr.facteur_correction
                FROM operations o
                LEFT JOIN projections_rem pr ON o.id = pr.operation_id 
                    AND pr.id = (SELECT MAX(id) FROM projections_rem WHERE operation_id = o.id)
                WHERE o.statut_principal != '✅ Clôturé (soldé)'
            """
            params = []
            
            if responsable_aco:
                query += " AND o.responsable_aco = ?"
                params.append(responsable_aco)
            
            cursor = conn.execute(query, params)
            operations = [dict(row) for row in cursor.fetchall()]
            
            # Utiliser la fonction de config.py
            portfolio_summary = config.get_rem_portfolio_summary(operations, periode)
            
            return portfolio_summary
            
        except Exception as e:
            print(f"❌ Erreur calcul portfolio REM : {e}")
            return {"erreur": str(e)}
        finally:
            conn.close()
    
    def update_rem_projection(self, operation_id: int, nouveaux_logements: Dict = None,
                             nouvelle_date_livraison: str = None) -> bool:
        """Met à jour la projection REM d'une opération"""
        
        conn = self.get_connection()
        try:
            # Récupérer l'opération actuelle
            operation = self.get_operation_detail(operation_id)
            if not operation:
                return False
            
            # Mettre à jour les logements si fourni
            if nouveaux_logements:
                conn.execute("""
                    UPDATE operations 
                    SET nb_lls = ?, nb_llts = ?, nb_pls = ?, 
                        nb_logements_total = ?, date_maj = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    nouveaux_logements.get('LLS', operation.get('nb_lls', 0)),
                    nouveaux_logements.get('LLTS', operation.get('nb_llts', 0)),
                    nouveaux_logements.get('PLS', operation.get('nb_pls', 0)),
                    sum(nouveaux_logements.values()) if nouveaux_logements else operation.get('nb_logements_total', 0),
                    operation_id
                ))
                
                # Mettre à jour operation dict pour le calcul REM
                operation.update(nouveaux_logements)
                operation['nb_logements_total'] = sum(nouveaux_logements.values())
            
            # Recalculer la projection REM
            rem_data = config.calculate_rem_projection(operation, nouveaux_logements)
            
            if 'erreur' not in rem_data:
                # Créer nouvelle projection
                conn.execute("""
                    INSERT INTO projections_rem (
                        operation_id, rem_annuelle_prevue, rem_semestrielle_prevue,
                        facteur_correction, rem_lls, rem_llts, rem_pls,
                        date_livraison_estimee, commentaires
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    rem_data.get('rem_annuelle', 0),
                    rem_data.get('rem_annuelle', 0) / 2,
                    rem_data.get('facteur_correction', 1.0),
                    rem_data.get('repartition', {}).get('LLS', 0),
                    rem_data.get('repartition', {}).get('LLTS', 0),
                    rem_data.get('repartition', {}).get('PLS', 0),
                    nouvelle_date_livraison,
                    f"Mise à jour projection - {rem_data.get('date_calcul', '')}"
                ))
                
                # Mettre à jour l'opération
                conn.execute("""
                    UPDATE operations 
                    SET rem_annuelle_prevue = ?
                    WHERE id = ?
                """, (rem_data.get('rem_annuelle', 0), operation_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour REM : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============================================================================
    # GESTION DES ACO
    # ============================================================================
    
    def get_acos_list(self, actifs_seulement: bool = True) -> List[Dict]:
        """Récupère la liste des ACO avec leurs statistiques"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT a.*, 
                       COUNT(o.id) as operations_actuelles,
                       COALESCE(AVG(o.pourcentage_avancement), 0) as avancement_moyen,
                       COALESCE(SUM(o.rem_annuelle_prevue), 0) as rem_totale_geree
                FROM configuration_aco a
                LEFT JOIN operations o ON a.nom_aco = o.responsable_aco 
                    AND o.statut_principal != '✅ Clôturé (soldé)'
                WHERE 1=1
            """
            
            if actifs_seulement:
                query += " AND a.actif = TRUE"
            
            query += """
                GROUP BY a.id, a.nom_aco, a.actif, a.date_creation, a.date_modification
                ORDER BY operations_actuelles DESC, a.nom_aco
            """
            
            cursor = conn.execute(query)
            acos = [dict(row) for row in cursor.fetchall()]
            
            return acos
            
        except Exception as e:
            print(f"❌ Erreur récupération ACO : {e}")
            return []
        finally:
            conn.close()
    
    def add_aco(self, nom_aco: str) -> bool:
        """Ajoute un nouveau chargé d'opération"""
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO configuration_aco (nom_aco)
                VALUES (?)
            """, (nom_aco,))
            
            conn.commit()
            
            # Mettre à jour la configuration en mémoire
            if nom_aco not in config.INTERVENANTS['ACO']:
                config.INTERVENANTS['ACO'].append(nom_aco)
            
            print(f"✅ ACO '{nom_aco}' ajouté avec succès")
            return True
            
        except sqlite3.IntegrityError:
            print(f"⚠️ ACO '{nom_aco}' existe déjà")
            return False
        except Exception as e:
            print(f"❌ Erreur ajout ACO : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def remove_aco(self, nom_aco: str) -> bool:
        """Supprime un chargé d'opération (désactivation)"""
        
        conn = self.get_connection()
        try:
            # Vérifier s'il a des opérations en cours
            cursor = conn.execute("""
                SELECT COUNT(*) FROM operations 
                WHERE responsable_aco = ? AND statut_principal != '✅ Clôturé (soldé)'
            """, (nom_aco,))
            
            operations_en_cours = cursor.fetchone()[0]
            
            if operations_en_cours > 0:
                print(f"⚠️ Impossible de supprimer {nom_aco} : {operations_en_cours} opérations en cours")
                return False
            
            # Désactiver l'ACO
            conn.execute("""
                UPDATE configuration_aco 
                SET actif = FALSE, date_modification = CURRENT_TIMESTAMP
                WHERE nom_aco = ?
            """, (nom_aco,))
            
            conn.commit()
            
            # Retirer de la configuration en mémoire
            if nom_aco in config.INTERVENANTS['ACO']:
                config.INTERVENANTS['ACO'].remove(nom_aco)
            
            print(f"✅ ACO '{nom_aco}' désactivé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression ACO : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_aco(self, ancien_nom: str, nouveau_nom: str) -> bool:
        """Modifie le nom d'un chargé d'opération"""
        
        conn = self.get_connection()
        try:
            # Vérifier que l'ancien nom existe
            cursor = conn.execute("""
                SELECT id FROM configuration_aco WHERE nom_aco = ? AND actif = TRUE
            """, (ancien_nom,))
            
            if not cursor.fetchone():
                print(f"⚠️ ACO '{ancien_nom}' introuvable ou inactif")
                return False
            
            # Vérifier que le nouveau nom n'existe pas déjà
            cursor = conn.execute("""
                SELECT id FROM configuration_aco WHERE nom_aco = ?
            """, (nouveau_nom,))
            
            if cursor.fetchone():
                print(f"⚠️ ACO '{nouveau_nom}' existe déjà")
                return False
            
            # Mettre à jour dans configuration_aco
            conn.execute("""
                UPDATE configuration_aco 
                SET nom_aco = ?, date_modification = CURRENT_TIMESTAMP
                WHERE nom_aco = ?
            """, (nouveau_nom, ancien_nom))
            
            # Mettre à jour dans les opérations
            conn.execute("""
                UPDATE operations 
                SET responsable_aco = ?
                WHERE responsable_aco = ?
            """, (nouveau_nom, ancien_nom))
            
            # Mettre à jour dans le journal
            conn.execute("""
                UPDATE journal 
                SET auteur = ?
                WHERE auteur = ?
            """, (nouveau_nom, ancien_nom))
            
            conn.commit()
            
            # Mettre à jour la configuration en mémoire
            if ancien_nom in config.INTERVENANTS['ACO']:
                index = config.INTERVENANTS['ACO'].index(ancien_nom)
                config.INTERVENANTS['ACO'][index] = nouveau_nom
            
            print(f"✅ ACO renommé de '{ancien_nom}' vers '{nouveau_nom}'")
            return True
            
        except Exception as e:
            print(f"❌ Erreur modification ACO : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============================================================================
    # KPI ET STATISTIQUES POUR STREAMLIT
    # ============================================================================
    
    def get_kpi_data(self) -> Dict:
        """Récupère les données KPI enrichies pour le tableau de bord manager"""
        
        conn = self.get_connection()
        try:
            # Nombre total d'opérations
            cursor = conn.execute("SELECT COUNT(*) as total FROM operations")
            total_operations = cursor.fetchone()[0]
            
            # Répartition par statut
            cursor = conn.execute("""
                SELECT statut_principal, COUNT(*) as count 
                FROM operations 
                GROUP BY statut_principal
            """)
            repartition_statuts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Répartition par type
            cursor = conn.execute("""
                SELECT type_operation, COUNT(*) as count 
                FROM operations 
                GROUP BY type_operation
            """)
            repartition_types = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Avancement moyen
            cursor = conn.execute("""
                SELECT AVG(pourcentage_avancement) as avg 
                FROM operations 
                WHERE statut_principal != '✅ Clôturé (soldé)'
            """)
            avancement_moyen = cursor.fetchone()[0] or 0
            
            # Opérations bloquées
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM operations 
                WHERE has_active_blocage = TRUE OR statut_principal LIKE '%Bloqué%'
            """)
            operations_bloquees = cursor.fetchone()[0]
            
            # Alertes actives
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM alertes 
                WHERE est_traitee = FALSE
            """)
            alertes_actives = cursor.fetchone()[0]
            
            # Opérations en retard (phases dépassées)
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT p.operation_id) as count
                FROM phases p
                WHERE p.est_validee = FALSE 
                AND p.date_fin_prevue IS NOT NULL 
                AND p.date_fin_prevue < date('now')
            """)
            operations_en_retard = cursor.fetchone()[0]
            
            # Évolution dernière semaine
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM operations 
                WHERE date_creation >= date('now', '-7 days')
            """)
            nouvelles_operations = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM operations 
                WHERE statut_principal = '✅ Clôturé (soldé)'
                AND date_maj >= date('now', '-7 days')
            """)
            operations_cloturees = cursor.fetchone()[0]
            
            # REM totale du portfolio
            cursor = conn.execute("""
                SELECT COALESCE(SUM(o.rem_annuelle_prevue), 0) as rem_totale,
                       COUNT(CASE WHEN o.rem_annuelle_prevue > 0 THEN 1 END) as ops_avec_rem
                FROM operations o
                WHERE o.statut_principal != '✅ Clôturé (soldé)'
            """)
            rem_data = cursor.fetchone()
            rem_totale = rem_data[0]
            ops_avec_rem = rem_data[1]
            
            # Budget total en cours
            cursor = conn.execute("""
                SELECT COALESCE(SUM(budget_total), 0) as budget_total
                FROM operations 
                WHERE statut_principal != '✅ Clôturé (soldé)'
            """)
            budget_total_portfolio = cursor.fetchone()[0]
            
            return {
                'total_operations': total_operations,
                'repartition_statuts': repartition_statuts,
                'repartition_types': repartition_types,
                'avancement_moyen': round(avancement_moyen, 1),
                'operations_bloquees': operations_bloquees,
                'alertes_actives': alertes_actives,
                'operations_en_retard': operations_en_retard,
                'nouvelles_operations_semaine': nouvelles_operations,
                'operations_cloturees_semaine': operations_cloturees,
                'rem_totale_portfolio': round(rem_totale, 2),
                'operations_avec_rem': ops_avec_rem,
                'budget_total_portfolio': round(budget_total_portfolio, 2),
                'date_calcul': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération KPI : {e}")
            return {}
        finally:
            conn.close()
    
    def get_performance_aco(self, nom_aco: str) -> Dict:
        """Récupère les métriques de performance d'un ACO"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_operations,
                    COUNT(CASE WHEN statut_principal != '✅ Clôturé (soldé)' THEN 1 END) as operations_actives,
                    AVG(pourcentage_avancement) as avancement_moyen,
                    AVG(score_risque) as risque_moyen,
                    COUNT(CASE WHEN has_active_blocage = TRUE THEN 1 END) as operations_bloquees,
                    SUM(CASE WHEN statut_principal = '✅ Clôturé (soldé)' THEN 1 ELSE 0 END) as operations_terminees,
                    COALESCE(SUM(rem_annuelle_prevue), 0) as rem_totale_geree,
                    COALESCE(SUM(budget_total), 0) as budget_total_gere
                FROM operations 
                WHERE responsable_aco = ?
            """, (nom_aco,))
            
            result = cursor.fetchone()
            if not result:
                return {"erreur": "ACO introuvable"}
            
            perf = dict(result)
            
            # Calculer le taux de réussite
            if perf['total_operations'] > 0:
                perf['taux_reussite'] = round((perf['operations_terminees'] / perf['total_operations']) * 100, 1)
            else:
                perf['taux_reussite'] = 0
            
            # Calculer la performance relative (par rapport à la moyenne)
            cursor = conn.execute("""
                SELECT AVG(pourcentage_avancement) as avg_global
                FROM operations 
                WHERE statut_principal != '✅ Clôturé (soldé)'
            """)
            avg_global = cursor.fetchone()[0] or 0
            
            perf['performance_relative'] = round(perf['avancement_moyen'] - avg_global, 1) if avg_global > 0 else 0
            
            # Tâches prioritaires de la semaine
            cursor = conn.execute("""
                SELECT COUNT(*) as taches_semaine
                FROM phases p
                JOIN operations o ON p.operation_id = o.id
                WHERE o.responsable_aco = ?
                AND p.est_validee = FALSE
                AND p.date_fin_prevue BETWEEN date('now') AND date('now', '+7 days')
            """, (nom_aco,))
            
            perf['taches_semaine'] = cursor.fetchone()[0]
            
            return perf
            
        except Exception as e:
            print(f"❌ Erreur performance ACO : {e}")
            return {"erreur": str(e)}
        finally:
            conn.close()
    
    # ============================================================================
    # FONCTIONS UTILITAIRES ET MAINTENANCE
    # ============================================================================
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Sauvegarde la base de données avec horodatage"""
        
        if backup_path is None:
            backup_path = f"spic_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Sauvegarde créée : {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde : {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Récupère les statistiques de la base de données pour Streamlit"""
        
        conn = self.get_connection()
        try:
            stats = {}
            
            # Statistiques par table
            tables = ['operations', 'phases', 'journal', 'alertes', 'configuration_aco', 'projections_rem']
            
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"total_{table}"] = cursor.fetchone()[0]
            
            # Taille de la base
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['taille_db_mo'] = round((page_count * page_size) / (1024 * 1024), 2)
            
            # Performance
            cursor = conn.execute("PRAGMA journal_mode")
            stats['journal_mode'] = cursor.fetchone()[0]
            
            # Dernière modification
            import os
            if os.path.exists(self.db_path):
                stats['derniere_modification'] = datetime.fromtimestamp(
                    os.path.getmtime(self.db_path)
                ).strftime('%d/%m/%Y %H:%M')
            
            # Alertes de maintenance
            alertes_maintenance = []
            
            if stats['taille_db_mo'] > 100:
                alertes_maintenance.append("Base de données volumineuse (>100MB)")
            
            if stats['total_alertes'] > 1000:
                alertes_maintenance.append("Nombreuses alertes en base")
            
            stats['alertes_maintenance'] = alertes_maintenance
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur récupération statistiques : {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """Nettoie les anciennes données pour optimiser Streamlit"""
        
        conn = self.get_connection()
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            # Supprimer les alertes traitées anciennes
            cursor = conn.execute("""
                DELETE FROM alertes 
                WHERE est_traitee = TRUE 
                AND date_traitement < ?
            """, (cutoff_date,))
            alertes_supprimees = cursor.rowcount
            
            # Supprimer les entrées journal anciennes (sauf blocages non résolus)
            cursor = conn.execute("""
                DELETE FROM journal 
                WHERE date_saisie < ? 
                AND (est_blocage = FALSE OR est_resolu = TRUE)
                AND type_action = 'INFO'
            """, (cutoff_date,))
            journal_supprime = cursor.rowcount
            
            # Supprimer les anciennes projections REM (garder les 3 dernières par opération)
            cursor = conn.execute("""
                DELETE FROM projections_rem 
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY operation_id ORDER BY date_calcul DESC) as rn
                        FROM projections_rem
                    ) WHERE rn <= 3
                )
            """)
            projections_supprimees = cursor.rowcount
            
            # Optimiser la base après nettoyage
            conn.execute("VACUUM")
            
            conn.commit()
            
            print(f"✅ Nettoyage effectué : {alertes_supprimees} alertes, {journal_supprime} entrées journal, {projections_supprimees} projections REM")
            return True
            
        except Exception as e:
            print(f"❌ Erreur nettoyage : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def optimize_for_streamlit(self) -> bool:
        """Optimise la base de données pour les performances Streamlit"""
        
        conn = self.get_connection()
        try:
            # Analyser les requêtes
            conn.execute("ANALYZE")
            
            # Optimiser la configuration SQLite pour Streamlit
            optimizations = [
                "PRAGMA cache_size = 10000",
                "PRAGMA temp_store = MEMORY",
                "PRAGMA mmap_size = 67108864",  # 64MB
                "PRAGMA optimize"
            ]
            
            for optimization in optimizations:
                conn.execute(optimization)
            
            print("✅ Base de données optimisée pour Streamlit")
            return True
            
        except Exception as e:
            print(f"❌ Erreur optimisation : {e}")
            return False
        finally:
            conn.close()
    
    def search_operations(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Recherche d'opérations avec terme de recherche"""
        
        conn = self.get_connection()
        try:
            search_pattern = f"%{search_term}%"
            
            cursor = conn.execute("""
                SELECT o.*, 
                       'nom' as match_field
                FROM operations o
                WHERE o.nom LIKE ?
                
                UNION
                
                SELECT o.*, 
                       'commune' as match_field
                FROM operations o
                WHERE o.commune LIKE ?
                
                UNION
                
                SELECT o.*, 
                       'responsable' as match_field
                FROM operations o
                WHERE o.responsable_aco LIKE ?
                
                ORDER BY pourcentage_avancement DESC
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except Exception as e:
            print(f"❌ Erreur recherche : {e}")
            return []
        finally:
            conn.close()
    
    def get_timeline_data(self, operation_id: int) -> Dict:
        """Récupère les données pour la timeline enrichie"""
        
        conn = self.get_connection()
        try:
            # Phases avec domaines
            cursor = conn.execute("""
                SELECT p.*, 
                       CASE 
                           WHEN p.domaine = 'OPERATIONNEL' THEN '#3b82f6'
                           WHEN p.domaine = 'JURIDIQUE' THEN '#8b5cf6'
                           WHEN p.domaine = 'BUDGETAIRE' THEN '#10b981'
                           ELSE '#6b7280'
                       END as couleur_domaine
                FROM phases p
                WHERE p.operation_id = ?
                ORDER BY p.ordre_phase
            """, (operation_id,))
            
            phases = [dict(row) for row in cursor.fetchall()]
            
            # Entrées journal importantes pour timeline
            cursor = conn.execute("""
                SELECT j.*, 
                       CASE 
                           WHEN j.est_blocage = 1 AND j.est_resolu = 0 THEN '#dc2626'
                           WHEN j.niveau_urgence >= 4 THEN '#f59e0b'
                           WHEN j.type_action = 'VALIDATION' THEN '#10b981'
                           ELSE '#6b7280'
                       END as couleur_timeline
                FROM journal j
                WHERE j.operation_id = ?
                AND (j.est_blocage = 1 OR j.niveau_urgence >= 3 OR j.type_action = 'VALIDATION')
                ORDER BY j.date_saisie DESC
                LIMIT 10
            """, (operation_id,))
            
            journal_timeline = [dict(row) for row in cursor.fetchall()]
            
            # Alertes actives pour timeline
            cursor = conn.execute("""
                SELECT a.*, 
                       CASE 
                           WHEN a.type_alerte = 'BLOCAGE' THEN '#dc2626'
                           WHEN a.type_alerte = 'RETARD' THEN '#f59e0b'
                           WHEN a.type_alerte = 'ATTENTION' THEN '#eab308'
                           ELSE '#3b82f6'
                       END as couleur_alerte
                FROM alertes a
                WHERE a.operation_id = ? AND a.est_traitee = FALSE AND a.visible_timeline = TRUE
                ORDER BY a.niveau_urgence DESC, a.date_creation DESC
            """, (operation_id,))
            
            alertes_timeline = [dict(row) for row in cursor.fetchall()]
            
            return {
                'phases': phases,
                'journal_entries': journal_timeline,
                'alertes': alertes_timeline,
                'domaines': config.DOMAINES_OPERATIONNELS
            }
            
        except Exception as e:
            print(f"❌ Erreur données timeline : {e}")
            return {'phases': [], 'journal_entries': [], 'alertes': []}
        finally:
            conn.close()
    
    def close(self):
        """Ferme proprement la base de données"""
        print("✅ DatabaseManager SPIC 2.0 Streamlit fermé")

# ============================================================================
# FONCTIONS UTILITAIRES GLOBALES
# ============================================================================

def get_db_instance():
    """Retourne une instance de DatabaseManager (pattern singleton pour Streamlit)"""
    if not hasattr(get_db_instance, '_instance'):
        get_db_instance._instance = DatabaseManager()
    return get_db_instance._instance

# Test de la classe
if __name__ == "__main__":
    # Test basique
    db = DatabaseManager()
    print("✅ Test DatabaseManager SPIC 2.0 Streamlit réussi")
    
    # Test des fonctions ACO
    print("\n🧪 Tests gestion ACO :")
    acos = db.get_acos_list()
    print(f"ACO configurés : {len(acos)}")
    
    # Test des KPI
    print("\n📊 Tests KPI :")
    kpis = db.get_kpi_data()
    print(f"KPI récupérés : {len(kpis)} indicateurs")
    
    # Test module REM
    print("\n💰 Tests module REM :")
    rem_summary = db.get_rem_portfolio_summary()
    if 'erreur' not in rem_summary:
        print(f"Portfolio REM : {rem_summary.get('rem_total', 0)} € annuel")
    
    # Statistiques base
    print("\n📈 Statistiques base :")
    stats = db.get_database_stats()
    for key, value in stats.items():
        if not key.startswith('alertes_'):
            print(f"  {key}: {value}")
    
    # Optimisation pour Streamlit
    db.optimize_for_streamlit()