from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Optional

app = FastAPI()

# ✅ Enable CORS (any origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load CSV
df = pd.read_csv("q-fastapi.csv")

@app.get("/api")
def get_students(class_: Optional[List[str]] = Query(None, alias="class")):
    data = df

    if class_:
        data = data[data["class"].isin(class_)]

    students = data.to_dict(orient="records")

    return {"students": students}
