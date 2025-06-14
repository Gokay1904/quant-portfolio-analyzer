import pandas as pd
import re
from nltk.tokenize import sent_tokenize, word_tokenize

CSV_PATH = "c:/Users/Gokay/OneDrive/Desktop/QuantFolder/scraping/constituents.csv"

def load_sp500_company_map(csv_path=CSV_PATH):
    df = pd.read_csv(csv_path, usecols=["Symbol", "Security"])
    company_map = {}
    for _, row in df.iterrows():
        ticker = str(row['Symbol']).upper()
        security = str(row['Security'])
        words = [w for w in word_tokenize(security) if w.isalpha()]
        variations = [ticker, security, f"{ticker}({security})"]
        variations += words
        company_map[ticker] = list(dict.fromkeys(variations))
    return company_map

SP500_COMPANY_MAP = load_sp500_company_map()

def get_company_names(ticker):
    return SP500_COMPANY_MAP.get(ticker.upper(), [])

def extract_relevant_sentences(text, ticker):
    """
    Mapping'deki tüm varyasyonları (ticker, şirket adı, Symbol(Security), kelimeler) arar.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    company_names = get_company_names(ticker)
    patterns = [re.escape(name) for name in company_names]
    pattern = re.compile("|".join(patterns), re.IGNORECASE)
    sentences = sent_tokenize(text)
    filtered = [s for s in sentences if pattern.search(s)]
    return " ".join(filtered) if filtered else ""

# Example usage:
# extract_relevant_sentences(news_text, "TSLA")