import os
import psycopg2
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Connection parameters for psycopg2
def get_db_connection():
    try:
        # Prioritize individual parameters for safer connection
        user = os.getenv("user")
        password = os.getenv("password")
        host = os.getenv("host")
        port = os.getenv("port")
        dbname = os.getenv("dbname")
        database_url = os.getenv("DATABASE_URL")

        if user and password and host:
            conn = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                dbname=dbname
            )
        elif database_url:
            conn = psycopg2.connect(database_url)
        else:
            raise ValueError("No database connection parameters found in .env")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return '<h1>Error</h1><p>Could not connect to the database.</p>'
    
    try:
        cur = conn.cursor()
        # Querying the 'todos' table via SQL instead of Supabase client
        cur.execute("SELECT name FROM todos;")
        todos = cur.fetchall()
        
        html = '<h1>Todos</h1><ul>'
        for todo in todos:
            html += f'<li>{todo[0]}</li>'
        html += '</ul>'
        
        cur.close()
        conn.close()
    except Exception as e:
        html = f'<h1>Error</h1><p>{str(e)}</p>'
    finally:
        if conn:
            conn.close()

    return html

if __name__ == '__main__':
    app.run(debug=True)
