
import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

st.title("CSV Analysis and Visualization")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
column = st.text_input("Enter the column name to visualize", "")

if uploaded_file is not None and column:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("CSV loaded successfully!")
        st.write("Available columns:", list(df.columns))
        
        if column not in df.columns:
            st.error(f"Column '{column}' not found. Available columns: {list(df.columns)}")
        else:
            st.write(f"Generating histogram for column: {column}")
            # Set a style and customize background
            sns.set_style("darkgrid")  # Try a different style
            
            # Create the figure and axes with a custom background color
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_facecolor("lightgray")  # Change axes background color
            fig.patch.set_facecolor("lightgray")  # Change overall figure background
            
            sns.histplot(df[column], kde=True, color='blue', ax=ax)
            ax.set_title(f'Histogram of {column}', color='black')
            ax.set_xlabel(column, color='black')
            ax.set_ylabel('Frequency', color='black')
            plt.tight_layout()
            
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Error processing the CSV file: {e}")
else:
    st.info("Please upload a CSV file and specify a column name to generate a visualization.")
