import requests

def get_news_yahoo(ticker, count=10):
    """
    Yahoo Finance üzerinden ilgili hisse için son haberleri getirir.
    """
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={"AAPL"}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"HTTP hata kodu: {response.status_code}")
            return []
        try:
            data = response.json()
        except Exception as e:
            print(f"Yanıt JSON'a çevrilemedi: {e}")
            return []
        news_list = []
        if "news" in data:
            for news in data["news"][:count]:
                news_list.append({
                    "title": news.get("title"),
                    "publisher": news.get("publisher"),
                    "link": news.get("link"),
                    "providerPublishTime": news.get("providerPublishTime")
                })
        return news_list
    except Exception as e:
        print(f"Haber alınırken hata oluştu: {e}")
        return []