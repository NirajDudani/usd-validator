from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hello World Application")

        container = QWidget()
        self.setCentralWidget(container)

        layout = QHBoxLayout(container)

        label1 = QLabel("One")
        label1.setAlignment(Qt.AlignCenter)

        label2 = QLabel("Two")
        label2.setAlignment(Qt.AlignCenter)

        label3 = QLabel("Three")
        label3.setAlignment(Qt.AlignCenter)

        label4 = QLabel("Four")
        label4.setAlignment(Qt.AlignCenter)

        layout.addWidget(label1)
        layout.addWidget(label2)
        layout.addWidget(label3)
        layout.addWidget(label4)
        

app = QApplication()

window = MainWindow()
window.show()

app.exec()