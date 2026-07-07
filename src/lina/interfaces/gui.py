"""Tkinter desktop interface for Lina."""

from collections.abc import Callable
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.services.conversation_service import ConversationService


class LinaGui:
    """Simple Tkinter chat window for Lina."""

    def __init__(
        self,
        conversation_service: ConversationService,
        root: tk.Tk | None = None,
        thread_factory: Callable[..., threading.Thread] = threading.Thread,
    ) -> None:
        self._conversation_service = conversation_service
        self._root = root or tk.Tk()
        self._thread_factory = thread_factory
        self._is_waiting_for_response = False
        self._root.title("Lina")
        self._root.geometry("780x620")
        self._root.minsize(520, 420)

        self._main_frame = ttk.Frame(self._root, padding=16)
        self._main_frame.grid(row=0, column=0, sticky="nsew")

        self._chat_log = ScrolledText(
            self._main_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=72,
            height=24,
        )
        self._chat_log.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self._message_input = tk.Text(self._main_frame, height=3, width=56)
        self._message_input.grid(row=1, column=0, padx=(0, 10), pady=(12, 0), sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)

        self._send_button = ttk.Button(
            self._main_frame,
            text="Gönder",
            command=self.send_message,
        )
        self._send_button.grid(row=1, column=1, pady=(12, 0), sticky="ew")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        self._main_frame.columnconfigure(0, weight=1)
        self._main_frame.columnconfigure(1, weight=0)
        self._main_frame.rowconfigure(0, weight=1)

        self._append_message("Lina", "Merhaba İlhan. Hazırım.")

    def run(self) -> None:
        self._root.mainloop()

    def send_message(self) -> None:
        if self._is_waiting_for_response:
            return

        message = self._get_input_text()
        if not message:
            return

        self._clear_input()
        self._append_message("İlhan", message)
        self._append_message("Lina", "yazıyor...")
        self._set_waiting_state(True)

        thread = self._thread_factory(
            target=self._generate_response,
            args=(message,),
            daemon=True,
        )
        thread.start()

    def _generate_response(self, message: str) -> None:
        try:
            response = self._conversation_service.handle_message(message)
        except ModelProviderError:
            self._root.after(0, self._show_error)
            return

        self._root.after(0, self._show_response, response)

    def _show_response(self, response: ModelResponse) -> None:
        self._remove_last_message()
        self._append_message("Lina", response.text)
        self._set_waiting_state(False)

    def _show_error(self) -> None:
        self._remove_last_message()
        self._append_message("Lina", format_error_message())
        self._set_waiting_state(False)

    def _handle_enter(self, event: tk.Event) -> str:
        self.send_message()
        return "break"

    def _get_input_text(self) -> str:
        return self._message_input.get("1.0", tk.END).strip()

    def _clear_input(self) -> None:
        self._message_input.delete("1.0", tk.END)

    def _append_message(self, sender: str, message: str) -> None:
        self._chat_log.configure(state=tk.NORMAL)
        self._chat_log.insert(tk.END, format_chat_message(sender, message))
        self._chat_log.configure(state=tk.DISABLED)
        self._chat_log.see(tk.END)

    def _remove_last_message(self) -> None:
        self._chat_log.configure(state=tk.NORMAL)
        self._chat_log.delete("end-3l", tk.END)
        self._chat_log.configure(state=tk.DISABLED)

    def _set_waiting_state(self, is_waiting: bool) -> None:
        self._is_waiting_for_response = is_waiting
        state = tk.DISABLED if is_waiting else tk.NORMAL
        self._message_input.configure(state=state)
        self._send_button.configure(state=state)


def format_chat_message(sender: str, message: str) -> str:
    return f"{sender}: {message.strip()}\n\n"


def format_error_message() -> str:
    return "Lina şu anda modele ulaşamadı. Ollama çalışıyor mu kontrol edebilir misin?"
