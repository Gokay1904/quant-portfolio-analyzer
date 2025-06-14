import os
import pandas as pd

class NewsInspector:
    def __init__(self, sp500_news_dir="sp500_news"):
        self.sp500_news_dir = sp500_news_dir

    def load_news_for_tickers(self, tickers, freq="Daily"):
        dfs = []
        for ticker in tickers:
            path = os.path.join(self.sp500_news_dir, f"{ticker.lower()}_news.csv")
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['ticker'] = ticker
                dfs.append(df)
        if not dfs:
            return pd.DataFrame()
        df = pd.concat(dfs, ignore_index=True)
        if freq == "Weekly" and "date" in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['week'] = df['date'].dt.to_period('W').astype(str)
            df = df.groupby(['ticker', 'week']).agg({
                'headline': 'first',
                'description': 'first',
                'detailed_news': 'first',
                'headline_positive': 'mean',
                'headline_neutral': 'mean',
                'headline_negative': 'mean',
                'description_positive': 'mean',
                'description_neutral': 'mean',
                'description_negative': 'mean',
                'detailed_positive': 'mean',
                'detailed_neutral': 'mean',
                'detailed_negative': 'mean',
            }).reset_index()
        return df

    @staticmethod
    def get_sentiment_label(row):
        pos = row.get('detailed_positive', 0)
        neg = row.get('detailed_negative', 0)
        if pos >= 0.7:
            return "POSITIVE"
        elif neg >= 0.7:
            return "NEGATIVE"
        else:
            return "NEUTRAL"