"""Средн.8: диалог выбора файла и безопасный просмотр текста."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

MAX_FILE_SIZE = 1_000_000


def read_text_file(path: str | Path, max_size: int = MAX_FILE_SIZE) -> str:
    """Читает UTF-8 файл, ограничивая размер загружаемых данных."""
    file_path = Path(path)
    with file_path.open("rb") as stream:
        data = stream.read(max_size + 1)

    if len(data) > max_size:
        raise ValueError(f"Файл больше допустимого размера {max_size} байт")

    return data.decode("utf-8")


class FileViewerApp(tk.Tk):
    """Окно с диалогом выбора файла и областью предпросмотра."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Средн.8 - выбор и просмотр файла")
        self.geometry("760x480")
        self.minsize(520, 320)
        self.resizable(True, True)

        self.path_var = tk.StringVar(value="Файл не выбран")
        self.status_var = tk.StringVar(value="Готово")
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(toolbar, text="Выбрать файл", command=self.choose_file).pack(side="left")
        ttk.Button(toolbar, text="Очистить", command=self.clear).pack(side="left", padx=(8, 0))

        ttk.Label(frame, textvariable=self.path_var).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 8),
        )

        self.text = scrolledtext.ScrolledText(frame, wrap="word", font=("TkFixedFont", 10))
        self.text.grid(row=2, column=0, sticky="nsew")

        ttk.Label(frame, textvariable=self.status_var, anchor="w").grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")),
        )
        if not path:
            self.status_var.set("Выбор файла отменён")
            return

        try:
            content = read_text_file(path)
        except FileNotFoundError:
            self._show_error("Файл больше не существует")
        except PermissionError:
            self._show_error("Нет прав для чтения выбранного файла")
        except UnicodeDecodeError:
            self._show_error("Файл не является текстом в кодировке UTF-8")
        except ValueError as exc:
            self._show_error(str(exc))
        except OSError as exc:
            self._show_error(f"Ошибка ввода-вывода: {exc}")
        else:
            self.path_var.set(path)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.status_var.set(f"Загружено символов: {len(content)}")

    def _show_error(self, message: str) -> None:
        self.status_var.set(message)
        messagebox.showerror("Не удалось открыть файл", message, parent=self)

    def clear(self) -> None:
        self.path_var.set("Файл не выбран")
        self.text.delete("1.0", tk.END)
        self.status_var.set("Просмотр очищен")


def main() -> None:
    app = FileViewerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
