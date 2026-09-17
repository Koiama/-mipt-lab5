"""Средн.10: простейший GUI на PyQt5."""

import sys

from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GreetingWindow(QWidget):
    """Простое PyQt5-окно с интерактивным приветствием."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Средн.10 - PyQt5")
        self.setMinimumSize(480, 220)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите имя")
        self.result = QLabel("Введите имя и нажмите кнопку")
        self.result.setWordWrap(True)

        greet_button = QPushButton("Поприветствовать")
        clear_button = QPushButton("Очистить")
        greet_button.clicked.connect(self.greet)
        clear_button.clicked.connect(self.clear)
        self.name_input.returnPressed.connect(self.greet)

        buttons = QHBoxLayout()
        buttons.addWidget(greet_button)
        buttons.addWidget(clear_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Простейший GUI на PyQt5"))
        layout.addWidget(self.name_input)
        layout.addLayout(buttons)
        layout.addWidget(self.result, stretch=1)
        self.setLayout(layout)

    def greet(self) -> None:
        name = self.name_input.text().strip()
        if name:
            self.result.setText(f"Привет, {name}!")
        else:
            self.result.setText("Сначала введите имя")

    def clear(self) -> None:
        self.name_input.clear()
        self.result.setText("Введите имя и нажмите кнопку")
        self.name_input.setFocus()


def main() -> int:
    app = QApplication(sys.argv)
    window = GreetingWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
