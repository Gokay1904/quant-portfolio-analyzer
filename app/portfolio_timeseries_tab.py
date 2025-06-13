from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDateEdit, QListWidget, QListWidgetItem, QAbstractItemView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

class PortfolioTimeSeriesTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Üst panel: Portföy, frekans ve tarih aralığı seçimi
        row = QHBoxLayout()
        row.addWidget(QLabel("Portföy:"))
        self.portfolio_combo = QComboBox()
        if hasattr(parent, "portfolio_manager"):
            for name in parent.portfolio_manager.get_portfolio_names():
                self.portfolio_combo.addItem(name)
        self.portfolio_combo.currentIndexChanged.connect(self.update_stock_list)
        row.addWidget(self.portfolio_combo)

        row.addWidget(QLabel("Frekans:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["Günlük", "Aylık", "Yıllık"])
        row.addWidget(self.freq_combo)

        row.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        row.addWidget(self.start_date)

        row.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        row.addWidget(self.end_date)

        self.normalize_btn = QPushButton("Normalize Et (0-1)")
        self.normalize_btn.setCheckable(True)
        row.addWidget(self.normalize_btn)

        self.update_btn = QPushButton("Güncelle")
        self.update_btn.clicked.connect(self.update_chart)
        row.addWidget(self.update_btn)
        self.layout.addLayout(row)

        # Hisse seçimi için liste
        self.stock_list = QListWidget()
        self.stock_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.layout.addWidget(QLabel("Portföydeki Hisseler:"))
        self.layout.addWidget(self.stock_list)

        # Grafik
        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.update_stock_list()  # İlk açılışta doldur

    def update_stock_list(self):
        self.stock_list.clear()
        portfolio_name = self.portfolio_combo.currentText()
        if not hasattr(self.parent, "portfolio_manager"):
            return
        portfolio = self.parent.portfolio_manager.portfolios.get(portfolio_name)
        if not portfolio:
            return
        for stock in sorted(portfolio.get_stocks()):
            item = QListWidgetItem(stock)
            item.setSelected(True)  # Varsayılan olarak hepsi seçili
            self.stock_list.addItem(item)

    def update_chart(self):
        if self.parent.data is None:
            return
        portfolio_name = self.portfolio_combo.currentText()
        portfolio = self.parent.portfolio_manager.portfolios.get(portfolio_name)
        if not portfolio:
            return
        # Seçili hisseleri al
        selected_items = self.stock_list.selectedItems()
        stocks = [item.text() for item in selected_items]
        if not stocks:
            return
        data = self.parent.data[stocks].copy()
        # Tarih aralığı
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        data = data[(data.index >= pd.Timestamp(start)) & (data.index <= pd.Timestamp(end))]
        # Frekans
        freq_map = {"Günlük": "D", "Aylık": "M", "Yıllık": "Y"}
        freq = freq_map[self.freq_combo.currentText()]
        data = data.resample(freq).last()
        data = data.bfill()  # <-- Eksik verileri backward fill ile doldur
        # Normalize seçiliyse 0-1 arası scale et
        if self.normalize_btn.isChecked():
            data = (data - data.min()) / (data.max() - data.min())
        # Grafik çiz
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for stock in stocks:
            ax.plot(data.index, data[stock], label=stock)
        ax.set_title(f"{portfolio_name} Portföyü Zaman Serisi ({self.freq_combo.currentText()})")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Fiyat" if not self.normalize_btn.isChecked() else "Normalize Fiyat (0-1)")
        ax.legend()
        self.canvas.draw()