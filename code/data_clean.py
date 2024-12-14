import os
import pandas as pd


def get_url(path):
    df = pd.read_excel(path)
    list = []
    url_list = []
    stock_name = []
    for cell_value in df["SYMBOL"]:
        c = cell_value
        list.append(c)
    for i in list:
        url = "https://stocktwits.com/symbol/" + i
        stock_name.append(i)
        url_list.append(url)
    return url_list, stock_name


def read_stock_data(folder_path, stock_path):
    """Reads financial data in the folder, excluding specific ones, and returns a dictionary of DataFrames."""
    url_list, stock_name = get_url(stock_path)
    stock_data = {}
    for stock in stock_name:
        file_name = stock + ".xlsx"
        file_path = os.path.join(folder_path, file_name)
        stock_df = pd.read_excel(file_path, engine="openpyxl")
        if "date" in stock_df.columns:
            stock_df["date"] = pd.to_datetime(stock_df["date"], errors="coerce")
        stock_data[stock] = stock_df
    return stock_data


def read_sentiment_data(file_path):
    """Reads sentiment data and ensures 'date' and 'stock' columns are present."""
    sentiment_df = pd.read_excel(file_path, engine="openpyxl")
    if "date" in sentiment_df.columns:
        sentiment_df["date"] = pd.to_datetime(sentiment_df["date"], errors="coerce")
        sentiment_df = sentiment_df[sentiment_df["date"] >= "2024-08-01"]
    if "stock" not in sentiment_df.columns and "company" in sentiment_df.columns:
        sentiment_df["stock"] = sentiment_df["company"]
    return sentiment_df


def merge_data(stock_df, sentiment_df, company_name):
    """Merges stock data with sentiment data on 'date' and 'stock' columns, filtering sentiment = 0."""
    if "stock" not in stock_df.columns:
        stock_df["stock"] = company_name
    stock_df["date"] = pd.to_datetime(stock_df["date"], errors="coerce")
    sentiment_df["date"] = pd.to_datetime(sentiment_df["date"], errors="coerce")
    merged = pd.merge(stock_df, sentiment_df, on=["date", "stock"], how="inner")
    return merged[merged["sentiment_score"] != 0]


def process_all_sheets(stock_data, sentiment_data):
    """Processes all stock data sheets, merges them with sentiment data, and combines the results."""
    combined_data = [
        merge_data(stock_df, sentiment_data, company)
        for company, stock_df in stock_data.items()
    ]
    return (
        pd.concat(combined_data, ignore_index=True) if combined_data else pd.DataFrame()
    )


def add_variation_column(file_path, output_path):
    """Adds a 'variation' column to the data using (high - low), excluding unnecessary columns."""
    data = pd.read_excel(file_path, engine="openpyxl")
    if {"high", "low"}.issubset(data.columns):
        data["variation"] = (data["high"] - data["low"]) / data["low"]
        data = data.drop(columns=["open", "close"], errors="ignore")
        data.to_excel(output_path, index=False)


def add_dowjones_return_column(file_path, output_path):
    """Calculates Dow Jones return as (high - low) / low and saves the result."""
    dowjones_df = pd.read_excel(file_path, engine="openpyxl")
    if {"date", "close"}.issubset(dowjones_df.columns):
        dowjones_df = dowjones_df.sort_values("date")
        dowjones_df["return"] = dowjones_df["close"].pct_change() * 100
    dowjones_df.to_excel(output_path, index=False)


def calculate_weighted_sentiment(sentiment_data, dowjones_data):
    """Calculates daily weighted sentiment by firm size and merges it with Dow Jones data."""
    sentiment_data["size"] = pd.to_numeric(sentiment_data["size"], errors="coerce")
    sentiment_data["weighted_sentiment"] = (
        sentiment_data["sentiment_score"] * sentiment_data["size"]
    )
    daily_sentiment = (
        sentiment_data.groupby("date")
        .agg(
            total_weighted_sentiment=("weighted_sentiment", "sum"),
            total_size=("size", "sum"),
        )
        .reset_index()
    )
    daily_sentiment["daily_weighted_sentiment"] = (
        daily_sentiment["total_weighted_sentiment"] / daily_sentiment["total_size"]
    )
    return pd.merge(
        dowjones_data,
        daily_sentiment[["date", "daily_weighted_sentiment"]],
        on="date",
        how="left",
    )


def process_combined_data(dowjones_file_path, sentiment_file_path, output_path):
    """Processes Dow Jones and sentiment data, calculates daily weighted sentiment, and saves the result."""
    dowjones_df = pd.read_excel(dowjones_file_path, engine="openpyxl")
    sentiment_df = pd.read_excel(sentiment_file_path, engine="openpyxl")
    dowjones_df["date"] = pd.to_datetime(dowjones_df["date"], errors="coerce")
    sentiment_df["date"] = pd.to_datetime(sentiment_df["date"], errors="coerce")
    combined_data = calculate_weighted_sentiment(sentiment_df, dowjones_df)
    combined_data.to_excel(output_path, index=False)


def save_to_excel(df, output_path):
    """Saves the DataFrame to an Excel file."""
    df.to_excel(output_path, index=False)


if __name__ == "__main__":
    DATA_DIR = "data/financialdata"
    stock_path = "data/Dow_Jones_Average_Index_companies.xlsx"
    STOCK_SENTIMENT_OUTPUT = "data/processed_stock_sentiment_data.xlsx"
    STOCK_SENTIMENT_VARIATION_OUTPUT = (
        "data/processed_stock_sentiment_data_with_variation.xlsx"
    )
    DOWJONES_FILE = os.path.join(DATA_DIR, "dowjones_data.xlsx")
    DOWJONES_OUTPUT_FILE = os.path.join(DATA_DIR, "dowjones_data_with_return.xlsx")
    DOWJONES_SENTIMENT_OUTPUT = "data/processed_dowjones.xlsx"
    sentiment_file_path = "data/sentiment_score.xlsx"

    stock_data = read_stock_data(DATA_DIR, stock_path)
    sentiment_data = read_sentiment_data(sentiment_file_path)
    final_data = process_all_sheets(stock_data, sentiment_data)
    save_to_excel(final_data, STOCK_SENTIMENT_OUTPUT)
    add_variation_column(STOCK_SENTIMENT_OUTPUT, STOCK_SENTIMENT_VARIATION_OUTPUT)

    add_dowjones_return_column(DOWJONES_FILE, DOWJONES_OUTPUT_FILE)
    process_combined_data(
        DOWJONES_OUTPUT_FILE, STOCK_SENTIMENT_OUTPUT, DOWJONES_SENTIMENT_OUTPUT
    )
