"""Повыш.10: локальный чат по TCP с GUI на Tkinter."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable

MAX_PACKET_SIZE = 16_384


@dataclass(frozen=True)
class ChatMessage:
    """Сообщение локального чата."""

    nickname: str
    text: str
    kind: str = "message"

    def __post_init__(self) -> None:
        if self.kind not in {"message", "system"}:
            raise ValueError("Недопустимый тип сообщения")
        if not self.nickname.strip():
            raise ValueError("Имя не должно быть пустым")
        if not self.text.strip():
            raise ValueError("Текст не должен быть пустым")


def encode_message(message: ChatMessage) -> bytes:
    """Кодирует сообщение в одну JSON-строку UTF-8."""
    payload = json.dumps(asdict(message), ensure_ascii=False, separators=(",", ":"))
    data = payload.encode("utf-8") + b"\n"
    if len(data) > MAX_PACKET_SIZE:
        raise ValueError("Сообщение слишком длинное")
    return data


def decode_message(data: bytes) -> ChatMessage:
    """Декодирует одну JSON-строку в ChatMessage."""
    if len(data) > MAX_PACKET_SIZE:
        raise ValueError("Сообщение слишком длинное")
    payload = json.loads(data.decode("utf-8").strip())
    return ChatMessage(
        nickname=str(payload["nickname"]),
        text=str(payload["text"]),
        kind=str(payload.get("kind", "message")),
    )


class ChatServer:
    """Небольшой TCP-сервер, рассылающий сообщения всем клиентам."""

    def __init__(self, host: str, port: int, on_event: Callable[[str], None]) -> None:
        self.host = host
        self.port = port
        self.on_event = on_event
        self._socket: socket.socket | None = None
        self._clients: set[socket.socket] = set()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Сервер уже запущен")

        self._stop_event.clear()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen()
        self._socket.settimeout(0.5)
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        self.on_event(f"Сервер запущен на {self.host}:{self.port}")

    def _accept_loop(self) -> None:
        assert self._socket is not None
        while not self._stop_event.is_set():
            try:
                client, _address = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client.settimeout(0.5)
            with self._lock:
                self._clients.add(client)
            threading.Thread(target=self._client_loop, args=(client,), daemon=True).start()

    def _client_loop(self, client: socket.socket) -> None:
        buffer = b""
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = client.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buffer += chunk
                if len(buffer) > MAX_PACKET_SIZE * 2:
                    break
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line:
                        continue
                    try:
                        decode_message(line)
                    except (UnicodeDecodeError, ValueError, KeyError, json.JSONDecodeError):
                        continue
                    self.broadcast(line + b"\n")
        finally:
            self._remove_client(client)

    def broadcast(self, packet: bytes) -> None:
        dead_clients: list[socket.socket] = []
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            try:
                client.sendall(packet)
            except OSError:
                dead_clients.append(client)
        for client in dead_clients:
            self._remove_client(client)

    def _remove_client(self, client: socket.socket) -> None:
        with self._lock:
            self._clients.discard(client)
        try:
            client.close()
        except OSError:
            pass

    def stop(self) -> None:
        self._stop_event.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        with self._lock:
            clients = list(self._clients)
            self._clients.clear()
        for client in clients:
            try:
                client.close()
            except OSError:
                pass
        self.on_event("Сервер остановлен")


class ChatClient:
    """TCP-клиент с фоновым чтением сообщений."""

    def __init__(self, on_message: Callable[[ChatMessage], None], on_event: Callable[[str], None]):
        self.on_message = on_message
        self.on_event = on_event
        self._socket: socket.socket | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def connect(self, host: str, port: int) -> None:
        if self.connected:
            raise RuntimeError("Клиент уже подключён")
        sock = socket.create_connection((host, port), timeout=3)
        sock.settimeout(0.5)
        self._socket = sock
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        self.on_event(f"Подключено к {host}:{port}")

    def send(self, message: ChatMessage) -> None:
        if self._socket is None:
            raise ConnectionError("Нет подключения к серверу")
        self._socket.sendall(encode_message(message))

    def _receive_loop(self) -> None:
        assert self._socket is not None
        buffer = b""
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = self._socket.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    self.on_event("Сервер закрыл соединение")
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line:
                        continue
                    try:
                        message = decode_message(line)
                    except (UnicodeDecodeError, ValueError, KeyError, json.JSONDecodeError):
                        self.on_event("Получено некорректное сообщение")
                        continue
                    self.on_message(message)
        except OSError as exc:
            if not self._stop_event.is_set():
                self.on_event(f"Ошибка сети: {exc}")
        finally:
            self.disconnect(notify=False)

    def disconnect(self, notify: bool = True) -> None:
        self._stop_event.set()
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        if notify:
            self.on_event("Отключено")


class LocalChatApp(tk.Tk):
    """GUI, который может запустить сервер или подключиться к нему."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Повыш.10 - локальный чат")
        self.geometry("820x560")
        self.minsize(620, 420)
        self.resizable(True, True)

        self.nickname_var = tk.StringVar(value="Ксения")
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="5050")
        self.message_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Не подключено")

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.server: ChatServer | None = None
        self.client = ChatClient(self._queue_message, self._queue_status)

        self._build_ui()
        self.after(100, self._process_events)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        connection = ttk.LabelFrame(root, text="Подключение", padding=8)
        connection.grid(row=0, column=0, sticky="ew")
        for column in range(6):
            connection.columnconfigure(column, weight=1 if column in {1, 3} else 0)

        ttk.Label(connection, text="Имя:").grid(row=0, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.nickname_var).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(4, 12),
        )
        ttk.Label(connection, text="Адрес:").grid(row=0, column=2, sticky="w")
        ttk.Entry(connection, textvariable=self.host_var).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(4, 12),
        )
        ttk.Label(connection, text="Порт:").grid(row=0, column=4, sticky="w")
        ttk.Entry(connection, textvariable=self.port_var, width=8).grid(
            row=0,
            column=5,
            sticky="ew",
            padx=(4, 0),
        )

        buttons = ttk.Frame(root)
        buttons.grid(row=1, column=0, sticky="w", pady=8)
        ttk.Button(buttons, text="Запустить сервер", command=self.start_server).pack(side="left")
        ttk.Button(buttons, text="Подключиться", command=self.connect_client).pack(
            side="left",
            padx=(8, 0),
        )
        ttk.Button(buttons, text="Отключиться", command=self.disconnect_client).pack(
            side="left",
            padx=(8, 0),
        )

        self.chat = scrolledtext.ScrolledText(root, wrap="word", state="disabled")
        self.chat.grid(row=2, column=0, sticky="nsew")

        sender = ttk.Frame(root)
        sender.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        sender.columnconfigure(0, weight=1)
        entry = ttk.Entry(sender, textvariable=self.message_var)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", lambda _event: self.send_message())
        ttk.Button(sender, text="Отправить", command=self.send_message).grid(
            row=0,
            column=1,
            padx=(8, 0),
        )

        ttk.Label(root, textvariable=self.status_var, anchor="w").grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

    def _validated_endpoint(self) -> tuple[str, int]:
        host = self.host_var.get().strip()
        if not host:
            raise ValueError("Адрес не должен быть пустым")
        try:
            port = int(self.port_var.get())
        except ValueError as exc:
            raise ValueError("Порт должен быть целым числом") from exc
        if not 1 <= port <= 65535:
            raise ValueError("Порт должен быть от 1 до 65535")
        return host, port

    def start_server(self) -> None:
        try:
            host, port = self._validated_endpoint()
            if self.server is not None:
                raise RuntimeError("Сервер уже запущен")
            server = ChatServer(host, port, self._queue_status)
            server.start()
            self.server = server
        except (ValueError, RuntimeError, OSError) as exc:
            messagebox.showerror("Не удалось запустить сервер", str(exc), parent=self)

    def connect_client(self) -> None:
        try:
            host, port = self._validated_endpoint()
            self.client.connect(host, port)
        except (ValueError, RuntimeError, OSError) as exc:
            messagebox.showerror("Не удалось подключиться", str(exc), parent=self)

    def disconnect_client(self) -> None:
        self.client.disconnect()

    def send_message(self) -> None:
        try:
            message = ChatMessage(
                nickname=self.nickname_var.get(),
                text=self.message_var.get(),
            )
            self.client.send(message)
        except (ValueError, ConnectionError, OSError) as exc:
            self.status_var.set(str(exc))
            return
        self.message_var.set("")

    def _queue_message(self, message: ChatMessage) -> None:
        self.events.put(("message", message))

    def _queue_status(self, text: str) -> None:
        self.events.put(("status", text))

    def _process_events(self) -> None:
        try:
            while True:
                event_type, payload = self.events.get_nowait()
                if event_type == "message" and isinstance(payload, ChatMessage):
                    self._append_message(payload)
                elif event_type == "status":
                    self.status_var.set(str(payload))
        except queue.Empty:
            pass
        self.after(100, self._process_events)

    def _append_message(self, message: ChatMessage) -> None:
        prefix = "[система]" if message.kind == "system" else f"[{message.nickname}]"
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{prefix} {message.text}\n")
        self.chat.see(tk.END)
        self.chat.configure(state="disabled")

    def close(self) -> None:
        self.client.disconnect(notify=False)
        if self.server is not None:
            self.server.stop()
        self.destroy()


def main() -> None:
    app = LocalChatApp()
    app.mainloop()


if __name__ == "__main__":
    main()
