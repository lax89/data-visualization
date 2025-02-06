import io
import os
import zipfile
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI(title="CSV Analysis API")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    """Uploads CSV file and saves it to the server."""
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "file_path": file_path}

@app.get("/analyze/")
async def analyze_csv(
    file_name: str = Query(..., description="Name of the uploaded file"),
    column: str = Query(None, description="Column name to visualize (except for heatmap)"),
    plot_types: str = Query("bar", description="Comma-separated list of plot types: bar, line, histogram, heatmap"),
    title: str = Query(None, description="Custom title for the chart"),
    xlabel: str = Query(None, description="Label for the X-axis"),
    ylabel: str = Query(None, description="Label for the Y-axis"),
    color: str = Query("blue", description="Color for the plot"),
    style: str = Query("darkgrid", description="Seaborn style (darkgrid, whitegrid, dark, white, ticks)")
):
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {e}")

    # Convert plot_types from string to list
    plot_types = plot_types.lower().split(",")
    valid_plots = {"bar", "line", "histogram", "heatmap"}
    requested_plots = set(plot_types)

    if not requested_plots.issubset(valid_plots):
        invalid = requested_plots - valid_plots
        raise HTTPException(status_code=400, detail=f"Invalid plot types: {', '.join(invalid)}. Choose from: {', '.join(valid_plots)}")

    if "heatmap" not in requested_plots and column is None:
        raise HTTPException(status_code=400, detail="Column is required unless requesting a heatmap.")

    if column and column not in df.columns:
        available_cols = ", ".join(df.columns)
        raise HTTPException(status_code=400, detail=f"Column '{column}' not found. Available columns: {available_cols}")

    sns.set_style(style)
    image_buffers = []

    for plot_type in requested_plots:
        fig, ax = plt.subplots(figsize=(10, 6))

        if plot_type == "bar":
            if not pd.api.types.is_object_dtype(df[column]) and not pd.api.types.is_categorical_dtype(df[column]):
                raise HTTPException(status_code=400, detail=f"Column '{column}' is not categorical for bar plot.")
            counts = df[column].value_counts().reset_index()
            counts.columns = [column, "count"]
            sns.barplot(data=counts, x=counts.columns[0], y="count", ax=ax, color=color)
            plt.title(title or f"Bar Plot of {column}")
            plt.xlabel(xlabel or column)
            plt.ylabel(ylabel or "Frequency")

        elif plot_type == "line":
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise HTTPException(status_code=400, detail=f"Column '{column}' must be numeric for line plot.")
            df[column].plot(kind="line", ax=ax, marker="o", color=color)
            plt.title(title or f"Line Chart of {column}")
            plt.xlabel(xlabel or "Index")
            plt.ylabel(ylabel or column)

        elif plot_type == "histogram":
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise HTTPException(status_code=400, detail=f"Column '{column}' must be numeric for histogram.")
            sns.histplot(df[column], kde=True, ax=ax, bins=20, color=color)
            plt.title(title or f"Histogram of {column}")
            plt.xlabel(xlabel or column)
            plt.ylabel(ylabel or "Frequency")

        elif plot_type == "heatmap":
            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.empty:
                raise HTTPException(status_code=400, detail="No numeric columns found for heatmap.")
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
            plt.title(title or "Heatmap of Correlations")

        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        image_buffers.append((plot_type, buf))
        plt.close()

    # Create a ZIP file with all images
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for plot_type, buf in image_buffers:
            zf.writestr(f"{plot_type}.png", buf.getvalue())

    zip_buf.seek(0)
    

    # Generate DataFrame Summary
    summary_stats = df.describe().to_dict()
    column_list = df.columns.tolist()
    
    
    return {
        "message": "Analysis completed successfully",
        "summary": summary_stats,
        "columns": column_list,
        "json_response":  JSONResponse(summary_stats, column_list),
        "chart_download": StreamingResponse(zip_buf, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=charts.zip"})
                                             
    }

