import pandas as pd
from config import Config

def recommend_chart_type(df: pd.DataFrame, question: str) -> str:
    """Asks Gemini to recommend the best Streamlit chart for the dataframe."""
    if df.empty or "error" in df.columns:
        return "table"
    
    # Give the LLM a sample of the data to make a decision
    data_sample = df.head(3).to_markdown()
    
    prompt = f"""
    Based on the following data sample and the user's question, what is the best way to visualize this data?
    Options: 'bar', 'line', 'table'.
    
    Question: {question}
    Data Sample: 
    {data_sample}
    
    Return ONLY the option name (bar, line, or table).
    """
    
    response = Config.llm.invoke(prompt)
    return response.content.strip().lower()