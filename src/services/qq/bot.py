import os
import logging
import random
import httpx
import asyncio

import botpy
from botpy.message import Message, C2CMessage
from botpy.types.message import MarkdownPayload

import dotenv
dotenv.load_dotenv()


logger = logging.getLogger(__name__)

class QQBot(botpy.Client):
    def __init__(
        self, 
        intents: botpy.Intents,
    ):
        super().__init__(intents=intents)
        
    async def on_c2c_message_create(self, message: C2CMessage):
        logger.info(f"收到用户私信: {message.author.user_openid} {message.content}")
        random_seq = random.randint(1, 1000000)
        # 单聊专用的 post_c2c_message
        #http://localhost:8000/api/v1/ask
        # 发送请求到后端
        timeout_retries = int(os.getenv("TIMEOUT_RETRIES", 3))
        for i in range(timeout_retries):
            content= await self.ollama_response(message.content) 
            logger.info(f"请求第{i+1}次，返回内容: {content}")
            if content:
                break
            await asyncio.sleep(1)
        else:
            content = "请求超时，请稍后重试"
        try:
            await self.api.post_c2c_message(
                openid=message.author.user_openid,  
                msg_type=2,                     
                msg_id=message.id, 
                # msg_seq=random_seq,           
                markdown= MarkdownPayload(content=content)
            )
        except Exception as e:
            logger.error(f"Error posting response: {e}", exc_info=True)

    async def ollama_response(self, query: str):
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(
                    "http://host.docker.internal:8000/api/v1/ask-agentic",
                    json={"query": query,"top_k": 10},
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}", exc_info=True)
            return
        return response.json()['answer']