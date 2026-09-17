"""Повыш.3: игра «Кликер» с таймером, счётом и рекордом."""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass
class ClickerGame:
    """Состояние игры без зависимости от GUI."""

    duration: int = 10
    score: int = 0
    best_score: int = 0
    remaining: int = 10
    active: bool = False

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("Длительность игры должна быть положительной")
        self.remaining = self.duration

    def start(self) -> None:
        self.score = 0
        self.remaining = self.duration
        self.active = True

    def click(self) -> int:
        if not self.active:
            return self.score
        self.score += 1
        self.best_score = max(self.best_score, self.score)
        return self.score

    def tick(self) -> int:
        if not self.active:
            return self.remaining

        self.remaining = max(0, self.remaining - 1)
        if self.remaining == 0:
            self.active = False
        return self.remaining


class ClickerApp(tk.Tk):
    """Графический интерфейс игры «Кликер»."""

    def __init__(self, duration: int = 10) -> None:
        super().__init__()
        self.title("Повыш.3 - Кликер")
        self.minsize(500, 330)
        self.resizable(True, True)

        self.game = ClickerGame(duration=duration)
        self.score_var = tk.StringVar(value="Счёт: 0")
        self.best_var = tk.StringVar(value="Рекорд: 0")
        self.time_var = tk.StringVar(value=f"Осталось: {duration} с")
        self.status_var = tk.StringVar(value="Нажмите «Старт»")
        self.timer_id: str | None = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        ttk.Label(frame, text="Игра «Кликер»", font=("TkDefaultFont", 16, "bold")).grid(
            row=0,
            column=0,
            pady=(0, 10),
        )

        stats = ttk.Frame(frame)
        stats.grid(row=1, column=0, sticky="ew")
        stats.columnconfigure((0, 1, 2), weight=1)
        ttk.Label(stats, textvariable=self.score_var, anchor="center").grid(row=0, column=0)
        ttk.Label(stats, textvariable=self.time_var, anchor="center").grid(row=0, column=1)
        ttk.Label(stats, textvariable=self.best_var, anchor="center").grid(row=0, column=2)

        self.progress = ttk.Progressbar(
            frame,
            maximum=self.game.duration,
            value=self.game.duration,
        )
        self.progress.grid(row=2, column=0, sticky="ew", pady=12)

        self.click_button = ttk.Button(frame, text="КЛИК!", command=self.register_click)
        self.click_button.grid(row=3, column=0, sticky="nsew", ipadx=20, ipady=30)
        self.click_button.state(["disabled"])

        ttk.Button(frame, text="Старт / заново", command=self.start_game).grid(
            row=4,
            column=0,
            pady=(12, 6),
        )
        ttk.Label(frame, textvariable=self.status_var, anchor="center").grid(
            row=5,
            column=0,
            sticky="ew",
        )

    def start_game(self) -> None:
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

        self.game.start()
        self.click_button.state(["!disabled"])
        self.status_var.set("Игра идёт. Кликайте как можно быстрее!")
        self._refresh()
        self.timer_id = self.after(1000, self._tick)

    def register_click(self) -> None:
        self.game.click()
        self._refresh()

    def _tick(self) -> None:
        self.timer_id = None
        self.game.tick()
        self._refresh()
        if self.game.active:
            self.timer_id = self.after(1000, self._tick)
        else:
            self.click_button.state(["disabled"])
            self.status_var.set(f"Время вышло. Результат: {self.game.score}")

    def _refresh(self) -> None:
        self.score_var.set(f"Счёт: {self.game.score}")
        self.best_var.set(f"Рекорд: {self.game.best_score}")
        self.time_var.set(f"Осталось: {self.game.remaining} с")
        self.progress["value"] = self.game.remaining

    def close(self) -> None:
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
        self.destroy()


def main() -> None:
    app = ClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
