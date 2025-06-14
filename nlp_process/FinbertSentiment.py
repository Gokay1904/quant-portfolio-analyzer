import torch
import numpy as np
import pandas as pd
import re
import nltk
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nlp_process.sp500_name_utils import get_company_names
from nltk.tokenize import sent_tokenize

class FinbertSentiment:
    def __init__(self, model_name="yiyanghkust/finbert-tone", device=None):
        nltk.download('punkt', quiet=True)
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def analyze(self, text):
        if not isinstance(text, str) or not text.strip():
            return {"sentiment": "neutral", "probabilities": {"neutral": 1.0, "positive": 0.0, "negative": 0.0}}
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits.detach().cpu().numpy()[0]
            probs = torch.nn.functional.softmax(torch.tensor(logits), dim=0).numpy()
        labels = ['neutral', 'positive', 'negative']
        sentiment = labels[np.argmax(probs)]
        return {
            "sentiment": sentiment,
            "probabilities": dict(zip(labels, probs.round(4)))
        }

    @staticmethod
    def extract_ticker_sentences(text, ticker):
        """
        Mapping'deki tüm varyasyonlarla eşleşen cümleleri döndürür.
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        company_names = get_company_names(ticker)
        patterns = [re.escape(name) for name in company_names]
        pattern = re.compile("|".join(patterns), re.IGNORECASE)
        sentences = sent_tokenize(text)
        filtered = [s for s in sentences if pattern.search(s)]
        return " ".join(filtered) if filtered else ""

    def analyze_row(self, row, ticker):
        head_text = self.extract_ticker_sentences(row['headline'], ticker)
        desc_text = self.extract_ticker_sentences(row['description'], ticker)
        detail_text = self.extract_ticker_sentences(row['detailed_news'], ticker)

        head_result = self.analyze(head_text)
        desc_result = self.analyze(desc_text)
        detail_result = self.analyze(detail_text)

        head_probs = head_result['probabilities']
        desc_probs = desc_result['probabilities']
        detail_probs = detail_result['probabilities']

        return pd.Series({
            "headline_positive": head_probs['positive'],
            "headline_neutral": head_probs['neutral'],
            "headline_negative": head_probs['negative'],
            "description_positive": desc_probs['positive'],
            "description_neutral": desc_probs['neutral'],
            "description_negative": desc_probs['negative'],
            "detailed_positive": detail_probs['positive'],
            "detailed_neutral": detail_probs['neutral'],
            "detailed_negative": detail_probs['negative'],
        })

    def analyze_dataframe(self, df, ticker):
        probs_df = df.apply(lambda row: self.analyze_row(row, ticker), axis=1)
        return pd.concat([df, probs_df], axis=1)

    @staticmethod
    def classify_condition(row):
        # İlgili detailed_news cümle sayısını bul
        detailed_sent_count = 0
        if isinstance(row.get('detailed_news', ""), str):
            from nlp_process.sp500_name_utils import get_company_names
            import re
            from nltk.tokenize import sent_tokenize
            ticker = row.get('ticker', '')
            company_names = get_company_names(ticker)
            patterns = [re.escape(name) for name in company_names]
            pattern = re.compile("|".join(patterns), re.IGNORECASE)
            sentences = sent_tokenize(row['detailed_news'])
            detailed_sent_count = sum(1 for s in sentences if pattern.search(s))
        # Ağırlıklar: detailed_news cümle sayısı arttıkça detailed ağırlığı artar
        # Min detailed_weight: 0.33, max: 0.7
        detailed_weight = min(0.7, max(0.33, detailed_sent_count / 6))
        other_weight = (1 - detailed_weight) / 2
        pos = (
            other_weight * row['headline_positive'] +
            other_weight * row['description_positive'] +
            detailed_weight * row['detailed_positive']
        )
        neg = (
            other_weight * row['headline_negative'] +
            other_weight * row['description_negative'] +
            detailed_weight * row['detailed_negative']
        )
        if pos >= 0.7:
            return "Highly Optimistic"
        elif pos >= 0.4:
            return "Optimistic"
        elif neg >= 0.7:
            return "Highly Pessimistic"
        elif neg >= 0.4:
            return "Pessimistic"
        else:
            return "Neutral"

    def sentence_sentiments(self, text, ticker):
        """
        Sadece mapping'deki varyasyonları içeren cümleleri analiz eder.
        """
        if not isinstance(text, str) or not text.strip():
            return []
        company_names = get_company_names(ticker)
        patterns = [re.escape(name) for name in company_names]
        pattern = re.compile("|".join(patterns), re.IGNORECASE)
        sentences = sent_tokenize(text)
        results = []
        for sent in sentences:
            if pattern.search(sent):
                res = self.analyze(sent)
                results.append({
                    "sentence": sent,
                    "sentiment": res["sentiment"],
                    "probabilities": res["probabilities"]
                })
        return results

