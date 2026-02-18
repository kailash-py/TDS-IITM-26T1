# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn",
#   "pandas"
# ]
# ///

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Dict, Union

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Load CSV once at startup
df = pd.read_csv("q-fastapi.csv")

@app.get("/api")
async def get_students(classes: List[str] = Query(default=None)) -> Dict[str, List[Dict[str, Union[str, int]]]]:
    if classes:
        filtered = df[df["class"].isin(classes)]
    else:
        filtered = df
    students = filtered.to_dict(orient="records")
    return {"students": students}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
