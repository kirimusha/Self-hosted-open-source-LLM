import httpx
import os

LLM_URL = os.getenv("LLM_URL", "http://llm_server:8080/completion")

async def call_llm(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                LLM_URL,
                json={
                    "prompt": prompt,
                    "n_predict": 2000,
                    "temperature": 0.3,
                    "stop": ["\n\n\n"]
                }
            )
            
            if response.status_code == 200:
                return response.json().get("content", "").strip()
            else:
                return f"Error: LLM returned {response.status_code}"
        except Exception as e:
            return f"Error calling LLM: {str(e)}"