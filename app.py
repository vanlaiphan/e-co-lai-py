import io
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import base64
import uvicorn

from api import outfit_swap

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class OutfitSwapItem(BaseModel):
    url_image_human: str
    url_image_outfit: str
    user_prompt: str

@app.get("/")
async def hello():
    return {"message": "Lai's API Services => Hello!"}


@app.post("/outfit_swap")
@app.post("/outfit_swap/")
async def outfit_swap_(item: OutfitSwapItem):
    loop = asyncio.get_event_loop()
    print(f"Received request with: {item.url_image_human}, {item.url_image_outfit}, {item.user_prompt}")
    images = await loop.run_in_executor(None, outfit_swap.swap, item.url_image_human, item.url_image_outfit, item.user_prompt)

    image_results = []

    for image in images:
        with io.BytesIO() as output:
            image.save(output, format="JPEG")
            image_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
            image_results.append({"image": image_base64})

    return image_results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7077)
