from fastapi import FastAPI
import uvicorn

app = FastAPI()
counter = { "id": 1, "waste_type": "Metal", "status": "Collected" }

@app.get("/data")
def get_data():
    return counter

@app.post("/simulate_drop")
def drop():
    counter["id"] += 1
    return {"msg": "dropped"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
