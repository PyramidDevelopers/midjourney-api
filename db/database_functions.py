import sqlite3
from fastapi import UploadFile



con = sqlite3.connect("athena.db")
cur = con.cursor()

def InsertIntoPrompts(info) :

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS messages (
        msg_id VARCHAR(50) PRIMARY KEY,
        msg_hash VARCHAR(255) NOT NULL,
        msg_content TEXT,
        url VARCHAR(255),
        proxy_url VARCHAR(255)
    )
'''

# Execute the SQL statement to create the table
    cur.execute(create_table_query)

# Commit the changes and close the connection
    con.commit()

    insert_query = f"""
    INSERT OR IGNORE INTO messages (msg_id, msg_hash, msg_content, url, proxy_url)
    VALUES ('{info["message_id"]}', '{info["message_hash"]}', '{info["content"]}', '{info["url"]}', '{info["proxy_url"]}')
"""

    # Assuming 'cur' is your cursor object, you can execute the query
    cur.execute(insert_query)
    con.commit()



def GetRecords(table_name,msg_id):

    try:
        # Execute the query to fetch all records
        cur.execute(f"SELECT * FROM {table_name}")

        # Fetch all rows from the result set
        rows = cur.fetchall()

        print(rows)

        # Get the column names from the cursor description
        column_names = [description[0] for description in cur.description]

        # Create a list of dictionaries, where column names are used as keys
        result = [dict(zip(column_names, map(str, row))) for row in rows]

        if msg_id is not None and table_name == "messages" :
            for msg in result :
                print(msg["msg_id"])
                if int(msg["msg_id"]) == msg_id :
                    return msg
            
            return {"error" : "Message with that message_id does not exist"} 
                

        return result

    except sqlite3.OperationalError as e:
        # Handle the case where the table does not exist
        print(f"Error: {e}")
        return {"error" : "Table does not exist"}


def UploadBanner(file : UploadFile,username,user_id):

    try :
        cur.execute('''
        CREATE TABLE IF NOT EXISTS concept_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            template_name VARCHAR(255) NOT NULL,
            template_data BLOB NOT NULL
            )
        ''')

        cur.execute('''
                INSERT INTO concept_templates (username, user_id, template_name, template_data)
                VALUES (?, ?, ?, ?)
                ''', 
                (username, user_id, file.filename, file.file.read())
                )
    
        con.commit()
        return {"status" : "Success"}
    
    except sqlite3.OperationalError as e:
        # Handle the case where the table does not exist
        print(f"Error: {e}")

        return {"error" : e}