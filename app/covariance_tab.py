from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
import numpy as np

class CovarianceTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Portföy seçimi
        row = QHBoxLayout()
        row.addWidget(QLabel("Portföy:"))
        self.portfolio_combo = QComboBox()
        self.portfolio_combo.addItem("Tüm Hisseler")
        if hasattr(parent, "portfolio_manager"):
            for name in parent.portfolio_manager.get_portfolio_names():
                self.portfolio_combo.addItem(name)
        row.addWidget(self.portfolio_combo)
        self.calc_btn = QPushButton("Kovaryans Heatmap")
        self.calc_btn.clicked.connect(self.calculate_covariance)
        row.addWidget(self.calc_btn)
        self.layout.addLayout(row)

        # Heatmap için Figure
        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Kovaryans tablosu (ilk 10 yüksek/düşük)
        self.cov_table = QTableWidget()
        self.layout.addWidget(QLabel("En Yüksek ve En Düşük Kovaryanslı 10 Hisse Çifti"))
        self.layout.addWidget(self.cov_table)

    def calculate_covariance(self):
        if self.parent.data is None:
            return
        selected = self.portfolio_combo.currentText()
        if selected == "Tüm Hisseler":
            data = self.parent.data
        else:
            portfolio = self.parent.portfolio_manager.portfolios.get(selected)
            if not portfolio:
                return
            stocks = portfolio.get_stocks()
            data = self.parent.data[stocks]
        cov = data.pct_change().dropna().cov()
        self.show_heatmap(cov)
        self.show_top_covariances(cov)

    def show_heatmap(self, cov):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        sns.heatmap(cov, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
        ax.set_title("Kovaryans Matrisi (Heatmap)")
        self.canvas.draw()

    def show_top_covariances(self, cov):
        # Kovaryans matrisini üçgen olarak al, diagonal hariç
        cov_values = cov.where(~np.eye(cov.shape[0],dtype=bool))
        pairs = []
        for i, row in enumerate(cov.index):
            for j, col in enumerate(cov.columns):
                if i < j:
                    pairs.append((row, col, cov.iloc[i, j]))
        # En yüksek 10 ve en düşük 10 kovaryans
        pairs_sorted = sorted(pairs, key=lambda x: x[2])
        lowest = pairs_sorted[:10]
        highest = pairs_sorted[-10:][::-1]

        # Tabloya yaz
        self.cov_table.clear()
        self.cov_table.setRowCount(20)
        self.cov_table.setColumnCount(3)
        self.cov_table.setHorizontalHeaderLabels(["Hisse 1", "Hisse 2", "Kovaryans"])
        for i, (a, b, v) in enumerate(lowest + highest):
            self.cov_table.setItem(i, 0, QTableWidgetItem(str(a)))
            self.cov_table.setItem(i, 1, QTableWidgetItem(str(b)))
            self.cov_table.setItem(i, 2, QTableWidgetItem(f"{v:.4f}"))
        self.cov_table.resizeColumnsToContents()