import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from transformers import pipeline
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score
from datastorage import get_all_comments
from datastorage import save_sentiment
from datastorage import get_all_sentiments


def write_csv(data, path):
    """Write the DataFrame data to a CSV file."""
    data.to_csv(path, mode="w+", index=False, encoding="utf-8")


def write_excel(data, path, sheet_name="Sheet1"):
    """Write the DataFrame data to an Excel file."""
    data.to_excel(path, sheet_name=sheet_name, index=False)


def comments_analysis(all_comments):
    """Analyze all comments and save the results."""
    data_sorted = all_comments.sort_values(by=["stock", "comment_time"]).reset_index(
        drop=True
    )
    stock_comment_counts = (
        data_sorted.groupby("stock").size().reset_index(name="total_comments")
    )
    tenth_comment_time = (
        data_sorted.groupby("stock", group_keys=False)
        .apply(
            lambda x: pd.Series(
                {
                    "stock": x["stock"].iloc[0],
                    "comment_time": x["comment_time"].iloc[9] if len(x) > 9 else None,
                }
            )
        )
        .reset_index(drop=True)
    )
    result = pd.merge(stock_comment_counts, tenth_comment_time, on="stock", how="left")
    result = result.rename(columns={"comment_time": "tenth_comment_time"})
    result = result.sort_values(by="total_comments", ascending=False).reset_index(
        drop=True
    )
    write_csv(result, path=OUTPUT_DIR1)


def sentiment_analysis(all_comments):
    """Perform text sentiment analysis and save the results."""
    pipe = pipeline(
        "text-classification",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
        device=0,
        truncation=True,
        padding=True,
    )

    comments = all_comments["comments"].astype(str).tolist()
    batch_size = 16
    sentiment_results = []

    for i in tqdm(
        range(0, len(comments), batch_size), desc="Processing comments in batches"
    ):
        batch = comments[i : i + batch_size]
        try:
            results = pipe(batch)
            sentiment_results.extend(results)
        except Exception as e:
            print(f"Error processing batch {i}: {e}")
            sentiment_results.extend([{"label": "error", "score": 0.0}] * len(batch))
    all_comments["sentiment"] = [res["label"] for res in sentiment_results]
    all_comments["score"] = [res["score"] for res in sentiment_results]
    save_sentiment(all_comments, session)


def check_accuracy(all_sentiments):
    """Evaluate the accuracy of the sentiment analysis model."""
    label_mapping = {"Bullish": "positive", "Bearish": "negative"}
    all_sentiments["mapped_sentiment_tag"] = all_sentiments["sentiment_tag"].map(
        label_mapping
    )
    labeled_data = all_sentiments.dropna(subset=["mapped_sentiment_tag", "sentiment"])
    y_true = labeled_data["mapped_sentiment_tag"].str.lower()
    y_pred = labeled_data["sentiment"].str.lower()
    labels = ["positive", "negative", "neutral"]
    filtered_data = labeled_data[y_pred != "neutral"]
    y_true_filtered = filtered_data["mapped_sentiment_tag"].str.lower()
    y_pred_filtered = filtered_data["sentiment"].str.lower()
    accuracy = accuracy_score(y_true_filtered, y_pred_filtered)
    print(f"Model Accuracy: {accuracy:.2%}")

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    correct_predictions = cm.diagonal().sum()
    positive_as_negative = cm[0, 1] if len(cm) > 1 else 0
    negative_as_positive = cm[1, 0] if len(cm) > 1 else 0
    categories = ["Correct Predictions", "Positive as Negative", "Negative as Positive"]
    values = [correct_predictions, positive_as_negative, negative_as_positive]
    plt.figure(figsize=(12, 8))
    plt.bar(categories, values, color=["green", "red", "blue", "orange"])
    plt.title("Model Prediction Results", fontsize=16)
    plt.xlabel("Categories", fontsize=14)
    plt.ylabel("Count", fontsize=14)
    plt.xticks(rotation=30, fontsize=12, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR3)


def get_sentiment_score(all_sentiments):
    """Calculate and return the sentiment score."""
    if not np.issubdtype(all_sentiments["comment_time"].dtype, np.datetime64):
        all_sentiments["comment_time"] = pd.to_datetime(all_sentiments["comment_time"])
    all_sentiments["date"] = all_sentiments["comment_time"].dt.date
    all_sentiments["weighted_influence"] = np.log1p(all_sentiments["influence"]) + 1
    sentiment_scores = []
    grouped = all_sentiments.groupby(["stock", "date"])
    for (stock, date), group in grouped:
        positive_weighted = group.loc[
            group["sentiment"] == "positive", "weighted_influence"
        ].sum()
        negative_weighted = group.loc[
            group["sentiment"] == "negative", "weighted_influence"
        ].sum()

        if (positive_weighted + negative_weighted) > 0:
            sentiment_score = (positive_weighted - negative_weighted) / (
                positive_weighted + negative_weighted
            )
        else:
            sentiment_score = 0

        total_posts = len(group)
        final_score = sentiment_score * np.log1p(total_posts)

        sentiment_scores.append(
            {"stock": stock, "date": date, "sentiment_score": final_score}
        )
    result = pd.DataFrame(sentiment_scores)
    write_excel(result, path=OUTPUT_DIR4)
    return result


if __name__ == "__main__":
    OUTPUT_DIR1 = "artifacts/comments_amount.csv"
    OUTPUT_DIR2 = "artifacts/comment_sentiment.csv"
    OUTPUT_DIR3 = "artifacts/accuracy.png"
    OUTPUT_DIR4 = "data/sentiment_score.xlsx"
    os.makedirs("artifacts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    load_dotenv()
    DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_DATABASE = os.getenv("DATABASE_DATABASE")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DATABASE}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    all_comments = get_all_comments(session)
    comments_analysis(all_comments)
    sentiment_analysis(all_comments)
    all_sentiments = get_all_sentiments(session)
    check_accuracy(all_sentiments)
    get_sentiment_score(all_sentiments)
