# ==========================================
# Connexion à la base de données PostgreSQL
# Module pour gérer les connexions à Supabase
# ==========================================

import psycopg2
from dotenv import load_dotenv
import os
import sys

# Trouver le chemin du .env (fonctionne avec PyInstaller et en développement)
if getattr(sys, 'frozen', False):
    # Quand packagé avec PyInstaller
    env_path = os.path.join(sys._MEIPASS, '.env')
else:
    # En développement
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

# Charger les variables d'environnement depuis .env
load_dotenv(env_path)

def connect_db():
    """
    Établit une connexion à la base de données PostgreSQL sur Supabase.
    
    Returns:
        Connection: Objet de connexion psycopg2 à la base de données
        
    Raises:
        psycopg2.Error: Si la connexion échoue
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'),
        sslmode=os.getenv('DB_SSLMODE')
    )

    return conn