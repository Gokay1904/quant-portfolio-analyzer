from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout
from app.portfolio import PortfolioManager
from app.portfolio_tab import PortfolioTab, PortfolioManagerTab
from app.chart_tab import ChartTab
from app.data_tab import DataTab
from app.covariance_tab import CovarianceTab

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

        self.data_tab = DataTab(self)
        self.tabs.addTab(self.data_tab, "Veri Yükle")
        self.chart_tab = ChartTab(self, self.portfolio_manager)
        self.tabs.addTab(self.chart_tab, "Risk-Getiri Analizi")
        self.portfolio_manager_tab = PortfolioManagerTab(self, self.portfolio_manager)
        self.tabs.addTab(self.portfolio_manager_tab, "Portföy Yöneticisi")
        self.portfolio_tab = PortfolioTab(self.portfolio_manager)
        self.tabs.addTab(self.portfolio_tab, "Portföyler")
        self.covariance_tab = CovarianceTab(self)
        self.tabs.addTab(self.covariance_tab, "Kovaryans Analizi")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        if self.tabs.widget(idx) == self.chart_tab and not self.chart_tab.has_rendered:
            self.chart_tab.update_chart()
            self.chart_tab.has_rendered = True