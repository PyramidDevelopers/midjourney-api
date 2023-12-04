from app.db.database import DatabaseConnection
from fastapi import UploadFile

def InsertIntoPrompts(info, connection):
    with connection.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                msg_id VARCHAR(50) PRIMARY KEY,
                msg_hash VARCHAR(255) NOT NULL,
                msg_content TEXT,
                url VARCHAR(999),
                proxy_url VARCHAR(999)
            )
        ''')

        insert_query = '''
            INSERT INTO messages (msg_id, msg_hash, msg_content, url, proxy_url)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (msg_id) DO NOTHING
        '''
        cur.execute(insert_query, (info["message_id"], info["message_hash"], info["content"], info["url"], info["proxy_url"]))
        connection.commit()

def GetRecords(table_name, msg_id=None, trigger_id=None, connection=None):
    with connection.cursor() as cur:
        try:
            query = f"SELECT * FROM {table_name}"
            conditions = []

            if msg_id is not None:
                conditions.append("msg_id = CAST(%s AS VARCHAR)")
            if trigger_id is not None:
                conditions.append("msg_content LIKE %s")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Pass the correct number of parameters to the execute method
            params = (msg_id, ) if msg_id is not None else ()
            params += (f"%{trigger_id}%", ) if trigger_id is not None else ()
            
            cur.execute(query, params)
            
            rows = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            result = [dict(zip(column_names, row)) for row in rows]
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

def UploadBanner(file: UploadFile, username, user_id, connection):
    with connection.cursor() as cur:
        try:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS concept_templates (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    template_name VARCHAR(255) NOT NULL,
                    template_data BYTEA NOT NULL
                )
            ''')
            insert_query = '''
                INSERT INTO concept_templates (username, user_id, template_name, template_data)
                VALUES (%s, %s, %s, %s)
            '''
            cur.execute(insert_query, (username, user_id, file.filename, file.file.read()))
            connection.commit()
            return {"status": "Success"}
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

# Example Usage
db_connection = DatabaseConnection(secret_name="prod/AthenaAI/postgres")
connection = db_connection.connection
if connection:
    # Use the functions with the connection
    # Example: InsertIntoPrompts(info, connection)
    # Don't forget to close the connection when done
    db_connection.close_connection()
