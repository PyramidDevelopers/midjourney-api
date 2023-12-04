import os
from .handler import generate_response

async def get_help_text(role, question):
    help_folder = "help_texts"

    # Read basic help
    basic_help_path = os.path.join(help_folder, "basic_help.txt")
    basic_help_extended_path = os.path.join(help_folder, "basic_help_extended.txt")

    basic_help_content = read_file(basic_help_path)
    basic_help_extended_content = read_file(basic_help_extended_path)

    # Read role-specific help
    role_help_path = os.path.join(help_folder, f"{role}_help.txt")
    role_help_content = read_file(role_help_path) if os.path.exists(role_help_path) else ""

    # Combine the help texts
    combined_help = f"{basic_help_content}\n{basic_help_extended_content}\n{role_help_content}"

    # print("ques -->", question)
    # print('text -->', combined_help)
    
    trig_id, resp = generate_response(question, combined_help)
    return trig_id, resp

def read_file(file_path):
    # Helper function to read content from a file
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return ""
