from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem
import pandas as pd

class DataTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.load_btn = QPushButton("CSV Yükle")
        self.load_btn.clicked.connect(self.load_csv)
        self.layout.addWidget(self.load_btn)

        self.clear_btn = QPushButton("Veriyi Temizle")
        self.clear_btn.clicked.connect(self.clear_data)
        self.layout.addWidget(self.clear_btn)

        self.data_label = QLabel("Henüz veri yüklenmedi.")
        self.layout.addWidget(self.data_label)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

    def load_csv(self):
        fname, _ = QFileDialog.getOpenFileName(self, "CSV Dosyası Seç", "", "CSV Files (*.csv)")
        if fname:
            data = pd.read_csv(fname, index_col=0, parse_dates=True)
            self.parent.data = data
            self.data_label.setText(f"Yüklendi: {fname}")
            self.show_table(data)

    def clear_data(self):
        self.parent.data = None
        self.data_label.setText("Veri temizlendi.")
        self.table.clear()

    def show_table(self, data):
        self.table.clear()
        self.table.setRowCount(min(20, len(data)))
        self.table.setColumnCount(len(data.columns))
        self.table.setHorizontalHeaderLabels([str(col) for col in data.columns])
        for i in range(min(20, len(data))):
            for j, col in enumerate(data.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(data.iloc[i, j])))
        self.table.resizeColumnsToContents()