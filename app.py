import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QFileDialog, QTabWidget, QMessageBox,
    QGroupBox, QGridLayout, QAbstractItemView, QListWidget, QInputDialog, QMenu
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from range_slider import QRangeSlider

class Portfolio:
    def __init__(self, name):
        self.name = name
        self.stocks = set()

    def add_stock(self, ticker):
        self.stocks.add(ticker)

    def remove_stock(self, ticker):
        self.stocks.discard(ticker)

    def has_stock(self, ticker):
        return ticker in self.stocks

    def get_stocks(self):
        return list(self.stocks)

class PortfolioManager:
    def __init__(self):
        self.portfolios = {}
        self.active_portfolio = None

    def create_portfolio(self, name):
        if name not in self.portfolios:
            self.portfolios[name] = Portfolio(name)
        self.active_portfolio = self.portfolios[name]

    def set_active(self, name):
        if name in self.portfolios:
            self.active_portfolio = self.portfolios[name]

    def get_active(self):
        return self.active_portfolio

    def get_portfolio_names(self):
        return list(self.portfolios.keys())

class PortfolioTab(QWidget):
    def __init__(self, portfolio_manager):
        super().__init__()
        self.portfolio_manager = portfolio_manager
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.portfolio_list = QListWidget()
        self.portfolio_list.itemClicked.connect(self.change_portfolio)
        self.layout.addWidget(QLabel("Portföyler"))
        self.layout.addWidget(self.portfolio_list)

        self.add_btn = QPushButton("Yeni Portföy Oluştur")
        self.add_btn.clicked.connect(self.create_portfolio)
        self.layout.addWidget(self.add_btn)

        self.stock_list = QListWidget()
        self.stock_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stock_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(QLabel("Portföydeki Hisseler"))
        self.layout.addWidget(self.stock_list)

        self.update_portfolio_list()
        self.update_list()

    def update_portfolio_list(self):
        self.portfolio_list.clear()
        for name in self.portfolio_manager.get_portfolio_names():
            self.portfolio_list.addItem(name)

    def update_list(self):
        self.stock_list.clear()
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            for stock in portfolio.get_stocks():
                self.stock_list.addItem(stock)

    def create_portfolio(self):
        name, ok = QInputDialog.getText(self, "Portföy Adı", "Yeni portföy adı girin:")
        if ok and name:
            self.portfolio_manager.create_portfolio(name)
            self.update_portfolio_list()
            self.update_list()

    def change_portfolio(self, item):
        self.portfolio_manager.set_active(item.text())
        self.update_list()

    def show_context_menu(self, pos: QPoint):
        item = self.stock_list.itemAt(pos)
        if item:
            menu = QMenu()
            remove_action = menu.addAction("Portföyden Çıkar")
            # İleride başka işlemler de eklenebilir
            action = menu.exec_(self.stock_list.mapToGlobal(pos))
            if action == remove_action:
                stock = item.text()
                portfolio = self.portfolio_manager.get_active()
                if portfolio:
                    portfolio.remove_stock(stock)
                    self.update_list()

class PortfolioManagerTab(QWidget):
    def __init__(self, parent, portfolio_manager):
        super().__init__()
        self.parent = parent
        self.portfolio_manager = portfolio_manager
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        filter_box = QGroupBox("Portföy Filtreleri")
        filter_layout = QGridLayout()
        filter_box.setLayout(filter_layout)

        # Return slider
        self.ret_range = QRangeSlider(Qt.Horizontal)
        self.ret_range.setMinimum(-100)
        self.ret_range.setMaximum(200)
        self.ret_range.setValue((0, 100))
        self.ret_range.rangeChanged.connect(self.update_table)
        filter_layout.addWidget(QLabel("Getiri Aralığı:"), 0, 0)
        filter_layout.addWidget(self.ret_range, 0, 1, 1, 2)
        self.ret_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.ret_val_label, 0, 3)

        # Volatility slider
        self.vol_range = QRangeSlider(Qt.Horizontal)
        self.vol_range.setMinimum(0)
        self.vol_range.setMaximum(200)
        self.vol_range.setValue((0, 100))
        self.vol_range.rangeChanged.connect(self.update_table)
        filter_layout.addWidget(QLabel("Volatilite Aralığı:"), 1, 0)
        filter_layout.addWidget(self.vol_range, 1, 1, 1, 2)
        self.vol_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.vol_val_label, 1, 3)

        self.layout.addWidget(filter_box)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.layout.addWidget(self.table)

        self.sort_col = 0
        self.sort_order = Qt.DescendingOrder

    def update_table(self):
        if self.parent.data is None:
            return
        returns = self.parent.data.pct_change().dropna()
        annual_returns, annual_std_dev = calculate_annualized_returns_and_risk(self.parent.data)
        sharpe = calculate_sharpe(returns)

        ret_min = self.ret_range.value()[0] / 100
        ret_max = self.ret_range.value()[1] / 100
        self.ret_val_label.setText(f"{ret_min:.2f} - {ret_max:.2f}")

        vol_min = self.vol_range.value()[0] / 100
        vol_max = self.vol_range.value()[1] / 100
        self.vol_val_label.setText(f"{vol_min:.2f} - {vol_max:.2f}")

        mask = (
            (annual_returns >= ret_min) & (annual_returns <= ret_max) &
            (annual_std_dev >= vol_min) & (annual_std_dev <= vol_max)
        )
        filtered = pd.DataFrame({
            "Sharpe": sharpe,
            "Volatilite": annual_std_dev,
            "Getiri": annual_returns
        })[mask]

        self.show_table(filtered)

    def show_table(self, df):
        self.table.clear()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Hisse", "Sharpe", "Volatilite", "Getiri", "Portföy"])
        active_portfolio = self.portfolio_manager.get_active()
        for i, (idx, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(idx)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['Sharpe']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['Volatilite']:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row['Getiri']:.2f}"))
            btn = QPushButton()
            if active_portfolio and active_portfolio.has_stock(idx):
                btn.setText("-")
                btn.setStyleSheet("background-color: #ffcccc;")
                btn.clicked.connect(lambda _, t=idx: self.remove_from_portfolio(t))
            else:
                btn.setText("+")
                btn.setStyleSheet("background-color: #ccffcc;")
                btn.clicked.connect(lambda _, t=idx: self.add_to_portfolio(t))
            self.table.setCellWidget(i, 4, btn)

            # Lending/Borrowing highlight (sadece göz ikonu açıksa)
            if hasattr(self, "lb_show_btn") and self.lb_show_btn.isChecked():
                if hasattr(self, "lending_stocks") and idx in self.lending_stocks:
                    for col in range(4):  # Sadece ilk 4 sütun (item olanlar)
                        item = self.table.item(i, col)
                        if item is not None:
                            item.setBackground(Qt.yellow)
                elif hasattr(self, "borrowing_stocks") and idx in self.borrowing_stocks:
                    for col in range(4):
                        item = self.table.item(i, col)
                        if item is not None:
                            item.setBackground(Qt.cyan)
        self.table.resizeColumnsToContents()

    def add_to_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.add_stock(ticker)
            self.update_table()
            self.parent.portfolio_tab.update_list()

    def remove_from_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.remove_stock(ticker)
            self.update_table()
            self.parent.portfolio_tab.update_list()

    def sort_table(self, col):
        if self.sort_col == col:
            self.sort_order = Qt.AscendingOrder if self.sort_order == Qt.DescendingOrder else Qt.DescendingOrder
        else:
            self.sort_col = col
            self.sort_order = Qt.DescendingOrder
        self.table.sortItems(col, self.sort_order)

class ChartTab(QWidget):
    def __init__(self, parent, portfolio_manager):
        super().__init__()
        self.parent = parent
        self.portfolio_manager = portfolio_manager

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Sol panel (widgetlar)
        side_panel = QGroupBox("Finansal Göstergeler")
        side_layout = QVBoxLayout()
        side_panel.setLayout(side_layout)

        # --- CML satırı ---
        cml_row = QHBoxLayout()
        cml_label = QLabel("CML")
        cml_row.addWidget(cml_label)

        self.cml_show_btn = QPushButton()
        self.cml_show_btn.setCheckable(True)
        self.cml_show_btn.setChecked(True)
        self.cml_show_btn.setIcon(QIcon.fromTheme("view-visible"))  # Göz ikonu
        self.cml_show_btn.clicked.connect(self.update_chart)
        cml_row.addWidget(self.cml_show_btn)

        self.cml_refresh_btn = QPushButton()
        self.cml_refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))  # Refresh ikonu
        self.cml_refresh_btn.clicked.connect(self.update_chart)
        cml_row.addWidget(self.cml_refresh_btn)

        side_layout.addLayout(cml_row)

        # --- Lending/Borrowing satırı ---
        lb_row = QHBoxLayout()
        lb_label = QLabel("Lending/Borrowing")
        lb_row.addWidget(lb_label)

        self.lb_show_btn = QPushButton()
        self.lb_show_btn.setCheckable(True)
        self.lb_show_btn.setChecked(True)
        self.lb_show_btn.setIcon(QIcon.fromTheme("view-visible"))  # Göz ikonu
        self.lb_show_btn.clicked.connect(self.update_chart)
        lb_row.addWidget(self.lb_show_btn)

        self.lb_refresh_btn = QPushButton()
        self.lb_refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))  # Refresh ikonu
        self.lb_refresh_btn.clicked.connect(self.update_chart)
        lb_row.addWidget(self.lb_refresh_btn)

        side_layout.addLayout(lb_row)

        # Toggle örneği (isteğe bağlı)
        self.toggle_btn = QPushButton("Toggle Özellik")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.clicked.connect(self.toggle_feature)
        side_layout.addWidget(self.toggle_btn)

        side_layout.addStretch()
        main_layout.addWidget(side_panel)

        # Sağ panel (grafik, filtreler, tablo)
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel)

        # Matplotlib chart + toolbar
        self.figure = Figure(figsize=(7, 5))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        right_panel.addWidget(self.toolbar)
        right_panel.addWidget(self.canvas)

        # Filtreler
        filter_box = QGroupBox("Grafik Filtreleri")
        filter_layout = QGridLayout()
        filter_box.setLayout(filter_layout)

        # Sharpe slider
        self.sharpe_range = QRangeSlider(Qt.Horizontal)
        self.sharpe_range.setMinimum(0)
        self.sharpe_range.setMaximum(300)
        self.sharpe_range.setValue((50, 150))
        self.sharpe_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Sharpe Aralığı:"), 0, 0)
        filter_layout.addWidget(self.sharpe_range, 0, 1, 1, 2)
        self.sharpe_val_label = QLabel("0.50 - 1.50")
        filter_layout.addWidget(self.sharpe_val_label, 0, 3)

        # Volatilite slider
        self.vol_range = QRangeSlider(Qt.Horizontal)
        self.vol_range.setMinimum(0)
        self.vol_range.setMaximum(200)
        self.vol_range.setValue((0, 100))
        self.vol_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Volatilite Aralığı:"), 1, 0)
        filter_layout.addWidget(self.vol_range, 1, 1, 1, 2)
        self.vol_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.vol_val_label, 1, 3)

        # Getiri slider
        self.ret_range = QRangeSlider(Qt.Horizontal)
        self.ret_range.setMinimum(-100)
        self.ret_range.setMaximum(200)
        self.ret_range.setValue((0, 100))
        self.ret_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Getiri Aralığı:"), 2, 0)
        filter_layout.addWidget(self.ret_range, 2, 1, 1, 2)
        self.ret_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.ret_val_label, 2, 3)

        # Arrow (Seçim) aracı artık burada!
        self.arrow_btn = QPushButton("Arrow (Seçim)")
        self.arrow_btn.setCheckable(True)
        self.arrow_btn.setChecked(True)
        self.arrow_btn.clicked.connect(self.set_arrow_mode)
        filter_layout.addWidget(self.arrow_btn, 3, 0, 1, 2)
        self.arrow_mode = True

        # Eksenleri sıfırla butonu
        self.reset_axes_btn = QPushButton("Eksenleri Sıfırla")
        self.reset_axes_btn.clicked.connect(self.reset_axes)
        filter_layout.addWidget(self.reset_axes_btn, 3, 2, 1, 2)

        right_panel.addWidget(filter_box)

        # Tablo
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)
        right_panel.addWidget(self.table)

        self.sort_col = 0
        self.sort_order = Qt.DescendingOrder

        # Interaktif: Nokta tıklama
        self.selected_stock = None
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.show_selected_stock_info)
        right_panel.addWidget(self.ok_btn)

        self.has_rendered = False  # Eklendi: ilk çizim kontrolü

        self.canvas.mpl_connect("button_press_event", self.on_point_click)
        # self.canvas.mpl_connect("draw_event", self.on_draw_event)  # Bunu kaldır veya yorum satırı yap

        self.highlight_mode = None  # <-- Bunu ekle

        self.toolbar.home = self.reset_home  # Home ikonuna kendi fonksiyonunu bağla

    def reset_home(self):
        # Grafik eksenlerini otomatik olarak en başa döndür
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # Tüm hisseleri ve filtreli hisseleri tekrar çiz
        ax.scatter(self.annual_std_dev, self.annual_returns, c='blue', alpha=0.5, label="Tüm Hisseler", picker=True)
        ax.scatter(self.filtered["Volatilite"], self.filtered["Getiri"], c='red', s=60, label="Filtreli", picker=True)
        for ticker in self.filtered.index:
            ax.annotate(ticker, (self.filtered.loc[ticker, "Volatilite"], self.filtered.loc[ticker, "Getiri"]), fontsize=8, alpha=0.7)
        ax.set_xlabel("Yıllık Volatilite (Risk)")
        ax.set_ylabel("Yıllık Getiri")
        ax.set_title("Risk-Getiri & Sharpe Dağılımı")
        ax.grid(True)
        ax.relim()
        ax.autoscale_view()  # Eksenleri otomatik sığdır
        self.current_ax = ax
        self.canvas.draw()

    def set_arrow_mode(self):
        self.arrow_mode = self.arrow_btn.isChecked()

    def on_point_click(self, event):
        if not self.arrow_mode:
            return
        if event.inaxes:
            x, y = event.xdata, event.ydata
            # Sadece ekranda görünen hisselerle çalış
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()
            mask = (self.annual_std_dev >= xlim[0]) & (self.annual_std_dev <= xlim[1]) & \
                   (self.annual_returns >= ylim[0]) & (self.annual_returns <= ylim[1])
            stds = self.annual_std_dev[mask]
            rets = self.annual_returns[mask]
            if stds.empty or rets.empty:
                return
            dists = np.sqrt((stds - x) ** 2 + (rets - y) ** 2)
            idx = dists.idxmin()
            sharpe = self.filtered.loc[idx, "Sharpe"] if idx in self.filtered.index else None
            vol = self.filtered.loc[idx, "Volatilite"] if idx in self.filtered.index else None
            ret = self.filtered.loc[idx, "Getiri"] if idx in self.filtered.index else None

            def fmt(val):
                if val is None or pd.isna(val):
                    return "-"
                return f"{val:.2f}"

            msg = (
                f"Hisse: {idx}\n"
                f"Sharpe: {fmt(sharpe)}\n"
                f"Volatilite: {fmt(vol)}\n"
                f"Getiri: {fmt(ret)}"
            )
            QMessageBox.information(self, "Hisse Bilgisi", msg)

    def update_chart(self):
        if self.parent.data is None:
            return

        # 1. Mevcut eksen limitlerini kaydet
        xlim, ylim = None, None
        if hasattr(self, "current_ax") and self.current_ax is not None:
            xlim = self.current_ax.get_xlim()
            ylim = self.current_ax.get_ylim()

        returns = self.parent.data.pct_change().dropna()
        annual_returns, annual_std_dev = calculate_annualized_returns_and_risk(self.parent.data)
        sharpe = calculate_sharpe(returns)

        self.annual_std_dev = annual_std_dev
        self.annual_returns = annual_returns
        self.sharpe = sharpe

        sharpe_min = self.sharpe_range.value()[0] / 100
        sharpe_max = self.sharpe_range.value()[1] / 100
        self.sharpe_val_label.setText(f"{sharpe_min:.2f} - {sharpe_max:.2f}")

        vol_min = self.vol_range.value()[0] / 100
        vol_max = self.vol_range.value()[1] / 100
        self.vol_val_label.setText(f"{vol_min:.2f} - {vol_max:.2f}")

        ret_min = self.ret_range.value()[0] / 100
        ret_max = self.ret_range.value()[1] / 100
        self.ret_val_label.setText(f"{ret_min:.2f} - {ret_max:.2f}")

        mask = (
            (sharpe >= sharpe_min) & (sharpe <= sharpe_max) &
            (annual_std_dev >= vol_min) & (annual_std_dev <= vol_max) &
            (annual_returns >= ret_min) & (annual_returns <= ret_max)
        )
        filtered = pd.DataFrame({
            "Sharpe": sharpe,
            "Volatilite": annual_std_dev,
            "Getiri": annual_returns
        })[mask]

        self.filtered = filtered

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(self.annual_std_dev, self.annual_returns, c='blue', alpha=0.5, label="Tüm Hisseler", picker=True)
        ax.scatter(filtered["Volatilite"], filtered["Getiri"], c='red', s=60, label="Filtreli", picker=True)
        for ticker in filtered.index:
            ax.annotate(ticker, (filtered.loc[ticker, "Volatilite"], filtered.loc[ticker, "Getiri"]), fontsize=8, alpha=0.7)
        ax.set_xlabel("Yıllık Volatilite (Risk)")
        ax.set_ylabel("Yıllık Getiri")
        ax.set_title("Risk-Getiri & Sharpe Dağılımı")
        ax.grid(True)

        # 2. Eksen limitlerini tekrar uygula (mevcut zoom/pan korunur)
        if xlim is not None and ylim is not None:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        # --- CML ve Lending/Borrowing sadece ikon açıksa çizilsin ---
        if self.cml_show_btn.isChecked():
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            visible_mask = (self.annual_std_dev >= xlim[0]) & (self.annual_std_dev <= xlim[1]) & \
                           (self.annual_returns >= ylim[0]) & (self.annual_returns <= ylim[1])
            visible_sharpe = sharpe[visible_mask]
            visible_returns = annual_returns[visible_mask]
            visible_std = annual_std_dev[visible_mask]
            if not visible_sharpe.empty:
                max_sharpe_idx = visible_sharpe.idxmax()
                max_sharpe_return = visible_returns[max_sharpe_idx]
                max_sharpe_risk = visible_std[max_sharpe_idx]
                risk_free_rate = 0.02
                cml_x = np.linspace(xlim[0], xlim[1], 200)
                cml_y = risk_free_rate + (max_sharpe_return - risk_free_rate) / max_sharpe_risk * cml_x
                ax.plot(cml_x, cml_y, color='green', linestyle='-', linewidth=2, label='CML')

                if self.lb_show_btn.isChecked():
                    lending_mask = (cml_x >= xlim[0]) & (cml_x <= max_sharpe_risk)
                    borrowing_mask = (cml_x > max_sharpe_risk)
                    ax.fill_between(cml_x[lending_mask], cml_y[lending_mask], risk_free_rate, color='lime', alpha=0.2, label='Lending')
                    ax.fill_between(cml_x[borrowing_mask], cml_y[borrowing_mask], cml_y[lending_mask][-1], color='orange', alpha=0.2, label='Borrowing')

                self.lending_stocks = visible_sharpe[visible_std <= max_sharpe_risk].index.tolist()
                self.borrowing_stocks = visible_sharpe[visible_std > max_sharpe_risk].index.tolist()
            else:
                self.lending_stocks = []
                self.borrowing_stocks = []
        else:
            self.lending_stocks = []
            self.borrowing_stocks = []

        ax.legend()
        self.canvas.draw()

        self.show_table(filtered)
        self.current_ax = ax

    def toggle_feature(self):
        # Toggle butonuna basınca yapılacak işlemler
        if self.toggle_btn.isChecked():
            self.toggle_btn.setText("Toggle Açık")
            # Buraya açılınca yapılacak işlemleri ekle
        else:
            self.toggle_btn.setText("Toggle Kapalı")
            # Buraya kapanınca yapılacak işlemleri ekle

    def highlight_lending_borrowing(self, mode):
        self.highlight_mode = mode
        self.show_table(self.filtered)

    def show_table(self, df):
        self.table.clear()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Hisse", "Sharpe", "Volatilite", "Getiri", "Portföy"])
        active_portfolio = self.portfolio_manager.get_active()
        for i, (idx, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(idx)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['Sharpe']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['Volatilite']:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row['Getiri']:.2f}"))
            btn = QPushButton()
            if active_portfolio and active_portfolio.has_stock(idx):
                btn.setText("-")
                btn.setStyleSheet("background-color: #ffcccc;")
                btn.clicked.connect(lambda _, t=idx: self.remove_from_portfolio(t))
            else:
                btn.setText("+")
                btn.setStyleSheet("background-color: #ccffcc;")
                btn.clicked.connect(lambda _, t=idx: self.add_to_portfolio(t))
            self.table.setCellWidget(i, 4, btn)

            # Lending/Borrowing highlight (sadece göz ikonu açıksa)
            if self.lb_show_btn.isChecked():
                if hasattr(self, "lending_stocks") and idx in self.lending_stocks:
                    for col in range(4):  # Sadece ilk 4 sütun (item olanlar)
                        item = self.table.item(i, col)
                        if item is not None:
                            item.setBackground(Qt.yellow)
                elif hasattr(self, "borrowing_stocks") and idx in self.borrowing_stocks:
                    for col in range(4):
                        item = self.table.item(i, col)
                        if item is not None:
                            item.setBackground(Qt.cyan)
        self.table.resizeColumnsToContents()

    def add_to_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.add_stock(ticker)
            self.update_chart()
            self.parent.portfolio_tab.update_list()

    def remove_from_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.remove_stock(ticker)
            self.update_chart()
            self.parent.portfolio_tab.update_list()

    def sort_table(self, col):
        if self.sort_col == col:
            self.sort_order = Qt.AscendingOrder if self.sort_order == Qt.DescendingOrder else Qt.DescendingOrder
        else:
            self.sort_col = col
            self.sort_order = Qt.DescendingOrder
        self.table.sortItems(col, self.sort_order)

    def on_point_click(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            dists = np.sqrt((self.annual_std_dev - x) ** 2 + (self.annual_returns - y) ** 2)
            idx = dists.idxmin()
            self.selected_stock = idx  # Sadece seçili hisseyi tut

    def show_selected_stock_info(self):
        if self.selected_stock is not None and self.selected_stock in self.filtered.index:
            sharpe = self.filtered.loc[self.selected_stock, "Sharpe"]
            vol = self.filtered.loc[self.selected_stock, "Volatilite"]
            ret = self.filtered.loc[self.selected_stock, "Getiri"]

            def fmt(val):
                if val is None or pd.isna(val):
                    return "-"
                return f"{val:.2f}"

            msg = (
                f"Hisse: {self.selected_stock}\n"
                f"Sharpe: {fmt(sharpe)}\n"
                f"Volatilite: {fmt(vol)}\n"
                f"Getiri: {fmt(ret)}"
            )
            QMessageBox.information(self, "Hisse Bilgisi", msg)
        else:
            QMessageBox.information(self, "Hisse Bilgisi", "Lütfen önce grafikten bir hisse seçin.")

    def reset_axes(self):
        self.update_chart()

    def on_draw_event(self, event):
        # Her yeniden çizimde (zoom/pan sonrası) CML ve Lending/Borrowing güncellenir
        self.update_chart()

def calculate_annualized_returns_and_risk(data):
    returns = data.pct_change().dropna()
    mean_daily_returns = returns.mean()
    std_daily_returns = returns.std()
    trading_days = 252
    annual_returns = mean_daily_returns * trading_days
    annual_std_dev = std_daily_returns * np.sqrt(trading_days)
    return annual_returns, annual_std_dev

def calculate_sharpe(returns, risk_free_rate=0.02):
    mean_daily_returns = returns.mean()
    std_daily_returns = returns.std()
    trading_days = 252
    annual_returns = mean_daily_returns * trading_days
    annual_std_dev = std_daily_returns * (trading_days ** 0.5)
    sharpe = (annual_returns - risk_free_rate) / annual_std_dev
    return sharpe

class FinanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finansal Analiz ve Portföy Uygulaması")
        self.resize(1200, 700)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.data = None
        self.portfolio_manager = PortfolioManager()
        self.portfolio_manager.create_portfolio("Portföy 1")

        self.tabs.addTab(self.data_tab_ui(), "Veri Yükle")
        self.chart_tab = ChartTab(self, self.portfolio_manager)
        self.tabs.addTab(self.chart_tab, "Risk-Getiri Analizi")
        self.portfolio_manager_tab = PortfolioManagerTab(self, self.portfolio_manager)
        self.tabs.addTab(self.portfolio_manager_tab, "Portföy Yöneticisi")
        self.portfolio_tab = PortfolioTab(self.portfolio_manager)
        self.tabs.addTab(self.portfolio_tab, "Portföyler")

        self.tabs.currentChanged.connect(self.on_tab_changed)  # Tab değişimini dinle

    def on_tab_changed(self, idx):
        # Risk-Getiri Analizi sekmesi açıldığında bir kez çizim yap
        if self.tabs.widget(idx) == self.chart_tab and not self.chart_tab.has_rendered:
            self.chart_tab.update_chart()
            self.chart_tab.has_rendered = True

    def data_tab_ui(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        self.data_label = QLabel("CSV dosyası seçin.")
        layout.addWidget(self.data_label)

        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("CSV Yükle")
        self.load_btn.clicked.connect(self.load_csv)
        btn_layout.addWidget(self.load_btn)

        self.clear_btn = QPushButton("Veriyi Temizle")
        self.clear_btn.clicked.connect(self.clear_data)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)
        return tab

    def load_csv(self):
        fname, _ = QFileDialog.getOpenFileName(self, "CSV Dosyası Seç", "", "CSV Files (*.csv)")
        if fname:
            self.data = pd.read_csv(fname, index_col=0, parse_dates=True)
            self.data_label.setText(f"Yüklendi: {fname}")
            self.chart_tab.has_rendered = False  # Yeni veri yüklenince tekrar çizilsin
            self.portfolio_manager_tab.update_table()

    def clear_data(self):
        self.data = None
        self.data_label.setText("Veri temizlendi.")
        self.chart_tab.has_rendered = False  # Temizlenince tekrar çizilsin
        self.portfolio_manager_tab.update_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceApp()
    window.show()
    sys.exit(app.exec_())