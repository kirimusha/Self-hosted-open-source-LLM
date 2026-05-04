from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from llama_cpp import Llama
import os
import json

app = FastAPI()

MODEL_PATH = os.getenv("MODEL_PATH", "/models/tinyllama.Q4_K_M.gguf")

# Загружаем модель при старте (один раз)
print(f"Loading model from {MODEL_PATH}...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,              # уменьшите контекст для экономии памяти
    n_threads=4,             # количество потоков CPU
    n_gpu_layers=0,          # 0 = только CPU
    verbose=True             # включите отладку
)
print("Model loaded!")

class CompletionRequest(BaseModel):
    prompt: str
    n_predict: int = 2000
    temperature: float = 0.3
    stop: Optional[List[str]] = []

@app.post("/completion")
async def completion(request: CompletionRequest):
    try:
        output = llm(
            request.prompt,
            max_tokens=request.n_predict,
            temperature=request.temperature,
            stop=request.stop if request.stop else None,
            echo=False
        )
        return {"content": output["choices"][0]["text"].strip()}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)