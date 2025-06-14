from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy,
    QListWidget, QLineEdit, QPushButton, QGroupBox, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt
import pandas as pd
import os
from nlp_process.FinbertSentiment import FinbertSentiment
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class SentimentTab(QWidget):
    def __init__(self, portfolio_manager):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.finbert = FinbertSentiment()
        self.result_df = pd.DataFrame()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Sol: Portföy ve Hisse Seçimi ---
        filter_group = QGroupBox("Filtrele")
        filter_layout = QVBoxLayout()
        filter_group.setLayout(filter_layout)

        # Portföy seçimi
        self.portfolio_list = QListWidget()
        self.portfolio_list.addItems(self.portfolio_manager.get_portfolio_names())
        self.portfolio_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.portfolio_list.currentItemChanged.connect(self.on_portfolio_selected)
        filter_layout.addWidget(QLabel("Portföy Seç"))
        filter_layout.addWidget(self.portfolio_list)

        # Hisse arama ve seçme
        filter_layout.addWidget(QLabel("Hisse Ara/Seç"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ticker ara (örn: AAPL)")
        filter_layout.addWidget(self.search_box)

        self.ticker_list = QListWidget()
        self.ticker_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.populate_ticker_list()
        filter_layout.addWidget(self.ticker_list)

        self.search_box.textChanged.connect(self.filter_ticker_list)

        # Ara butonu
        self.search_button = QPushButton("Ara")
        self.search_button.clicked.connect(self.on_search_clicked)
        filter_layout.addWidget(self.search_button)

        # Inspect butonu
        self.inspect_button = QPushButton("Inspect")
        self.inspect_button.clicked.connect(self.on_inspect_clicked)
        filter_layout.addWidget(self.inspect_button)

        main_layout.addWidget(filter_group, 1)

        # --- Sağ: Haberler ---
        self.news_area = QScrollArea()
        self.news_area.setWidgetResizable(True)
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_area.setWidget(self.news_container)
        main_layout.addWidget(self.news_area, 4)

        self.setLayout(main_layout)
        self.selected_tickers = []
        self.show_news([])

    def populate_ticker_list(self):
        # Tüm scraping/sp500_news klasöründeki tickerları bul
        scraping_dir = "c:/Users/Gokay/OneDrive/Desktop/QuantFolder/scraping/sp500_news"
        tickers = []
        if os.path.exists(scraping_dir):
            for fname in os.listdir(scraping_dir):
                if fname.endswith("_news.csv"):
                    tickers.append(fname.split("_news.csv")[0].upper())
        self.ticker_list.clear()
        self.ticker_list.addItems(sorted(tickers))

    def filter_ticker_list(self, text):
        for i in range(self.ticker_list.count()):
            item = self.ticker_list.item(i)
            item.setHidden(text.upper() not in item.text())

    def on_portfolio_selected(self):
        # Portföy seçilince, ilgili hisseleri otomatik seç
        selected_portfolio = self.portfolio_list.currentItem().text() if self.portfolio_list.currentItem() else None
        if not selected_portfolio:
            return
        tickers = self.portfolio_manager.portfolios[selected_portfolio].get_stocks()
        # Ticker listesinde bu hisseleri seçili yap
        for i in range(self.ticker_list.count()):
            item = self.ticker_list.item(i)
            item.setSelected(item.text() in tickers)
        self.show_news(tickers)

    def on_search_clicked(self):
        # Seçili hisseleri bul ve haberleri göster
        selected = [self.ticker_list.item(i).text() for i in range(self.ticker_list.count()) if self.ticker_list.item(i).isSelected()]
        self.show_news(selected)

    def on_inspect_clicked(self):
        if self.result_df.empty:
            QMessageBox.information(self, "Inspect", "Önce haberleri yükleyin.")
            return
        # İlk 5 haberi gösteren bir popup
        msg = QMessageBox(self)
        msg.setWindowTitle("Inspect: İlk 5 Haber")
        msg.setText(self.result_df.head().to_string())
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_news(self, tickers):
        # Clear previous news
        for i in reversed(range(self.news_layout.count())):
            widget = self.news_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not tickers:
            label = QLabel("Haber görmek için portföy seçin veya hisseleri seçip 'Ara'ya tıklayın.")
            label.setWordWrap(True)
            self.news_layout.addWidget(label)
            self.result_df = pd.DataFrame()
            return

        news_df = self.load_news_for_tickers(tickers)
        if news_df.empty:
            label = QLabel("Seçili hisseler için haber bulunamadı.")
            label.setWordWrap(True)
            self.news_layout.addWidget(label)
            self.result_df = pd.DataFrame()
            return

        # FinBERT skorları yoksa hesapla
        sentiment_cols = [
            "headline_positive", "headline_neutral", "headline_negative",
            "description_positive", "description_neutral", "description_negative",
            "detailed_positive", "detailed_neutral", "detailed_negative"
        ]
        if not all(col in news_df.columns for col in sentiment_cols):
            # Her ticker için ayrı ayrı analiz et
            dfs = []
            for ticker in tickers:
                df_ticker = news_df[news_df['ticker'] == ticker]
                df_ticker = self.finbert.analyze_dataframe(df_ticker, ticker=ticker)
                dfs.append(df_ticker)
            news_df = pd.concat(dfs, ignore_index=True)

        # Sınıflandırma etiketi ekle
        if "classified" not in news_df.columns:
            news_df['classified'] = news_df.apply(self.finbert.classify_condition, axis=1)

        self.result_df = news_df.copy()

        for _, row in news_df.iterrows():
            news_widget = self.create_news_widget(row)
            news_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.news_layout.addWidget(news_widget)

        # PIE CHART: Distribution of classified news
        if not news_df.empty:
            fig = plt.figure(figsize=(4, 4))
            news_df['classified'].value_counts().plot.pie(
                autopct='%1.1f%%',
                colors=sns.color_palette("Set2"),
                ylabel=""
            )
            plt.title("Distribution of News Sentiment (Detailed News)")
            plt.tight_layout()
            canvas = FigureCanvas(fig)
            self.news_layout.addWidget(canvas)

        self.news_layout.addStretch()

    def load_news_for_tickers(self, tickers):
        dfs = []
        scraping_dir = "c:/Users/Gokay/OneDrive/Desktop/QuantFolder/scraping/sp500_news"
        
        for ticker in tickers:
            path = os.path.join(scraping_dir, f"{ticker.lower()}_news.csv")
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['ticker'] = ticker
                dfs.append(df)
        if not dfs:
            return pd.DataFrame()
        df = pd.concat(dfs, ignore_index=True)
        return df

    def create_news_widget(self, row):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(frame)

        # Üst satır: Ticker + related + sağ üstte sınıflandırma etiketi
        top_row = QHBoxLayout()
        ticker_label = QLabel(f"<b>{row.get('ticker','')}</b>")
        ticker_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        related_label = QLabel(f"<i>{row.get('related','')}</i>")
        related_label.setStyleSheet("color: #888;")
        related_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(ticker_label)
        top_row.addWidget(related_label)
        top_row.addStretch()
        sentiment_label = row.get('classified', 'N/A')
        sentiment_color = {
            "Highly Optimistic": "#4A90E2",
            "Optimistic": "#6EC6FF",
            "Highly Pessimistic": "#D0021B",
            "Pessimistic": "#FF6E6E",
            "Neutral": "#888888"
        }.get(sentiment_label, "#888888")
        sentiment = QLabel(sentiment_label)
        sentiment.setStyleSheet(f"background:{sentiment_color}; color:white; padding:2px 10px; border-radius:8px; font-weight:bold;")
        sentiment.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_row.addWidget(sentiment, alignment=Qt.AlignRight)
        layout.addLayout(top_row)

        # Headline, Description, Detailed News (her cümle altı çizili ve renkli)
        for field, label in [
            ("headline", "Headline"),
            ("description", "Description"),
            ("detailed_news", "Detailed News")
        ]:
            html = self.colored_sentences_html(row.get(field, ""), self.finbert)
            lbl = QLabel(f"<b>{label}:</b> {html}")
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setStyleSheet("color:black;")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(lbl)

        # Tarih
        date_lbl = QLabel(f"<b>Date Published:</b> {row.get('date_published','')}")
        date_lbl.setWordWrap(True)
        date_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(date_lbl)

        # Skorlar (renkli)
        score_row = QHBoxLayout()
        for field, prefix, color in [
            ("Headline", "headline", "#4A90E2"),
            ("Description", "description", "#888888"),
            ("Detailed", "detailed", "#D0021B")
        ]:
            lbl = QLabel(
                f"<b>{field}</b> POS: <span style='color:#4A90E2'>{row.get(f'{prefix}_positive',0):.2f}</span> | "
                f"NEU: <span style='color:#888888'>{row.get(f'{prefix}_neutral',0):.2f}</span> | "
                f"NEG: <span style='color:#D0021B'>{row.get(f'{prefix}_negative',0):.2f}</span>"
            )
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setStyleSheet("color:black;")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            score_row.addWidget(lbl)
        layout.addLayout(score_row)

        return frame

    def colored_sentences_html(self, text, finbert):
        sents = finbert.sentence_sentiments(text)
        html = ""
        for s in sents:
            if s["sentiment"] == "positive":
                html += f'<span style="color:#4A90E2;">{s["sentence"]} </span>'
            elif s["sentiment"] == "negative":
                html += f'<span style="color:#D0021B;">{s["sentence"]} </span>'
            else:  # neutral
                html += f'<span style="color:#888888;">{s["sentence"]} </span>'
        return html if html else f'<span style="color:black;">{text}</span>'