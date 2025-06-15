"""
Module de gestion de la base de données SQLite pour SPIC
Classe DatabaseManager avec toutes les fonctions CRUD
"""

import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import config

class DatabaseManager:
    """Gestionnaire de base de données SQLite pour SPIC"""
    
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
        """Initialise les tables de la base de données"""
        conn = self.get_connection()
        try:
            # Table operations
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
                    pourcentage_avancement REAL DEFAULT 0
                )
            """)
            
            # Table phases
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
                    alerte_activee BOOLEAN NOT NULL DEFAULT TRUE,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table journal
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    date_saisie TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    auteur TEXT NOT NULL,
                    type_action TEXT NOT NULL DEFAULT 'INFO',
                    contenu TEXT NOT NULL,
                    phase_concernee TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table finances
            conn.execute("""
                CREATE TABLE IF NOT EXISTS finances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    type_mouvement TEXT NOT NULL CHECK (type_mouvement IN ('engagement', 'mandat', 'solde', 'revision', 'avenant')),
                    montant_ht REAL NOT NULL DEFAULT 0,
                    montant_ttc REAL DEFAULT 0,
                    date_mouvement DATE NOT NULL,
                    fournisseur_entreprise TEXT,
                    numero_facture TEXT,
                    commentaire TEXT,
                    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table fichiers
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fichiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    nom_fichier TEXT NOT NULL,
                    type_mime TEXT,
                    taille_bytes INTEGER DEFAULT 0,
                    contenu_base64 TEXT NOT NULL,
                    description TEXT,
                    categorie TEXT,
                    date_upload TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    uploade_par TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations (id)
                )
            """)
            
            # Table alertes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alertes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id INTEGER NOT NULL,
                    phase_id INTEGER,
                    type_alerte TEXT NOT NULL CHECK (type_alerte IN ('retard', 'blocage', 'validation_requise', 'deadline_proche')),
                    niveau_urgence INTEGER NOT NULL CHECK (niveau_urgence BETWEEN 1 AND 5) DEFAULT 3,
                    message TEXT NOT NULL,
                    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    date_echeance DATE,
                    est_traitee BOOLEAN NOT NULL DEFAULT FALSE,
                    date_traitement TIMESTAMP,
                    FOREIGN KEY (operation_id) REFERENCES operations (id),
                    FOREIGN KEY (phase_id) REFERENCES phases (id)
                )
            """)
            
            # Index pour les performances
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations (type_operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_statut ON operations (statut_principal)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operations_aco ON operations (responsable_aco)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_operation ON phases (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_phases_validee ON phases (est_validee)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_operation ON journal (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_finances_operation ON finances (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fichiers_operation ON fichiers (operation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alertes_operation ON alertes (operation_id)")
            
            conn.commit()
            print("✅ Base de données initialisée avec succès")
            
        except Exception as e:
            print(f"❌ Erreur initialisation base : {e}")
            conn.rollback()
        finally:
            conn.close()
    
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
            
            # Ajout entrée journal
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu)
                VALUES (?, ?, ?, ?)
            """, (operation_id, "Système", "CREATION", f"Opération '{nom}' créée"))
            
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
        """Génère les phases automatiquement selon le type d'opération"""
        
        try:
            phases_referentiel = config.get_phases_for_type(type_operation)
            
            for ordre, phase in enumerate(phases_referentiel, 1):
                # Conversion des durées texte en jours
                duree_mini = self._convert_duration_to_days(phase.get('Duree_Mini', ''))
                duree_maxi = self._convert_duration_to_days(phase.get('Duree_Maxi', ''))
                
                conn.execute("""
                    INSERT INTO phases (
                        operation_id, phase_principale, sous_phase, ordre_phase,
                        duree_mini_jours, duree_maxi_jours, responsable_principal,
                        responsable_validation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    phase.get('Phase_Principale', ''),
                    phase.get('Sous_Phase', ''),
                    ordre,
                    duree_mini,
                    duree_maxi,
                    phase.get('Responsable_Principal', ''),
                    phase.get('Responsable_Validation', '')
                ))
            
            print(f"✅ {len(phases_referentiel)} phases générées pour l'opération {operation_id}")
            
        except Exception as e:
            print(f"❌ Erreur génération phases : {e}")
            raise
    
    def _convert_duration_to_days(self, duration_text: str) -> Optional[int]:
        """Convertit un texte de durée en nombre de jours"""
        if not duration_text:
            return None
        
        try:
            # Extraction des nombres du texte
            if "semaine" in duration_text.lower():
                number = int(''.join(filter(str.isdigit, duration_text)))
                return number * 7
            elif "mois" in duration_text.lower():
                number = int(''.join(filter(str.isdigit, duration_text)))
                return number * 30
            elif "jour" in duration_text.lower():
                return int(''.join(filter(str.isdigit, duration_text)))
            else:
                # Tentative d'extraction directe du nombre
                return int(''.join(filter(str.isdigit, duration_text)))
        except:
            return None
    
    def get_operations(self, responsable: str = None, type_op: str = None, 
                      statut: str = None) -> List[Dict]:
        """Récupère la liste des opérations avec filtres optionnels"""
        
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
            
            query += " ORDER BY date_maj DESC"
            
            cursor = conn.execute(query, params)
            operations = [dict(row) for row in cursor.fetchall()]
            
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
            cursor = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération détail opération : {e}")
            return None
        finally:
            conn.close()
    
    def get_phases_by_operation(self, operation_id: int) -> List[Dict]:
        """Récupère toutes les phases d'une opération"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM phases 
                WHERE operation_id = ? 
                ORDER BY ordre_phase
            """, (operation_id,))
            
            phases = [dict(row) for row in cursor.fetchall()]
            return phases
            
        except Exception as e:
            print(f"❌ Erreur récupération phases : {e}")
            return []
        finally:
            conn.close()
    
    def update_phase(self, phase_id: int, est_validee: bool = None, 
                    date_debut_prevue: str = None, date_fin_prevue: str = None,
                    date_debut_reelle: str = None, date_fin_reelle: str = None,
                    commentaire: str = None) -> bool:
        """Met à jour une phase"""
        
        conn = self.get_connection()
        try:
            # Construction dynamique de la requête
            updates = []
            params = []
            
            if est_validee is not None:
                updates.append("est_validee = ?")
                params.append(est_validee)
            
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
            
            if not updates:
                return True
            
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
    
    def update_operation_progress(self, operation_id: int, pourcentage: float) -> bool:
        """Met à jour le pourcentage d'avancement d'une opération"""
        
        conn = self.get_connection()
        try:
            conn.execute("""
                UPDATE operations 
                SET pourcentage_avancement = ?, date_maj = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (pourcentage, operation_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour avancement : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_journal_entry(self, operation_id: int, auteur: str, type_action: str,
                         contenu: str, phase_concernee: str = None) -> bool:
        """Ajoute une entrée dans le journal"""
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO journal (operation_id, auteur, type_action, contenu, phase_concernee)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_id, auteur, type_action, contenu, phase_concernee))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout journal : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_journal_by_operation(self, operation_id: int) -> List[Dict]:
        """Récupère le journal d'une opération"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM journal 
                WHERE operation_id = ? 
                ORDER BY date_saisie DESC
            """, (operation_id,))
            
            journal = [dict(row) for row in cursor.fetchall()]
            return journal
            
        except Exception as e:
            print(f"❌ Erreur récupération journal : {e}")
            return []
        finally:
            conn.close()
    
    def add_finance_entry(self, operation_id: int, type_mouvement: str, montant_ht: float,
                         montant_ttc: float = None, date_mouvement: str = None,
                         fournisseur_entreprise: str = None, numero_facture: str = None,
                         commentaire: str = None) -> bool:
        """Ajoute un mouvement financier"""
        
        conn = self.get_connection()
        try:
            if date_mouvement is None:
                date_mouvement = datetime.now().date().isoformat()
            
            if montant_ttc is None:
                montant_ttc = montant_ht * 1.20  # TVA 20% par défaut
            
            conn.execute("""
                INSERT INTO finances (
                    operation_id, type_mouvement, montant_ht, montant_ttc,
                    date_mouvement, fournisseur_entreprise, numero_facture, commentaire
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (operation_id, type_mouvement, montant_ht, montant_ttc,
                  date_mouvement, fournisseur_entreprise, numero_facture, commentaire))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout finance : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_finances_by_operation(self, operation_id: int) -> List[Dict]:
        """Récupère les mouvements financiers d'une opération"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM finances 
                WHERE operation_id = ? 
                ORDER BY date_mouvement DESC
            """, (operation_id,))
            
            finances = [dict(row) for row in cursor.fetchall()]
            return finances
            
        except Exception as e:
            print(f"❌ Erreur récupération finances : {e}")
            return []
        finally:
            conn.close()
    
    def add_file(self, operation_id: int, nom_fichier: str, contenu_base64: str,
                type_mime: str = None, taille_bytes: int = 0, categorie: str = None,
                description: str = None, uploade_par: str = None) -> bool:
        """Ajoute un fichier"""
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO fichiers (
                    operation_id, nom_fichier, contenu_base64, type_mime,
                    taille_bytes, categorie, description, uploade_par
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (operation_id, nom_fichier, contenu_base64, type_mime,
                  taille_bytes, categorie, description, uploade_par))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout fichier : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_files_by_operation(self, operation_id: int) -> List[Dict]:
        """Récupère les fichiers d'une opération"""
        
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM fichiers 
                WHERE operation_id = ? 
                ORDER BY date_upload DESC
            """, (operation_id,))
            
            fichiers = [dict(row) for row in cursor.fetchall()]
            return fichiers
            
        except Exception as e:
            print(f"❌ Erreur récupération fichiers : {e}")
            return []
        finally:
            conn.close()
    
    def add_alert(self, operation_id: int, phase_id: int = None, type_alerte: str = "retard",
                 niveau_urgence: int = 3, message: str = "", date_echeance: str = None) -> bool:
        """Ajoute une alerte"""
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO alertes (
                    operation_id, phase_id, type_alerte, niveau_urgence,
                    message, date_echeance
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (operation_id, phase_id, type_alerte, niveau_urgence, message, date_echeance))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout alerte : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_alerts_by_operation(self, operation_id: int, non_traitees_seulement: bool = True) -> List[Dict]:
        """Récupère les alertes d'une opération"""
        
        conn = self.get_connection()
        try:
            query = "SELECT * FROM alertes WHERE operation_id = ?"
            params = [operation_id]
            
            if non_traitees_seulement:
                query += " AND est_traitee = FALSE"
            
            query += " ORDER BY niveau_urgence DESC, date_creation DESC"
            
            cursor = conn.execute(query, params)
            alertes = [dict(row) for row in cursor.fetchall()]
            return alertes
            
        except Exception as e:
            print(f"❌ Erreur récupération alertes : {e}")
            return []
        finally:
            conn.close()
    
    def get_kpi_data(self) -> Dict:
        """Récupère les données KPI pour le tableau de bord manager"""
        
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
            
            # Opérations en retard (exemple)
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM operations 
                WHERE statut_principal LIKE '%Bloqué%'
            """)
            operations_bloquees = cursor.fetchone()[0]
            
            return {
                'total_operations': total_operations,
                'repartition_statuts': repartition_statuts,
                'repartition_types': repartition_types,
                'avancement_moyen': avancement_moyen,
                'operations_bloquees': operations_bloquees
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération KPI : {e}")
            return {}
        finally:
            conn.close()
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Sauvegarde la base de données"""
        
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
    
    def close(self):
        """Ferme proprement la base de données"""
        print("✅ DatabaseManager fermé")

# Test de la classe
if __name__ == "__main__":
    # Test basique
    db = DatabaseManager()
    print("✅ Test DatabaseManager réussi")
    
    