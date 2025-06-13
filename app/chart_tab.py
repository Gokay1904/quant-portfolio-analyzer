from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, QMessageBox
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from .core import calculate_annualized_returns_and_risk, calculate_sharpe
from range_slider import QRangeSlider
import pandas as pd
import numpy as np
from PyQt5.QtGui import QIcon

class ChartTab(QWidget):
    def __init__(self, parent, portfolio_manager):
        super().__init__()
        self.parent = parent
        self.portfolio_manager = portfolio_manager
        self.has_rendered = False

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Sol panel (göstergeler)
        side_panel = QGroupBox("Finansal Göstergeler")
        side_layout = QVBoxLayout()
        side_panel.setLayout(side_layout)

        # --- CML satırı ---
        cml_row = QHBoxLayout()
        cml_label = QLabel("CML")
        cml_row.addWidget(cml_label)
        self.cml_show_btn = QPushButton("Göster")
        self.cml_show_btn.setCheckable(True)
        self.cml_show_btn.setChecked(True)
        self.cml_show_btn.clicked.connect(self.update_chart)
        cml_row.addWidget(self.cml_show_btn)
        self.cml_refresh_btn = QPushButton("⟳")
        self.cml_refresh_btn.clicked.connect(self.update_chart)
        cml_row.addWidget(self.cml_refresh_btn)
        side_layout.addLayout(cml_row)

        # --- Lending/Borrowing satırı ---
        lb_row = QHBoxLayout()
        lb_label = QLabel("Lending/Borrowing")
        lb_row.addWidget(lb_label)
        self.lb_show_btn = QPushButton("Göster")
        self.lb_show_btn.setCheckable(True)
        self.lb_show_btn.setChecked(True)
        self.lb_show_btn.clicked.connect(self.update_chart)
        lb_row.addWidget(self.lb_show_btn)
        self.lb_refresh_btn = QPushButton("⟳")
        self.lb_refresh_btn.clicked.connect(self.update_chart)
        lb_row.addWidget(self.lb_refresh_btn)
        side_layout.addLayout(lb_row)

        side_layout.addStretch()
        main_layout.addWidget(side_panel)

        # Sağ panel (grafik ve filtreler)
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

        self.sharpe_range = QRangeSlider(Qt.Horizontal)
        self.sharpe_range.setMinimum(0)
        self.sharpe_range.setMaximum(300)
        self.sharpe_range.setValue((50, 150))
        self.sharpe_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Sharpe Aralığı:"), 0, 0)
        filter_layout.addWidget(self.sharpe_range, 0, 1, 1, 2)
        self.sharpe_val_label = QLabel("0.50 - 1.50")
        filter_layout.addWidget(self.sharpe_val_label, 0, 3)

        self.vol_range = QRangeSlider(Qt.Horizontal)
        self.vol_range.setMinimum(0)
        self.vol_range.setMaximum(200)
        self.vol_range.setValue((0, 100))
        self.vol_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Volatilite Aralığı:"), 1, 0)
        filter_layout.addWidget(self.vol_range, 1, 1, 1, 2)
        self.vol_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.vol_val_label, 1, 3)

        self.ret_range = QRangeSlider(Qt.Horizontal)
        self.ret_range.setMinimum(-100)
        self.ret_range.setMaximum(200)
        self.ret_range.setValue((0, 100))
        self.ret_range.rangeChanged.connect(self.update_chart)
        filter_layout.addWidget(QLabel("Getiri Aralığı:"), 2, 0)
        filter_layout.addWidget(self.ret_range, 2, 1, 1, 2)
        self.ret_val_label = QLabel("0.00 - 1.00")
        filter_layout.addWidget(self.ret_val_label, 2, 3)

        right_panel.addWidget(filter_box)

        # Tablo
        self.table = QTableWidget()
        right_panel.addWidget(self.table)

        self.current_ax = None
        self.toolbar.home = self.reset_home  # Home ikonuna kendi fonksiyonunu bağla
        self.inspect_mode = False  # Inspecting Mode için

        # İnceleme (Inspecting Mode) butonu
        self.inspect_btn = QPushButton(QIcon("search.png"), "İnceleme")
        self.inspect_btn.setCheckable(True)
        self.inspect_btn.setToolTip("Grafikte noktaların üzerine gelince bilgi kutucuğu gösterir")
        self.inspect_btn.setChecked(False)
        self.inspect_btn.clicked.connect(self.toggle_inspect_mode)
        side_layout.addWidget(self.inspect_btn)

        # Lokal/Global butonu
        self.local_global_btn = QPushButton("Lokal")
        self.local_global_btn.setCheckable(True)
        self.local_global_btn.setChecked(True)
        self.local_global_btn.clicked.connect(self.toggle_local_global)
        right_panel.addWidget(self.local_global_btn)
        self.table_mode = "local"  # "local" veya "global"

        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def reset_home(self):
        if self.parent.data is None:
            return

        # Tüm noktaların (annual_std_dev, annual_returns) min/max'ını bul
        all_x = self.annual_std_dev.values
        all_y = self.annual_returns.values
        x_min, x_max = self._orig_vol_min, self._orig_vol_max
        y_min, y_max = self._orig_ret_min, self._orig_ret_max
        ax.set_xlim(x_min - 0.05 * (x_max - x_min), x_max + 0.05 * (x_max - x_min))
        ax.set_ylim(y_min - 0.05 * (y_max - y_min), y_max + 0.05 * (y_max - y_min))

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(self.annual_std_dev, self.annual_returns, c='blue', alpha=0.5, label="Tüm Hisseler", picker=True)
        ax.scatter(self.filtered["Volatilite"], self.filtered["Getiri"], c='red', s=60, label="Filtreli", picker=True)
        for ticker in self.filtered.index:
            ax.annotate(ticker, (self.filtered.loc[ticker, "Volatilite"], self.filtered.loc[ticker, "Getiri"]), fontsize=8, alpha=0.7)
        ax.set_xlabel("Yıllık Volatilite (Risk)")
        ax.set_ylabel("Yıllık Getiri")
        ax.set_title("Risk-Getiri & Sharpe Dağılımı")
        ax.grid(True)
        # Eksenleri tüm noktaları kapsayacak şekilde ayarla
        ax.set_xlim(x_min - 0.05 * (x_max - x_min), x_max + 0.05 * (x_max - x_min))
        ax.set_ylim(y_min - 0.05 * (y_max - y_min), y_max + 0.05 * (y_max - y_min))

        # CML ve Lending/Borrowing açıksa çiz
        if self.cml_show_btn.isChecked():
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            returns = self.parent.data.pct_change().dropna()
            annual_returns, annual_std_dev = calculate_annualized_returns_and_risk(self.parent.data)
            sharpe = calculate_sharpe(returns)
            visible_mask = (annual_std_dev >= xlim[0]) & (annual_std_dev <= xlim[1]) & \
                           (annual_returns >= ylim[0]) & (annual_returns <= ylim[1])
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
        ax.legend()
        self.canvas.draw()
        self.current_ax = ax

    def toggle_inspect_mode(self):
        self.inspect_mode = self.inspect_btn.isChecked()

    def on_hover(self, event):
        if not self.inspect_mode or event.inaxes is None:
            annot = getattr(self, "_annot", None)
            if annot and annot.get_visible():
                annot.set_visible(False)
                self.canvas.draw_idle()
            return

        x, y = event.xdata, event.ydata
        if x is None or y is None:
            annot = getattr(self, "_annot", None)
            if annot and annot.get_visible():
                annot.set_visible(False)
                self.canvas.draw_idle()
            return

        stds = self.annual_std_dev
        rets = self.annual_returns
        dists = np.sqrt((stds - x) ** 2 + (rets - y) ** 2)
        ticker = dists.idxmin()
        if ticker not in dists.index:
            return
        if dists[ticker] > 0.01:
            annot = getattr(self, "_annot", None)
            if annot and annot.get_visible():
                annot.set_visible(False)
                self.canvas.draw_idle()
            return

        std_val = stds[ticker]
        ret_val = rets[ticker]
        sharpe_val = self.sharpe[ticker]
        # Lending/Borrowing durumu
        if hasattr(self, "lending_stocks") and ticker in self.lending_stocks:
            lb_status = "Lending"
        elif hasattr(self, "borrowing_stocks") and ticker in self.borrowing_stocks:
            lb_status = "Borrowing"
        else:
            lb_status = "Normal"

        annot = getattr(self, "_annot", None)
        if annot is None:
            annot = event.inaxes.annotate(
                "", xy=(0,0), xytext=(15,15), textcoords="offset points",
                bbox=dict(boxstyle="round", fc="w"),
                arrowprops=dict(arrowstyle="->"))
            annot.set_visible(False)
            self._annot = annot
        annot.xy = (std_val, ret_val)
        annot.set_text(
            f"{ticker}\n"
            f"Volatilite: {std_val:.3f}\n"
            f"Yıllık Getiri: {ret_val:.3f}\n"
            f"Sharpe: {sharpe_val:.2f}\n"
            f"Durum: {lb_status}"
        )
        annot.set_visible(True)
        self.canvas.draw_idle()

    def on_axes_changed(self, event):
    # Sadece lokal modda tabloyu güncelle
        if self.table_mode == "local":
            self.update_table_view()

    def update_chart(self):
        if self.parent.data is None:
            return

        # Mevcut eksen limitlerini kaydet
        xlim, ylim = None, None
        if self.current_ax is not None:
            xlim = self.current_ax.get_xlim()
            ylim = self.current_ax.get_ylim()

        returns = self.parent.data.pct_change().dropna()
        annual_returns, annual_std_dev = calculate_annualized_returns_and_risk(self.parent.data)
        sharpe = calculate_sharpe(returns)

        self.annual_std_dev = annual_std_dev
        self.annual_returns = annual_returns
        self.sharpe = sharpe

        # Orijinal min/max'ı sadece ilk yüklemede sakla
        if not hasattr(self, "_orig_vol_min"):
            # Her zaman tüm dataya göre hesapla
            all_returns = self.parent.data.pct_change().dropna()
            all_annual_returns, all_annual_std_dev = calculate_annualized_returns_and_risk(self.parent.data)
            self._orig_vol_min = all_annual_std_dev.min()
            self._orig_vol_max = all_annual_std_dev.max()
            self._orig_ret_min = all_annual_returns.min()
            self._orig_ret_max = all_annual_returns.max()

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
        ax.set_title("Risk-Getiri & Sharpe Dağılımı")
        ax.grid(True)

        # Eksen limitlerini tekrar uygula (mevcut zoom/pan korunur)
        if xlim is not None and ylim is not None:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        # --- CML ve Lending/Borrowing çizgileri ---
        self.lending_stocks = []
        self.borrowing_stocks = []
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
                    # Lending ve Borrowing hisselerini belirle
                    self.lending_stocks = visible_sharpe[visible_std <= max_sharpe_risk].index.tolist()
                    self.borrowing_stocks = visible_sharpe[visible_std > max_sharpe_risk].index.tolist()

        ax.legend()
        self.canvas.draw()
        self.current_ax = ax

        self.update_table_view()  # Sadece bu satırı bırak

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

            # Lending/Borrowing highlight
            if hasattr(self, "lending_stocks") and idx in self.lending_stocks:
                for col in range(4):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(Qt.green)
            elif hasattr(self, "borrowing_stocks") and idx in self.borrowing_stocks:
                for col in range(4):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(Qt.yellow)
        self.table.resizeColumnsToContents()

    def add_to_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.add_stock(ticker)
            self.update_table_view()
            # Diğer tabları güncelle
            if hasattr(self.parent, "portfolio_tab"):
                self.parent.portfolio_tab.update_list()
            if hasattr(self.parent, "portfolio_manager_tab"):
                self.parent.portfolio_manager_tab.update_table()
            if hasattr(self.parent, "portfolio_timeseries_tab"):
                self.parent.portfolio_timeseries_tab.update_stock_list()
            if hasattr(self.parent, "covariance_tab"):
                self.parent.covariance_tab.portfolio_combo.clear()
                self.parent.covariance_tab.portfolio_combo.addItem("Tüm Hisseler")
                for name in self.parent.portfolio_manager.get_portfolio_names():
                    self.parent.covariance_tab.portfolio_combo.addItem(name)

    def remove_from_portfolio(self, ticker):
        portfolio = self.portfolio_manager.get_active()
        if portfolio:
            portfolio.remove_stock(ticker)
            self.update_table_view()
            # Diğer tabları güncelle
            if hasattr(self.parent, "portfolio_tab"):
                self.parent.portfolio_tab.update_list()
            if hasattr(self.parent, "portfolio_manager_tab"):
                self.parent.portfolio_manager_tab.update_table()
            if hasattr(self.parent, "portfolio_timeseries_tab"):
                self.parent.portfolio_timeseries_tab.update_stock_list()
            if hasattr(self.parent, "covariance_tab"):
                self.parent.covariance_tab.portfolio_combo.clear()
                self.parent.covariance_tab.portfolio_combo.addItem("Tüm Hisseler")
                for name in self.parent.portfolio_manager.get_portfolio_names():
                    self.parent.covariance_tab.portfolio_combo.addItem(name)

    def toggle_local_global(self):
        # 1. tıklama: lokal, 2. tıklama: global, tekrar tıklama: lokal...
        if self.local_global_btn.isChecked():
            self.local_global_btn.setText("Lokal")
            self.table_mode = "local"
        else:
            self.local_global_btn.setText("Global")
            self.table_mode = "global"
        self.update_table_view()

    def update_table_view(self):
        if self.table_mode == "local":
            # Ekranda görünen min/max volatilite ve getiri aralığında kalan hisseleri bul
            if self.current_ax is not None:
                xlim = self.current_ax.get_xlim()
                ylim = self.current_ax.get_ylim()
                mask = (
                    (self.annual_std_dev >= xlim[0]) & (self.annual_std_dev <= xlim[1]) &
                    (self.annual_returns >= ylim[0]) & (self.annual_returns <= ylim[1])
                )
                local_df = pd.DataFrame({
                    "Sharpe": self.sharpe[mask],
                    "Volatilite": self.annual_std_dev[mask],
                    "Getiri": self.annual_returns[mask]
                })
                self.show_table(local_df)
            else:
                self.show_table(self.filtered)
        else:
            all_df = pd.DataFrame({
                "Sharpe": self.sharpe,
                "Volatilite": self.annual_std_dev,
                "Getiri": self.annual_returns
            })
            self.show_table(all_df)

    def on_chart_right_click(self, event):
        if not self.inspect_mode or event.button() != 3 or event.inaxes is None:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        stds = self.annual_std_dev
        rets = self.annual_returns
        dists = np.sqrt((stds - x) ** 2 + (rets - y) ** 2)
        idx = dists.idxmin()
        ticker = stds.index[idx]
        std_val = stds[ticker]
        ret_val = rets[ticker]
        sharpe_val = self.sharpe[ticker]
        # Buraya istediğin kadar bilgi ekleyebilirsin
        msg = QMessageBox(self)
        msg.setWindowTitle(f"{ticker} Detay")
        msg.setText(
            f"Hisse: {ticker}\n"
            f"Volatilite: {std_val:.3f}\n"
            f"Yıllık Getiri: {ret_val:.3f}\n"
            f"Sharpe: {sharpe_val:.2f}\n"
            f"(Buraya ek bilgi ekleyebilirsin)"
        )
        msg.exec_()