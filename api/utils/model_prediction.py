# from fastapi import FastAPI, Request
# import httpx
# import os

# app = FastAPI()

# API_URL = "https://api-inference.huggingface.co/models/your-username/distilbert-news-classifier-tf"
# HEADERS = {"Authorization": f"Bearer "+ os.getenv("HUGGINGFACE_API_TOKEN")}

# @app.post("/predict/")
# async def predict(request: Request):
#     data = await request.json()
#     text = data["text"]

#     async with httpx.AsyncClient() as client:
#         response = await client.post(API_URL, headers=HEADERS, json={"inputs": text})
    
#     result = response.json()
    
#     if "error" in result:
#         return {"error": result["error"]}
    
#     return {"prediction": result[0]['label']}



# from fastapi import FastAPI, Request
# import httpx

# app = FastAPI()

# API_URL = "https://api-inference.huggingface.co/models/your-username/roberta-twitter-sentiment-tf"
# HEADERS = {"Authorization": f"Bearer YOUR_HUGGINGFACE_API_TOKEN"}

# @app.post("/sentiment/")
# async def sentiment(request: Request):
#     body = await request.json()
#     text = body["text"]

#     async with httpx.AsyncClient() as client:
#         response = await client.post(API_URL, headers=HEADERS, json={"inputs": text})
    
#     result = response.json()

#     if "error" in result:
#         return {"error": result["error"]}

#     return {"sentiment": result[0]["label"]}
