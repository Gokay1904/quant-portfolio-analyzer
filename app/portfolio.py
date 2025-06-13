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