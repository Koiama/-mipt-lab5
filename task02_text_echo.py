"""Средн.2: текстовое поле и кнопка, выводящая введённый текст."""

import tkinter as tk
from tkinter import ttk


class TextEchoApp(tk.Tk):
    """Небольшое окно для вывода текста из поля ввода."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Средн.2 - вывод текста")
        self.minsize(460, 220)
        self.resizable(True, True)

        self.input_var = tk.StringVar()
        self.result_var = tk.StringVar(value="Здесь появится введённый текст")
        self.status_var = tk.StringVar(value="Введите текст и нажмите кнопку")

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        ttk.Label(frame, text="Введите сообщение:").grid(row=0, column=0, sticky="w")

        entry = ttk.Entry(frame, textvariable=self.input_var)
        entry.grid(row=1, column=0, sticky="ew", pady=(6, 12))
        entry.bind("<Return>", lambda _event: self.show_text())
        entry.focus_set()

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, sticky="w", pady=(0, 12))
        ttk.Button(buttons, text="Показать", command=self.show_text).pack(side="left")
        ttk.Button(buttons, text="Очистить", command=self.clear).pack(side="left", padx=(8, 0))

        result = ttk.Label(
            frame,
            textvariable=self.result_var,
            anchor="center",
            justify="center",
            relief="groove",
            padding=12,
        )
        result.grid(row=3, column=0, sticky="nsew")

        ttk.Label(frame, textvariable=self.status_var, anchor="w").grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

    def show_text(self) -> None:
        """Показывает непустой текст из поля ввода."""
        text = self.input_var.get().strip()
        if not text:
            self.result_var.set("Нечего выводить")
            self.status_var.set("Поле ввода пустое")
            return

        self.result_var.set(text)
        self.status_var.set(f"Выведено символов: {len(text)}")

    def clear(self) -> None:
        """Очищает поле ввода и результат."""
        self.input_var.set("")
        self.result_var.set("Здесь появится введённый текст")
        self.status_var.set("Поле очищено")


def main() -> None:
    app = TextEchoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
