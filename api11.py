import io
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse

app = FastAPI(title="CSV Analysis API")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "file_path": file_path}

@app.get("/analyze/")
async def analyze_csv(file_name: str = Query(..., description="Name of the uploaded file"),
                      column: str = Query(..., description="Column name to visualize")):
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {e}")

    if column not in df.columns:
        available_cols = ", ".join(df.columns)
        raise HTTPException(
            status_code=400,
            detail=f"Column '{column}' not found. Available columns: {available_cols}",
        )

    sns.set_style("darkgrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    counts = df[column].value_counts().reset_index()
    
    
    sns.barplot(data=counts, x=counts.columns[0], y="count")  # ✅ Fixed here
    
    plt.title(f"Bar plot of {column}")
    plt.xlabel(column)
    plt.ylabel("Frequency")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return StreamingResponse(buf, media_type="image/png")

