import io
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="CSV Analysis API")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 📌 Model for POST Body Request
class AnalysisRequest(BaseModel):
    file_name: str
    column: str
    chart_type: str  # "histogram", "bar", or "heatmap"

# 📌 1. Upload CSV File (POST Request)
@app.get("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "file_path": file_path}

# 📌 2. Analyze CSV (POST Request)
@app.post("/analyze/")
async def analyze_csv(request: AnalysisRequest):
    file_path = os.path.join(UPLOAD_FOLDER, request.file_name)

    # 🛑 Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {e}")

    # 📊 Create the visualization based on chart type
    sns.set_style("darkgrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    if request.chart_type == "histogram":
        if request.column not in df.columns:
            available_cols = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Column '{request.column}' not found. Available columns: {available_cols}",
            )
        sns.histplot(df[request.column], kde=True, color="blue", ax=ax)
        plt.title(f"Histogram of {request.column}")
        plt.xlabel(request.column)
        plt.ylabel("Frequency")

    elif request.chart_type == "bar":
        if request.column not in df.columns:
            available_cols = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Column '{request.column}' not found. Available columns: {available_cols}",
            )
        value_counts = df[request.column].value_counts()
        sns.barplot(x=value_counts.index, y=value_counts.values, ax=ax, palette="Blues_d")
        plt.title(f"Bar Chart of {request.column}")
        plt.xlabel(request.column)
        plt.ylabel("Count")
        plt.xticks(rotation=45)

    elif request.chart_type == "heatmap":
        # Heatmap does not need a specific column; it shows correlation of all numeric columns
        plt.figure(figsize=(12, 8))
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            raise HTTPException(status_code=400, detail="No numeric columns available for heatmap.")
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", linewidths=0.5)
        plt.title("Heatmap of Numerical Features")

    else:
        raise HTTPException(status_code=400, detail="Invalid chart_type. Use 'histogram', 'bar', or 'heatmap'.")

    # 🎨 Save and return the image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return StreamingResponse(buf, media_type="image/png")
