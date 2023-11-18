import sqlite3

con = sqlite3.connect("athena.db")
cur = con.cursor()

def InsertIntoPrompts(info) :

    insert_query = f"""
    INSERT OR IGNORE INTO view_prompts (msg_id, msg_hash, msg_content, url, proxy_url)
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

        if msg_id is not None and table_name == "view_prompts" :
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

