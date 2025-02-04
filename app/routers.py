from fastapi import APIRouter, UploadFile, HTTPException, status, Request, Form
import requests
from fastapi import HTTPException
import openai
import os


openai.api_key = os.environ['OPENAI_API_KEY']



from lib.api import discord
from lib.api.discord import TriggerType
from util._queue import taskqueue
from .handler import prompt_handler, concept_handler, generate_single_prompt, unique_id, generate_prompt_error_message
from .get_role_response import get_help_text
from .schema import (
    TriggerExpandIn,
    TriggerImagineIn,
    TriggerConcept,
    TriggerUVIn,
    TriggerResetIn,
    QueueReleaseIn,
    TriggerResponse,
    PromptResponse,
    PromptErrorMsgIn,
    PromptErrorMsgInResponse,
    GenerateResponseIn,
    GenerateResponseOut,
    TriggerZoomOutIn,
    UploadResponse,
    TriggerDescribeIn,
    SendMessageResponse,
    SendMessageIn,
    MessageBody,
    TableBody,
    UploadBody
)

from .get_messages import Retrieve_Messages

from db.database_functions import InsertIntoPrompts,GetRecords, UploadBanner
from db.database import DatabaseConnection

router = APIRouter()


# Assuming you have a PostgreSQL database connection details
DB_SECRET_NAME = "prod/AthenaAI/postgres"

# Function to create the prompts table in PostgreSQL
def create_prompts_table():
    db_connection = DatabaseConnection(DB_SECRET_NAME)
    connection = db_connection.connection
    if connection:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_prompts (
                id SERIAL PRIMARY KEY,
                concept_name TEXT,
                trigger_id TEXT,
                prompt_id TEXT,
                prompt_text TEXT
            )
        ''')
        connection.commit()
        cursor.close()
        db_connection.close_connection()

# Function to insert prompts into the PostgreSQL database
def insert_prompts(concept_name, trigger_id, prompts):
    db_connection = DatabaseConnection(DB_SECRET_NAME)
    connection = db_connection.connection
    if connection:
        cursor = connection.cursor()
        for prompt in prompts:
            cursor.execute('''
                INSERT INTO concept_prompts (concept_name, trigger_id, prompt_id, prompt_text)
                VALUES (%s, %s, %s, %s)
            ''', (concept_name, trigger_id, prompt['prompt_id'], prompt['prompt_text']))

        connection.commit()
        cursor.close()
        db_connection.close_connection()

@router.post("/understanding_concepts", response_model=TriggerResponse)
async def concept(body: TriggerConcept):
    trigger_id, gen_prompt = concept_handler(body.concept_name, body.concept_info)
    trigger_type = TriggerType.generate.value

    taskqueue.put(trigger_id, discord.generate, gen_prompt)
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}



@router.post("/generate_prompts", response_model=PromptResponse)
async def prompt(body: TriggerConcept):
    trigger_id, gen_prompt = concept_handler(body.concept_name, body.concept_info)
    
    additional_prompts = []
    for i in range(3):
        additional_prompt = generate_single_prompt(gen_prompt)
        
        additional_prompts.append({
            "prompt_id": additional_prompt[0],
            "prompt_text": additional_prompt[1],
        })

    # Use the generate_prompts function to send all prompts in one call
    #taskqueue.put(trigger_id, discord.generate_prompts, additional_prompts)
    # Generate the three additional prompts
    # prompt_1 = generate_single_prompt(gen_prompt)
    # prompt_2 = generate_single_prompt(gen_prompt)
    # prompt_3 = generate_single_prompt(gen_prompt)

    for prompt in additional_prompts:
            taskqueue.put(trigger_id, discord.generate_prompts, [prompt])
    
    create_prompts_table()
    insert_prompts(body.concept_name,trigger_id, additional_prompts)
    
    # Return the additional prompts and their trigger IDs
    return {
        "trigger_id": trigger_id,
        "trigger_type": TriggerType.generate.value,
        "additional_prompts": additional_prompts,
    }


@router.post("/generate_prompt_error_message", response_model=PromptErrorMsgInResponse)
async def prompt_error_msg(body: PromptErrorMsgIn):
    trigger_id, prompt_res = generate_prompt_error_message(body.prev_msg)
    taskqueue.put(trigger_id, discord.generate_prompt_error_message, prompt_res)
    return {
        "trigger_id": trigger_id,
        "trigger_type": TriggerType.generate.value,
        "prompt": prompt_res
    }
# {
#   "prev_msg": "Capture a thrilling shot of an Assassin's Creed character in a high-stakes cooking competition, utilizing dynamic lighting, intense camera angles, and vivid colors to convey competitiveness and innovation."
# }

@router.post("/generate_response", response_model=GenerateResponseOut)
async def generate_response(body: GenerateResponseIn):
    response_result = await get_help_text(body.role, body.question)
    trigger_id, reply = response_result
    taskqueue.put(trigger_id, discord.generate_response, body.question, reply)
    return{
        "trigger_id": trigger_id,
        "trigger_type": TriggerType.generate.value,
        "reply": reply
    }

# Function to alter prompts in the PostgreSQL database
def alter_prompt(concept_name, instructions):
    db_connection = DatabaseConnection(DB_SECRET_NAME)
    connection = db_connection.connection
    if connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT * FROM concept_prompts
            WHERE concept_name = ?
        ''', (concept_name,))
        prompts = cursor.fetchall()
        if not prompts:
            cursor.close()
            db_connection.close_connection()
            raise HTTPException(status_code=404, detail=f"No prompts found for concept_name: {concept_name}")

        altered_prompts = []
        for prompt in prompts:
            # Assuming the prompt_text is at the fifth position in the tuple
            mj_prompt = prompt[4]
            altered_prompt = f"""
            Use the instructions provided below in delimiter [], to edit the image prompt in delimiter <>

            instructions:
            [{instructions}]

            image prompt:
            <{mj_prompt}>
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are an AI assistant capable of editing / modifying an image description according to given instructions"
                }, {
                    "role": "user",
                    "content": altered_prompt
                }])
            altered_content = response.choices[0].message.content.strip()
            altered_prompts.append({"prompt_id": prompt[2], "prompt_text": altered_content})

            # Update the prompt in the database
            cursor.execute('''
                UPDATE concept_prompts
                SET prompt_text = ?
                WHERE id = ?
            ''', (altered_content, prompt[0]))

        cursor.close()
        db_connection.close_connection()
        return altered_prompts

@router.post("/alter_prompts",response_model=list[dict])
async def concept(concept_name: str, instructions: str):
    altered_prompts = alter_prompt(concept_name=concept_name,instructions=instructions)

    # Use the first altered prompt to generate an image
    trigger_id = str(unique_id())
    taskqueue.put(trigger_id, discord.generate_prompts, altered_prompts[0])

    return altered_prompts





@router.post("/imagine", response_model=TriggerResponse)
async def imagine(body: TriggerImagineIn):
    trigger_id, prompt = prompt_handler(body.prompt, body.extra, body.picurl)
    trigger_type = TriggerType.generate.value

    taskqueue.put(trigger_id, discord.generate, prompt)

    return {"trigger_id": trigger_id, "trigger_type": trigger_type, "prompt" : body.prompt}


@router.post("/upscale", response_model=TriggerResponse)
async def upscale(body: TriggerUVIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.upscale.value

    taskqueue.put(trigger_id, discord.upscale, **body.dict())
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}


@router.post("/variation", response_model=TriggerResponse)
async def variation(body: TriggerUVIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.variation.value

    taskqueue.put(trigger_id, discord.variation, **body.dict())
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}


@router.post("/reset", response_model=TriggerResponse)
async def reset(body: TriggerResetIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.reset.value

    taskqueue.put(trigger_id, discord.reset, **body.dict())
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}


@router.post("/describe", response_model=TriggerResponse)
async def describe(body: TriggerDescribeIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.describe.value

    taskqueue.put(trigger_id, discord.describe, **body.dict())
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}


@router.post("/upload", response_model=UploadResponse)
async def upload_attachment(file: UploadFile):
    if not file.content_type.startswith("image/"):
        return {"message": "must image"}

    trigger_id = str(unique_id())
    filename = f"{trigger_id}.jpg"
    file_size = file.size
    attachment = await discord.upload_attachment(filename, file_size, await file.read())
    if not (attachment and attachment.get("upload_url")):
        return {"message": "Failed to upload image"}

    return {
        "upload_filename": attachment.get("upload_filename"),
        "upload_url": attachment.get("upload_url"),
        "trigger_id": trigger_id,
    }


@router.post("/message", response_model=SendMessageResponse)
async def send_message(body: SendMessageIn):
    picurl = await discord.send_attachment_message(body.upload_filename)
    if not picurl:
        return {"message": "Failed to send message"}

    return {"picurl": picurl}


@router.post("/queue/release", response_model=TriggerResponse)
async def queue_release(body: QueueReleaseIn):
    """bot 清除队列任务"""
    taskqueue.pop(body.trigger_id)

    return body


@router.post("/solo_variation", response_model=TriggerResponse)
async def solo_variation(body: TriggerUVIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_variation.value
    taskqueue.put(trigger_id, discord.solo_variation, **body.dict())

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}

@router.post("/solo_low_variation", response_model=TriggerResponse)
async def solo_low_variation(body: TriggerUVIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_low_variation.value
    taskqueue.put(trigger_id, discord.solo_low_variation, **body.dict())

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}

@router.post("/solo_high_variation", response_model=TriggerResponse)
async def solo_high_variation(body: TriggerUVIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.solo_high_variation.value
    taskqueue.put(trigger_id, discord.solo_high_variation, **body.dict())

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}

@router.post("/expand", response_model=TriggerResponse)
async def expand(body: TriggerExpandIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.expand.value
    taskqueue.put(trigger_id, discord.expand, **body.dict())

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}


@router.post("/zoomout", response_model=TriggerResponse)
async def zoomout(body: TriggerZoomOutIn):
    trigger_id = body.trigger_id
    trigger_type = TriggerType.zoomout.value
    taskqueue.put(trigger_id, discord.zoomout, **body.dict())

    # 返回结果
    return {"trigger_id": trigger_id, "trigger_type": trigger_type}

@router.post("/view_concepts",response_model=list[dict])
# Function to view concepts from the PostgreSQL database
def view_concepts(concept_name):
    db_connection = DatabaseConnection(DB_SECRET_NAME)
    connection = db_connection.connection
    if connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT * FROM concept_prompts
            WHERE concept_name = %s
        ''', (concept_name,))
        prompts = cursor.fetchall()
        cursor.close()
        db_connection.close_connection()
        if not prompts:
            raise HTTPException(status_code=404, detail="No prompts found for concept_name")
        
        return [{"prompt_id": prompt[2], "prompt_text": prompt[4]} for prompt in prompts]







@router.post("/get_message")
async def get_message(body: MessageBody):
    try:
        # Create a database connection
        db_connection = DatabaseConnection(secret_name="prod/AthenaAI/postgres")
        connection = db_connection.connection

        # Retrieve messages
        data = await Retrieve_Messages(body.trigger_id)
        
        if "error" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data["error"],
            )

        # Insert data into the database
        InsertIntoPrompts(data, connection)

        return data

    finally:
        # Ensure that the database connection is closed, even in case of an exception
        db_connection.close_connection()





@router.post("/view_messages")
async def view_messages(msg_id: int = None, trigger_id: str = None):
    try:
        # Create a database connection
        db_connection = DatabaseConnection(secret_name="prod/AthenaAI/postgres")
        connection = db_connection.connection

        # Get records from the "messages" table with optional msg_id and trigger_id
        data = GetRecords("messages", msg_id=msg_id, trigger_id=trigger_id, connection=connection)

        if "error" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data["error"],
            )

        return data

    finally:
        # Ensure that the database connection is closed, even in case of an exception
        db_connection.close_connection()

@router.post("/upload_concept_template")
async def upload_concept_template(template: UploadFile,
    username: str = Form(...),
    user_id: str = Form(...)):

    data =  UploadBanner(template,username,user_id)

    
    if "error" in data :
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=data["error"],
    )

    return {"filename": template.filename, "status" : "success"}