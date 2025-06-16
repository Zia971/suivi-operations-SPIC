"""
Module de gestion de la base de données SQLite pour SPIC 2.0 - VERSION AMÉLIORÉE
Classe DatabaseManager avec gestion des alertes, blocages et statuts dynamiques
Intégration complète avec la logique journal → TOP 3 risques
"""

import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import config

class DatabaseManager:
    """Gestionnaire de base de données SQLite pour SPIC 2.0 avec alertes intelligentes"""
    
    def __init__(self, db_path: str = "spic.db"):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
        return conn
    
    def init_database(self):
        """Initialise les tables de la base de données avec structure améliorée"""
        conn = self.get_connection()
        try:
            # Table operations - Structure optimisée
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
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
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pourcentage_avancement REAL DEFAULT 0,
                    score_risque REAL DEFAULT 0,
                    has_active_blocage BOOLEAN DEFAULT FALSE,
                    derniere_alerte TEXT,
                    date_derniere_alerte TIMESTAMP
                )
            """)
            
            # Table phases - Enrichie avec gestion des blocages
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
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table journal - Enrichie pour gestion des alertes et blocages
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
                    impact_planning BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table alertes - Nouvelle table pour gestion avancée des alertes
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
                    operations_en_cours INTEGER DEFAULT 0
                )
            """)
            
            # Index optimisés pour performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations (type_operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_statut ON operations (statut_principal)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_aco ON operations (responsable_aco)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_risque ON operations (score_risque DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_blocage ON operations (has_active_blocage)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_operation ON phases (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_validee ON phases (est_validee)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_blocage ON phases (blocage_actif)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_ordre ON phases (operation_id, ordre_phase)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_operation ON journal (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal (date_saisie DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_blocage ON journal (est_blocage, est_resolu)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alertes_operation ON alertes (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alertes_urgence ON alertes (niveau_urgence DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alertes_actives ON alertes (est_traitee, date_creation)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_aco_actif ON configuration_aco (actif)")
            
            # Initialiser les ACO par défaut
            self._init_default_acos(conn)
            
            conn.commit()
            print("✅ Base de données SPIC 2.0 initialisée avec succès")
            
        except Exception as e:
            print(f"❌ Erreur initialisation base : {e}")
            conn.rollback()
        finally:
            conn.close()
    
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
    
    def create_operation(self, nom: str, type_operation: str, responsable_aco: str, 
                        commune: str = "", promoteur: str = "", nb_logements_total: int = 0,
                        nb_lls: int = 0, nb_llts: int = 0, nb_pls: int = 0, 
                        budget_total: float = 0.0) -> int:
        """Crée une nouvelle opération avec génération automatique des phases"""
        
        conn = self.get_connection()
        try:
            # Insertion de l'opération
            cursor = conn.execute("""
                INSERT INTO operations (
                    nom, type_operation, responsable_aco, commune, promoteur,
                    nb_logements_total, nb_lls, nb_llts, nb_pls, budget_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nom, type_operation, responsable_aco, commune, promoteur,
                  nb_logements_total, nb_lls, nb_llts, nb_pls, budget_total))
            
            operation_id = cursor.lastrowid
            
            # Génération automatique des phases selon le type
            self._generate_phases_for_operation(operation_id, type_operation, conn)
            
            # Ajout entrée journal de création
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu, niveau_urgence)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_id, "Système", "VALIDATION", f"Opération '{nom}' créée avec {len(config.get_phases_for_type(type_operation))} phases automatiques", 2))
            
            # Mise à jour compteur ACO
            conn.execute("""
                UPDATE configuration_aco 
                SET operations_en_cours = operations_en_cours + 1,
                    date_modification = CURRENT_TIMESTAMP
                WHERE nom_aco = ?
            """, (responsable_aco,))
            
            conn.commit()
            print(f"✅ Opération '{nom}' créée avec ID {operation_id}")
            return operation_id
            
        except Exception as e:
            print(f"❌ Erreur création opération : {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _generate_phases_for_operation(self, operation_id: int, type_operation: str, conn):
        """Génère les phases automatiquement selon le type d'opération avec gestion des couleurs"""
        
        try:
            phases_referentiel = config.get_phases_for_type(type_operation)
            print(f"DEBUG: Génération de {len(phases_referentiel)} phases pour {type_operation}")
            
            for ordre, phase in enumerate(phases_referentiel, 1):
                conn.execute("""
                    INSERT INTO phases (
                        operation_id, phase_principale, sous_phase, ordre_phase,
                        duree_mini_jours, duree_maxi_jours, responsable_principal,
                        responsable_validation, est_validee, couleur_statut
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    phase.get('phase_principale', ''),
                    phase.get('sous_phase', ''),
                    ordre,
                    phase.get('duree_mini_jours', 30),
                    phase.get('duree_maxi_jours', 60),
                    phase.get('responsable_principal', ''),
                    phase.get('responsable_validation', ''),
                    False,
                    '🟡'  # Couleur par défaut
                ))
            
            print(f"✅ {len(phases_referentiel)} phases générées pour l'opération {operation_id}")
            
        except Exception as e:
            print(f"❌ Erreur génération phases : {e}")
            raise
    
    def get_operations(self, responsable: str = None, type_op: str = None, 
                      statut: str = None, with_risk_score: bool = True) -> List[Dict]:
        """Récupère la liste des opérations avec calcul du score de risque"""
        
        conn = self.get_connection()
        try:
            query = "SELECT * FROM operations WHERE 1=1"
            params = []
            
            if responsable:
                query += " AND responsable_aco = ?"
                params.append(responsable)
            
            if type_op:
                query += " AND type_operation = ?"
                params.append(type_op)
            
            if statut:
                query += " AND statut_principal = ?"
                params.append(statut)
            
            query += " ORDER BY score_risque DESC, date_maj DESC"
            
            cursor = conn.execute(query, params)
            operations = [dict(row) for row in cursor.fetchall()]
            
            # Calcul du score de risque si demandé
            if with_risk_score:
                for operation in operations:
                    operation['score_risque'] = self._calculate_operation_risk_score(operation['id'], conn)
            
            return operations
            
        except Exception as e:
            print(f"❌ Erreur récupération opérations : {e}")
            return []
        finally:
            conn.close()
    
    def get_operation_detail(self, operation_id: int) -> Optional[Dict]:
        """Récupère les détails complets d'une opération avec alertes"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
            row = cursor.fetchone()
            
            if row:
                operation = dict(row)
                
                # Ajouter les alertes actives
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM alertes 
                    WHERE operation_id = ? AND est_traitee = FALSE
                """, (operation_id,))
                operation['alertes_actives'] = cursor.fetchone()[0]
                
                # Ajouter les blocages actifs
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM journal 
                    WHERE operation_id = ? AND est_blocage = TRUE AND est_resolu = FALSE
                """, (operation_id,))
                operation['blocages_actifs'] = cursor.fetchone()[0]
                
                return operation
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération détail opération : {e}")
            return None
        finally:
            conn.close()
    
    def get_phases_by_operation(self, operation_id: int) -> List[Dict]:
        """Récupère toutes les phases d'une opération avec couleurs mises à jour"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM phases 
                WHERE operation_id = ? 
                ORDER BY ordre_phase
            """, (operation_id,))
            
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
                    commentaire: str = None, blocage_actif: bool = None,
                    motif_blocage: str = None) -> bool:
        """Met à jour une phase avec gestion des blocages"""
        
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
            
            if commentaire is not None:
                updates.append("commentaire = ?")
                params.append(commentaire)
            
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
            
            # Si c'est un blocage, créer une alerte automatique
            if blocage_actif:
                # Récupérer l'operation_id
                cursor = conn.execute("SELECT operation_id, sous_phase FROM phases WHERE id = ?", (phase_id,))
                phase_info = cursor.fetchone()
                if phase_info:
                    self._create_automatic_alert(
                        phase_info['operation_id'], 
                        phase_id, 
                        'BLOCAGE', 
                        5, 
                        f"Blocage signalé sur phase: {phase_info['sous_phase']} - {motif_blocage or 'Motif non spécifié'}",
                        conn
                    )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour phase : {e}")
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
            
            # Mettre à jour l'opération
            conn.execute("""
                UPDATE operations 
                SET pourcentage_avancement = ?, 
                    statut_principal = ?,
                    score_risque = ?,
                    has_active_blocage = ?,
                    date_maj = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (pourcentage, nouveau_statut, score_risque, has_blocage, operation_id))
            
            conn.commit()
            
            print(f"✅ Opération {operation_id} mise à jour: {pourcentage:.1f}% - {nouveau_statut}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour opération : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_journal_entry(self, operation_id: int, auteur: str, type_action: str,
                         contenu: str, phase_concernee: str = None, 
                         est_blocage: bool = False, niveau_urgence: int = 1) -> bool:
        """Ajoute une entrée dans le journal avec gestion des blocages"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO journal (
                    operation_id, auteur, type_action, contenu, phase_concernee,
                    est_blocage, niveau_urgence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (operation_id, auteur, type_action, contenu, phase_concernee, est_blocage, niveau_urgence))
            
            journal_id = cursor.fetchone()[0]
            
            # Si c'est un blocage, créer une alerte automatique
            if est_blocage:
                alerte_level = 5 if type_action == "BLOCAGE" else min(5, niveau_urgence + 1)
                self._create_automatic_alert(
                    operation_id, 
                    None, 
                    'BLOCAGE' if type_action == "BLOCAGE" else 'ATTENTION',
                    alerte_level,
                    f"Blocage signalé: {contenu}",
                    conn,
                    journal_id
                )
                
                # Mettre à jour le statut de l'opération si blocage critique
                if type_action == "BLOCAGE":
                    conn.execute("""
                        UPDATE operations 
                        SET statut_principal = '🔴 Bloqué',
                            has_active_blocage = TRUE,
                            derniere_alerte = ?,
                            date_derniere_alerte = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (contenu, operation_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout journal : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_journal_by_operation(self, operation_id: int, include_resolved: bool = True) -> List[Dict]:
        """Récupère le journal d'une opération avec informations de blocage"""
        
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
                    date_resolution = CURRENT_TIMESTAMP
                WHERE id = ? AND est_blocage = TRUE
            """, (journal_id,))
            
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
    
    def get_operations_at_risk(self, limit: int = 3) -> List[Dict]:
        """Récupère le TOP des opérations à risque avec score détaillé"""
        
        conn = self.get_connection()
        try:
            # Récupérer toutes les opérations avec calcul de risque
            cursor = conn.execute("""
                SELECT o.*, 
                       (SELECT COUNT(*) FROM alertes a WHERE a.operation_id = o.id AND a.est_traitee = FALSE) as alertes_actives,
                       (SELECT COUNT(*) FROM journal j WHERE j.operation_id = o.id AND j.est_blocage = TRUE AND j.est_resolu = FALSE) as blocages_actifs
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
                
                if operation['has_active_blocage']:
                    raisons_risque.append("🔴 Blocage actif")
                
                if operation['pourcentage_avancement'] < 30 and '🚧 En travaux' in operation['statut_principal']:
                    raisons_risque.append("⚠️ Travaux peu avancés")
                
                if operation['alertes_actives'] > 0:
                    raisons_risque.append(f"🚨 {operation['alertes_actives']} alerte(s)")
                
                if operation['pourcentage_avancement'] == 0:
                    raisons_risque.append("📊 Aucun avancement")
                
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
            # Récupérer les données nécessaires
            cursor = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
            operation = cursor.fetchone()
            if not operation:
                return 0.0
            
            cursor = conn.execute("SELECT * FROM phases WHERE operation_id = ?", (operation_id,))
            phases = [dict(row) for row in cursor.fetchall()]
            
            cursor = conn.execute("""
                SELECT * FROM alertes 
                WHERE operation_id = ? AND est_traitee = FALSE
            """, (operation_id,))
            alertes = [dict(row) for row in cursor.fetchall()]
            
            # Utiliser la fonction de calcul de config.py
            score = config.calculate_risk_score(dict(operation), phases, alertes)
            
            return score
            
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
            cursor = conn.execute("SELECT AVG(pourcentage_avancement) as avg FROM operations")
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
            
            return {
                'total_operations': total_operations,
                'repartition_statuts': repartition_statuts,
                'repartition_types': repartition_types,
                'avancement_moyen': round(avancement_moyen, 1),
                'operations_bloquees': operations_bloquees,
                'alertes_actives': alertes_actives,
                'operations_en_retard': operations_en_retard,
                'nouvelles_operations_semaine': nouvelles_operations,
                'operations_cloturees_semaine': operations_cloturees
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération KPI : {e}")
            return {}
        finally:
            conn.close()
    
    # ============================================================================
    # GESTION DYNAMIQUE DES ACO
    # ============================================================================
    
    def get_acos_list(self, actifs_seulement: bool = True) -> List[Dict]:
        """Récupère la liste des ACO avec leurs statistiques"""
        
        conn = self.get_connection()
        try:
            query = """
                SELECT a.*, 
                       COUNT(o.id) as operations_actuelles,
                       COALESCE(AVG(o.pourcentage_avancement), 0) as avancement_moyen
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
        """Récupère les statistiques de la base de données"""
        
        conn = self.get_connection()
        try:
            stats = {}
            
            # Statistiques par table
            tables = ['operations', 'phases', 'journal', 'alertes', 'configuration_aco']
            
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"total_{table}"] = cursor.fetchone()[0]
            
            # Taille de la base
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['taille_db_mo'] = round((page_count * page_size) / (1024 * 1024), 2)
            
            # Dernière modification
            import os
            if os.path.exists(self.db_path):
                stats['derniere_modification'] = datetime.fromtimestamp(
                    os.path.getmtime(self.db_path)
                ).strftime('%d/%m/%Y %H:%M')
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur récupération statistiques : {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """Nettoie les anciennes données (alertes traitées, journal ancien)"""
        
        conn = self.get_connection()
        try:
            cutoff_date = datetime.now().date() - datetime.timedelta(days=days_to_keep)
            
            # Supprimer les alertes traitées anciennes
            cursor = conn.execute("""
                DELETE FROM alertes 
                WHERE est_traitee = TRUE 
                AND date_traitement < ?
            """, (cutoff_date,))
            alertes_supprimees = cursor.rowcount
            
            # Supprimer les entrées journal anciennes (sauf blocages)
            cursor = conn.execute("""
                DELETE FROM journal 
                WHERE date_saisie < ? 
                AND est_blocage = FALSE
                AND type_action = 'INFO'
            """, (cutoff_date,))
            journal_supprime = cursor.rowcount
            
            conn.commit()
            
            print(f"✅ Nettoyage effectué : {alertes_supprimees} alertes, {journal_supprime} entrées journal")
            return True
            
        except Exception as e:
            print(f"❌ Erreur nettoyage : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def close(self):
        """Ferme proprement la base de données"""
        print("✅ DatabaseManager SPIC 2.0 fermé")

# Test de la classe
if __name__ == "__main__":
    # Test basique
    db = DatabaseManager()
    print("✅ Test DatabaseManager SPIC 2.0 réussi")
    
    # Test des fonctions ACO
    print("\n🧪 Tests gestion ACO :")
    acos = db.get_acos_list()
    print(f"ACO configurés : {len(acos)}")
    
    # Test des KPI
    print("\n📊 Tests KPI :")
    kpis = db.get_kpi_data()
    print(f"KPI récupérés : {len(kpis)} indicateurs")
    
    # Statistiques base
    print("\n📈 Statistiques base :")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")