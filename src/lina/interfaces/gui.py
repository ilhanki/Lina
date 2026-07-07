"""Tkinter desktop interface for Lina."""

from __future__ import annotations

from collections.abc import Callable
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.services.conversation_service import ConversationService
from lina.services.model_diagnostics_service import (
    ModelDiagnosticsService,
    ModelStatus,
    format_status_message,
)

if TYPE_CHECKING:
    from lina.services.model_diagnostics_service import DiagnosticsResult


class LinaGui:
    """Simple Tkinter chat window for Lina."""

    def __init__(
        self,
        conversation_service: ConversationService,
        root: tk.Tk | None = None,
        thread_factory: Callable[..., threading.Thread] = threading.Thread,
        diagnostics_service: ModelDiagnosticsService | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._root = root or tk.Tk()
        self._thread_factory = thread_factory
        self._diagnostics_service = diagnostics_service
        self._is_waiting_for_response = False
        self._root.title("Lina")
        self._root.geometry("780x620")
        self._root.minsize(520, 420)
        self._message_ranges: list[tuple[str, str]] = []
        self._chat_font = font.Font(family="Segoe UI", size=10)

        self._main_frame = ttk.Frame(self._root, padding=16)
        self._main_frame.grid(row=0, column=0, sticky="nsew")

        self._chat_log = ScrolledText(
            self._main_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=72,
            height=24,
            font=self._chat_font,
            borderwidth=1,
            relief=tk.SOLID,
            padx=10,
            pady=10,
        )
        self._chat_log.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self._message_input = tk.Text(self._main_frame, height=3, width=56)
        self._message_input.grid(row=2, column=0, padx=(0, 10), pady=(12, 0), sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)

        self._send_button = ttk.Button(
            self._main_frame,
            text="Gönder",
            command=self.send_message,
        )
        self._send_button.grid(row=2, column=1, pady=(12, 0), sticky="ew")

        self._status_text = tk.StringVar(value="")
        self._status_label = ttk.Label(
            self._main_frame,
            textvariable=self._status_text,
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        self._main_frame.columnconfigure(0, weight=1)
        self._main_frame.columnconfigure(1, weight=0)
        self._main_frame.rowconfigure(1, weight=1)

        self._append_message("Lina", "Merhaba İlhan. Hazırım.")
        self._message_input.focus_set()
        self._run_initial_diagnostics()

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
        self._append_message("Lina", "Yazıyor...")
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
        self._focus_input()

    def _show_error(self) -> None:
        self._remove_last_message()
        self._append_message("Lina", format_error_message())
        self._set_waiting_state(False)
        self._focus_input()

    def _handle_enter(self, event: tk.Event) -> str:
        self.send_message()
        return "break"

    def _get_input_text(self) -> str:
        return self._message_input.get("1.0", tk.END).strip()

    def _clear_input(self) -> None:
        self._message_input.delete("1.0", tk.END)

    def _append_message(self, sender: str, message: str) -> None:
        self._chat_log.configure(state=tk.NORMAL)
        start_index = self._chat_log.index(tk.END)
        self._chat_log.insert(tk.END, format_chat_message(sender, message))
        end_index = self._chat_log.index(tk.END)
        self._message_ranges.append((start_index, end_index))
        self._chat_log.configure(state=tk.DISABLED)
        self._chat_log.see(tk.END)

    def _remove_last_message(self) -> None:
        if not self._message_ranges:
            return

        start_index, end_index = self._message_ranges.pop()
        self._chat_log.configure(state=tk.NORMAL)
        self._chat_log.delete(start_index, end_index)
        self._chat_log.configure(state=tk.DISABLED)
        self._chat_log.see(tk.END)

    def _set_waiting_state(self, is_waiting: bool) -> None:
        self._is_waiting_for_response = is_waiting
        state = tk.DISABLED if is_waiting else tk.NORMAL
        self._message_input.configure(state=state)
        self._send_button.configure(state=state)

    def _focus_input(self) -> None:
        self._message_input.focus_set()

    def _run_initial_diagnostics(self) -> None:
        if self._diagnostics_service is None:
            return

        self._update_status_text("Modele bağlanılıyor...")
        thread = self._thread_factory(
            target=self._check_diagnostics,
            args=(),
            daemon=True,
        )
        thread.start()

    def _check_diagnostics(self) -> None:
        if self._diagnostics_service is None:
            return

        result = self._diagnostics_service.check_status()
        message = format_status_message(result)
        self._root.after(0, self._update_status_text, message)

    def _update_status_text(self, text: str) -> None:
        self._status_text.set(text)


def format_chat_message(sender: str, message: str) -> str:
    return f"{sender}:\n{message.strip()}\n\n"


def format_error_message() -> str:
    return "Lina şu anda modele ulaşamadı. Ollama çalışıyor mu kontrol edebilir misin?"
