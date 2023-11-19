import hashlib
import time
from functools import wraps
from typing import Union

from fastapi import status
from fastapi.responses import JSONResponse

from exceptions import BannedPromptError
from lib.prompt import BANNED_PROMPT

PROMPT_PREFIX = "<#"
PROMPT_SUFFIX = "#>"
import openai
import os


openai.api_key = os.environ['OPENAI_API_KEY']


def check_banned(prompt: str):
    words = set(w.lower() for w in prompt.split())
    if len(words & BANNED_PROMPT) != 0:
        raise BannedPromptError(f"banned prompt: {prompt}")


def unique_id():
    """生成唯一的 10 位数字，作为任务 ID"""
    return int(hashlib.sha256(str(time.time()).encode("utf-8")).hexdigest(), 16) % 10**10


def prompt_handler(prompt: str, picurl: Union[str, None] = None):
    """
    拼接 Prompt 形如: <#1234567890#>a cute cat
    """
    check_banned(prompt)

    trigger_id = str(unique_id())

    if not picurl and prompt.startswith(("http://", "https://")):
        picurl, _, prompt = prompt.partition(" ")

    return trigger_id, f"{picurl+' ' if picurl else ''}{PROMPT_PREFIX}{trigger_id}{PROMPT_SUFFIX}{prompt}"

def concept_handler(concept_name: str, concept_info: str):
    trigger_id = str(unique_id())
    prompt = f"""
    Using the information provided below, please generate a concepts, context, and style for an advertisement campaign. Keep each section short, crisp and concise and yet take all of the information you can get.
    
    Provided information:
    {concept_info,concept_name}
    Stricly keep the prompt to less than 20 words. Only respond with the prompt and remove all instructions and other text
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
        "role":
        "system",
        "content":
        "You are an AI assistant capable of understanding the concept, context, and style for advertisement campaigns. Extract relevant information from the provided input."
        }, {
        "role": "user",
        "content": prompt
        }])
    generated_prompt= response.choices[0].message.content.strip()
    return trigger_id,generated_prompt

def generate_single_prompt(generated_prompt):
    trigger_id = str(unique_id())
    prompt = f"""
    Using the information in `` delimiter. Generate a prompt for the concepts, using context and style.
    `
    {generated_prompt}
    `
    Generate an image description prompt for the concepts, using context and style. Keep it in single line describe the lighting, the style of the image, the mood to the convey the concepts like you would describe to a artist or a professional photographer. 
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role":
            "system",
            "content":
            "You are an Image Generation assistant capable of generating image descriptions that include camera angles, settings, lighting, and tone. Keep each Prompt less than 100 characters"
        }, {
            "role": "user",
            "content": prompt
        }])
    prompt=response.choices[0].message.content.strip()
    return trigger_id,prompt

def generate_prompt_error_message(previous_message):
    trigger_id = str(unique_id())
    prompt = f"""
    Using the input command in `` delimiter. Process and reflect back to the user on what was understood as concept, context, and style in the previous message and how they can give better concept input.
    `
    {previous_message}
    `

    Give the feedback as if you are talking to a colleague.  Keep each section short, crisp, and concise and yet give all of the information you can.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "You are a concept requirement taking bot and feedback giving bot"
        }, {
            "role": "user",
            "content": prompt
        }])
    
    prompt=response.choices[0].message.content.strip()
    return trigger_id, prompt



def http_response(func):
    @wraps(func)
    async def router(*args, **kwargs):
        trigger_id, resp = await func(*args, **kwargs)
        if resp is not None:
            code, trigger_result = status.HTTP_200_OK, "success"
        else:
            code, trigger_result = status.HTTP_400_BAD_REQUEST, "fail"

        return JSONResponse(
            status_code=code,
            content={"trigger_id": trigger_id, "trigger_result": trigger_result}
        )

    return router
