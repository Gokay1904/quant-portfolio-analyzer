from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QListWidget, QInputDialog, QMenu
from PyQt5.QtCore import Qt, QPoint

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

        # Portföy ekleme arayüzü
        row = QHBoxLayout()
        self.name_input = QLineEdit()
        row.addWidget(QLabel("Yeni Portföy Adı:"))
        row.addWidget(self.name_input)
        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self.add_portfolio)
        row.addWidget(self.add_btn)
        self.layout.addLayout(row)

        # Portföyleri gösteren tablo
        self.table = QTableWidget()
        self.layout.addWidget(self.table)
        self.update_table()

    def update_table(self):
        portfolios = self.portfolio_manager.get_portfolio_names()
        self.table.setRowCount(len(portfolios))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Portföy Adı", "Aktif Yap"])
        for i, name in enumerate(portfolios):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            btn = QPushButton("Aktif Yap")
            btn.clicked.connect(lambda _, n=name: self.set_active(n))
            self.table.setCellWidget(i, 1, btn)
        self.table.resizeColumnsToContents()

    def add_portfolio(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Portföy adı boş olamaz.")
            return
        self.portfolio_manager.create_portfolio(name)
        self.update_table()
        if hasattr(self.parent, "portfolio_tab"):
            self.parent.portfolio_tab.update_portfolio_list()
        self.name_input.clear()

    def set_active(self, name):
        self.portfolio_manager.set_active(name)
        QMessageBox.information(self, "Bilgi", f"{name} aktif portföy olarak seçildi.")
        if hasattr(self.parent, "portfolio_tab"):
            self.parent.portfolio_tab.update_list()

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