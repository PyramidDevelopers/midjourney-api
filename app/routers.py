from fastapi import APIRouter, UploadFile, HTTPException, status
import requests
import sqlite3
from fastapi import HTTPException
import openai
import os


openai.api_key = os.environ['OPENAI_API_KEY']



from lib.api import discord
from lib.api.discord import TriggerType
from util._queue import taskqueue
from .handler import prompt_handler, concept_handler,generate_single_prompt, unique_id
from .schema import (
    TriggerExpandIn,
    TriggerImagineIn,
    TriggerConcept,
    TriggerUVIn,
    TriggerResetIn,
    QueueReleaseIn,
    TriggerResponse,
    PromptResponse,
    TriggerZoomOutIn,
    UploadResponse,
    TriggerDescribeIn,
    SendMessageResponse,
    SendMessageIn,
    MessageBody,
    TableBody
)

from .get_messages import Retrieve_Messages

from db.database_functions import InsertIntoPrompts,GetRecords


router = APIRouter()

# Assuming you have a SQLite database file named "prompts.db"
DB_FILE = "athena.db"

# Function to create the prompts table
def create_prompts_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concept_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_name TEXT,
            trigger_id TEXT,
            prompt_id TEXT,
            prompt_text TEXT
        )
    ''')
    conn.commit()
    conn.close()
# Function to insert prompts into the database
def insert_prompts(concept_name,trigger_id, prompts):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for prompt in prompts:
        cursor.execute('''
            INSERT INTO concept_prompts (concept_name, trigger_id, prompt_id, prompt_text)
            VALUES (?,?, ?, ?)
        ''', (concept_name, trigger_id, prompt['prompt_id'], prompt['prompt_text']))

    conn.commit()

    conn.close()


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


def alter_prompt(concept_name, instructions):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Retrieve prompts for the given concept_name
    cursor.execute('''
        SELECT * FROM concept_prompts
        WHERE concept_name = ?
    ''', (concept_name,))

    prompts = cursor.fetchall()

    # Check if prompts were found
    if not prompts:
        conn.close()
        raise HTTPException(status_code=404, detail=f"No prompts found for the given concept_name: {concept_name}")

    altered_prompts = []
    for prompt in prompts:
        mj_prompt = prompt[4]  # Assuming the prompt_text is at the fifth position in the table
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
                "role":
                "system",
                "content":
                "You are an AI assistant capable of editing / modifying an image description according to given instructions"
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

    conn.commit()
    conn.close()

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
    trigger_id, prompt = prompt_handler(body.prompt, body.picurl)
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
async def view_concepts(concept_name: str):
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Retrieve prompts for the given concept_name
    cursor.execute('''
        SELECT * FROM concept_prompts
        WHERE concept_name = ?
    ''', (concept_name,))

    prompts = cursor.fetchall()

    conn.close()

    # Check if prompts were found
    if not prompts:
        raise HTTPException(status_code=404, detail="No prompts found for the given concept_name")

    prompts_list = [{"prompt_id": prompt[2], "prompt_text": prompt[4]} for prompt in prompts]

    return prompts_list





@router.post("/get_message")
async def get_message(body: MessageBody):
    data = await Retrieve_Messages(body.trigger_id)
    if "error" in data :
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=data["error"],
    )
    InsertIntoPrompts(data)
    return data


@router.post("/view_messages")
async def view_messages(body: TableBody):
    data = GetRecords(body.data_type, body.msg_id)
    if "error" in data :
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=data["error"],
    )

    return data