import io
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="CSV & DataFrame Analysis API")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ 1️⃣ Upload CSV (Still supports file upload)
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "file_path": file_path}

# ✅ 2️⃣ Define Pydantic model to accept DataFrame as JSON
class DataFrameInput(BaseModel):
    data: List[Dict]  # Accepts a list of dictionary objects
    column: str       # Column name to visualize
    chart_type: str   # "histogram", "bar", or "heatmap"

# ✅ 3️⃣ Analyze CSV or DataFrame
@app.post("/analyze/")
async def analyze_csv_or_dataframe(df_input: DataFrameInput):
    try:
        # Convert JSON to Pandas DataFrame
        df = pd.DataFrame(df_input.data)

        # 🛑 Validate if the column exists
        if df_input.column not in df.columns:
            available_cols = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Column '{df_input.column}' not found. Available columns: {available_cols}",
            )

        # 📊 Select chart type
        sns.set_style("darkgrid")
        fig, ax = plt.subplots(figsize=(10, 6))

        if df_input.chart_type == "histogram":
            sns.histplot(df[df_input.column], kde=True, color="blue", ax=ax)
            plt.title(f"Histogram of {df_input.column}")
            plt.xlabel(df_input.column)
            plt.ylabel("Frequency")

        elif df_input.chart_type == "bar":
            sns.countplot(x=df_input.column, data=df, ax=ax)
            plt.title(f"Bar Chart of {df_input.column}")
            plt.xlabel(df_input.column)
            plt.ylabel("Count")

        elif df_input.chart_type == "heatmap":
            numeric_df = df.select_dtypes(include=['number'])  # Only numeric columns
            if numeric_df.shape[1] < 2:
                raise HTTPException(status_code=400, detail="Heatmap requires at least two numerical columns.")
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
            plt.title("Heatmap of Numerical Features")

        else:
            raise HTTPException(status_code=400, detail="Invalid chart type. Use 'histogram', 'bar', or 'heatmap'.")

        plt.tight_layout()

        # 🎨 Save and return the image
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing data: {e}")
