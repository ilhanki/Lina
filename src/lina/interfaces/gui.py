"""Tkinter desktop interface for Lina."""

from __future__ import annotations

from collections.abc import Callable
import logging
import re
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


_logger = logging.getLogger(__name__)


class LinaGui:
    """Professional Tkinter chat window for Lina."""

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
        self._last_response_text: str = ""
        self._root.title("Lina")
        self._root.geometry("820x660")
        self._root.minsize(540, 440)
        self._message_ranges: list[tuple[str, str]] = []
        self._chat_font = font.Font(family="Segoe UI", size=10)
        self._header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self._status_font = font.Font(family="Segoe UI", size=9)

        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- Header ---
        self._header_frame = ttk.Frame(self._root, padding=(16, 10, 16, 0))
        self._header_frame.grid(row=0, column=0, sticky="ew")

        self._header_label = ttk.Label(
            self._header_frame,
            text="Lina",
            font=self._header_font,
            anchor="w",
        )
        self._header_label.grid(row=0, column=0, sticky="w")

        self._header_subtitle = ttk.Label(
            self._header_frame,
            text="Yapay Zekâ Masaüstü Asistanı",
            anchor="w",
        )
        self._header_subtitle.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._header_frame.columnconfigure(1, weight=1)

        ttk.Separator(self._root, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=16, pady=(6, 0)
        )

        # --- Main content ---
        self._main_frame = ttk.Frame(self._root, padding=(16, 8, 16, 0))
        self._main_frame.grid(row=2, column=0, sticky="nsew")

        self._chat_log = ScrolledText(
            self._main_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=72,
            height=22,
            font=self._chat_font,
            borderwidth=1,
            relief=tk.SOLID,
            padx=10,
            pady=10,
        )
        self._chat_log.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # --- Input row ---
        self._input_frame = ttk.Frame(self._main_frame)
        self._input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        self._message_input = tk.Text(self._input_frame, height=3, width=56)
        self._message_input.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)

        self._send_button = ttk.Button(
            self._input_frame,
            text="Gönder",
            command=self.send_message,
            width=8,
        )
        self._send_button.grid(row=0, column=1, sticky="ew")

        self._input_frame.columnconfigure(0, weight=1)

        # --- Controls row ---
        self._controls_frame = ttk.Frame(self._main_frame)
        self._controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        self._clear_button = ttk.Button(
            self._controls_frame,
            text="Sohbeti Temizle",
            command=self.clear_chat,
            width=14,
        )
        self._clear_button.grid(row=0, column=0, sticky="w")

        self._copy_button = ttk.Button(
            self._controls_frame,
            text="Son Cevabı Kopyala",
            command=self.copy_last_response,
            width=18,
        )
        self._copy_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._controls_frame.columnconfigure(2, weight=1)

        # --- Status bar ---
        ttk.Separator(self._root, orient="horizontal").grid(
            row=3, column=0, sticky="ew", padx=16, pady=(8, 0)
        )

        self._status_frame = ttk.Frame(self._root, padding=(16, 4, 16, 6))
        self._status_frame.grid(row=4, column=0, sticky="ew")

        self._status_text = tk.StringVar(value="Hazır")
        self._status_label = ttk.Label(
            self._status_frame,
            textvariable=self._status_text,
            font=self._status_font,
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w")
        self._status_frame.columnconfigure(0, weight=1)

        # --- Layout weights ---
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(2, weight=1)
        self._main_frame.columnconfigure(0, weight=1)
        self._main_frame.rowconfigure(0, weight=1)

        self._append_message("Lina", format_welcome_message())
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
        self._update_status_text("Cevap bekleniyor...")

        thread = self._thread_factory(
            target=self._generate_response,
            args=(message,),
            daemon=True,
        )
        thread.start()

    def clear_chat(self) -> None:
        """Clear the chat log and message tracking."""
        self._chat_log.configure(state=tk.NORMAL)
        self._chat_log.delete("1.0", tk.END)
        self._chat_log.configure(state=tk.DISABLED)
        self._message_ranges.clear()
        self._last_response_text = ""
        self._append_message("Lina", format_welcome_message())

    def copy_last_response(self) -> None:
        """Copy last Lina response to clipboard."""
        if not self._last_response_text:
            return
        self._root.clipboard_clear()
        self._root.clipboard_append(self._last_response_text)

    def _generate_response(self, message: str) -> None:
        try:
            response = self._conversation_service.handle_message(message)
        except ModelProviderError as error:
            self._root.after(0, self._show_error, error)
            return
        except Exception:
            _logger.exception("Unexpected error while generating GUI response")
            self._root.after(0, self._show_unexpected_error)
            return

        self._root.after(0, self._show_response, response)

    def _show_response(self, response: ModelResponse) -> None:
        self._remove_last_message()
        self._append_message("Lina", response.text)
        self._last_response_text = response.text
        self._set_waiting_state(False)
        self._update_status_text("Hazır")
        self._focus_input()

    def _show_error(self, error: ModelProviderError | None = None) -> None:
        self._remove_last_message()
        error_text = format_error_message(error)
        self._append_message("Lina", error_text)
        self._last_response_text = error_text
        self._set_waiting_state(False)
        self._update_status_text("Bağlantı hatası")
        self._focus_input()

    def _show_unexpected_error(self) -> None:
        self._remove_last_message()
        error_text = format_unexpected_error_message()
        self._append_message("Lina", error_text)
        self._last_response_text = error_text
        self._set_waiting_state(False)
        self._update_status_text("Hata oluştu")
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
        start_index = self._chat_log.index("end-1c")
        self._chat_log.insert("end-1c", format_chat_message(sender, message))
        end_index = self._chat_log.index("end-1c")
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

    def _on_close(self) -> None:
        """Handle window close gracefully."""
        self._root.destroy()

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
    return f"{sender}:\n{normalize_chat_message(sender, message)}\n\n"


def normalize_chat_message(sender: str, message: str) -> str:
    text = message.strip()
    sender_name = sender.strip()
    if not sender_name:
        return text

    label_pattern = re.compile(
        rf"^(?:{re.escape(sender_name)}\s*:\s*)+",
        re.IGNORECASE,
    )
    previous_text = None
    while previous_text != text:
        previous_text = text
        text = label_pattern.sub("", text).strip()

    return text


def format_error_message(error: ModelProviderError | None = None) -> str:
    if error is not None:
        error_text = str(error).lower()
        if "not configured" in error_text:
            return "Model adı yapılandırılmamış. Lütfen config/default.toml dosyasını kontrol edin."
        if "http error: 404" in error_text or "not found" in error_text:
            return "Yapılandırılmış model Ollama içinde bulunamadı. Model adını ve yüklü modelleri kontrol edin."
        if "timed out" in error_text or "timeout" in error_text:
            return "Ollama yanıt vermedi. Bağlantı zaman aşımına uğradı."
        if "network error" in error_text or "connection refused" in error_text:
            return "Ollama'ya ulaşılamıyor. Ollama çalışıyor mu kontrol edin."
        if "request failed" in error_text:
            return "Ollama isteği tamamlanamadı. Lütfen Ollama durumunu ve model ayarlarını kontrol edin."

    return (
        "Modele ulaşılamadı. Lütfen Ollama'nın çalıştığından "
        "ve yapılandırılmış modelin yüklü olduğundan emin olun."
    )


def format_unexpected_error_message() -> str:
    return (
        "Beklenmeyen bir hata oluştu. İşlem tamamlanamadı ama arayüz "
        "kullanıma hazır."
    )


def format_welcome_message() -> str:
    return (
        "Merhaba İlhan! Ben Lina, yapay zekâ masaüstü asistanın.\n"
        "Sana nasıl yardımcı olabilirim?"
    )
