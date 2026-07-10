"""Tkinter desktop interface for Lina."""

from __future__ import annotations

from collections.abc import Callable
import logging
from pathlib import Path
import re
import threading
import tkinter as tk
from tkinter import font
from tkinter import ttk
from typing import TYPE_CHECKING

from lina.brain.model_provider import ModelProviderError, ModelResponse
from lina.services.conversation_service import ConversationService
from lina.services.model_diagnostics_service import (
    ModelDiagnosticsService,
    format_status_message,
)
from lina.speech.models import SpeechServiceError, SpeechTranscriptionResult
from lina.speech.service import SpeechService

if TYPE_CHECKING:
    from lina.services.model_diagnostics_service import DiagnosticsResult


_logger = logging.getLogger(__name__)

APP_VERSION = "v0.5.1-alpha"

COLOR_BG = "#111318"
COLOR_SIDEBAR = "#0b0d12"
COLOR_PANEL = "#171a21"
COLOR_CHAT_BG = "#111318"
COLOR_INPUT_BG = "#20242d"
COLOR_ASSISTANT_BUBBLE = "#242933"
COLOR_USER_BUBBLE = "#2f5cff"
COLOR_TEXT = "#f4f7fb"
COLOR_MUTED = "#9aa4b2"
COLOR_ACCENT = "#5b8cff"
COLOR_BORDER = "#2d3440"
COLOR_BUTTON = "#252a34"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRANDING_LOGO_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-logo.png"
BRANDING_ICON_PATH = PROJECT_ROOT / "assets" / "branding" / "lina-icon.png"


class LinaGui:
    """Professional Tkinter chat window for Lina."""

    def __init__(
        self,
        conversation_service: ConversationService,
        root: tk.Tk | None = None,
        thread_factory: Callable[..., threading.Thread] = threading.Thread,
        diagnostics_service: ModelDiagnosticsService | None = None,
        speech_service: SpeechService | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._root = root or tk.Tk()
        self._thread_factory = thread_factory
        self._diagnostics_service = diagnostics_service
        self._speech_service = speech_service
        self._is_waiting_for_response = False
        self._last_response_text: str = ""
        self._input_history: list[str] = []
        self._input_history_index = 0
        self._root.title("Lina")
        self._root.geometry("1080x720")
        self._root.minsize(840, 560)
        self._message_ranges: list[tuple[str, str]] = []
        self._message_widgets: list[tk.Widget] = []
        self._chat_font = font.Font(family="Segoe UI", size=10)
        self._header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self._title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self._status_font = font.Font(family="Segoe UI", size=9)
        self._logo_image: tk.PhotoImage | None = None
        self._icon_image: tk.PhotoImage | None = None

        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._load_branding_assets()
        self._configure_theme()
        self._build_sidebar()
        self._build_main_area()

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

        self._record_input_history(message)
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
        if hasattr(self, "_messages_frame"):
            for widget in list(self._message_widgets):
                widget.destroy()
            self._message_widgets.clear()
        elif hasattr(self, "_chat_log"):
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

    def _load_branding_assets(self) -> None:
        self._logo_image = self._load_photo_image(BRANDING_LOGO_PATH, max_size=72)
        self._icon_image = self._load_photo_image(BRANDING_ICON_PATH, max_size=48)
        if self._icon_image is None:
            self._icon_image = self._logo_image

        if self._icon_image is None:
            return

        try:
            self._root.iconphoto(True, self._icon_image)
        except tk.TclError:
            _logger.debug("Window icon is not supported on this platform")

    def _load_photo_image(self, path: Path, max_size: int) -> tk.PhotoImage | None:
        if not path.exists():
            return None

        try:
            image = tk.PhotoImage(file=str(path))
        except (OSError, tk.TclError):
            _logger.debug("Could not load branding image: %s", path)
            return None

        scale = max(1, image.width() // max_size, image.height() // max_size)
        if scale == 1:
            return image
        return image.subsample(scale, scale)

    def _configure_theme(self) -> None:
        self._root.configure(bg=COLOR_BG)
        style = ttk.Style(self._root)
        style.configure("Lina.TFrame", background=COLOR_BG)
        style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("Lina.TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
        style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_MUTED)
        style.configure("Sidebar.TLabel", background=COLOR_SIDEBAR, foreground=COLOR_TEXT)
        style.configure("SidebarMuted.TLabel", background=COLOR_SIDEBAR, foreground=COLOR_MUTED)
        style.configure("Panel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT)
        style.configure("Lina.TButton", padding=(10, 6))

    def _build_sidebar(self) -> None:
        self._sidebar = tk.Frame(self._root, bg=COLOR_SIDEBAR, width=250)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._build_sidebar_branding(self._sidebar)

        title = tk.Label(
            self._sidebar,
            text="Lina",
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT,
            font=self._title_font,
            anchor="w",
        )
        title.pack(fill=tk.X, padx=18, pady=(20, 4))

        subtitle = tk.Label(
            self._sidebar,
            text="Local AI Assistant",
            bg=COLOR_SIDEBAR,
            fg=COLOR_MUTED,
            font=self._status_font,
            anchor="w",
        )
        subtitle.pack(fill=tk.X, padx=18, pady=(0, 18))

        self._new_chat_button = tk.Button(
            self._sidebar,
            text="Yeni Sohbet",
            command=self._handle_new_chat,
            bg=COLOR_ACCENT,
            fg=COLOR_TEXT,
            activebackground=COLOR_USER_BUBBLE,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
            pady=8,
        )
        self._new_chat_button.pack(fill=tk.X, padx=16, pady=(0, 18))

        section = tk.Label(
            self._sidebar,
            text="Sohbetler",
            bg=COLOR_SIDEBAR,
            fg=COLOR_MUTED,
            font=self._status_font,
            anchor="w",
        )
        section.pack(fill=tk.X, padx=18, pady=(0, 8))

        for item in ("Bugünkü Sohbet", "Proje", "Memory"):
            button = tk.Button(
                self._sidebar,
                text=item,
                command=self._show_history_placeholder,
                bg=COLOR_BUTTON,
                fg=COLOR_TEXT,
                activebackground=COLOR_PANEL,
                activeforeground=COLOR_TEXT,
                relief=tk.FLAT,
                anchor="w",
                padx=12,
                pady=8,
            )
            button.pack(fill=tk.X, padx=16, pady=4)

        footer = tk.Label(
            self._sidebar,
            text=f"{APP_VERSION}\nLocal-first alpha",
            bg=COLOR_SIDEBAR,
            fg=COLOR_MUTED,
            font=self._status_font,
            justify=tk.LEFT,
            anchor="sw",
        )
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=18)

    def _build_sidebar_branding(self, parent: tk.Widget) -> None:
        branding_frame = tk.Frame(parent, bg=COLOR_SIDEBAR)
        branding_frame.pack(fill=tk.X, padx=18, pady=(18, 0))

        if self._logo_image is None:
            return

        logo = tk.Label(
            branding_frame,
            image=self._logo_image,
            bg=COLOR_SIDEBAR,
        )
        logo.pack(anchor="w")

    def _build_main_area(self) -> None:
        self._main_frame = tk.Frame(self._root, bg=COLOR_BG)
        self._main_frame.grid(row=0, column=1, sticky="nsew")

        self._build_header()
        self._build_chat_area()
        self._build_composer()
        self._build_status_bar()

        self._root.columnconfigure(1, weight=1)
        self._root.rowconfigure(0, weight=1)
        self._main_frame.columnconfigure(0, weight=1)
        self._main_frame.rowconfigure(1, weight=1)

    def _build_header(self) -> None:
        self._header_frame = tk.Frame(self._main_frame, bg=COLOR_BG)
        self._header_frame.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 10))

        self._header_label = tk.Label(
            self._header_frame,
            text="Lina",
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=self._header_font,
            anchor="w",
        )
        self._header_label.grid(row=0, column=0, sticky="w")

        self._header_subtitle = tk.Label(
            self._header_frame,
            text="Local AI Desktop Assistant",
            bg=COLOR_BG,
            fg=COLOR_MUTED,
            anchor="w",
        )
        self._header_subtitle.grid(row=1, column=0, sticky="w")

        self._model_badge = tk.Label(
            self._header_frame,
            text="Local mode",
            bg=COLOR_PANEL,
            fg=COLOR_MUTED,
            padx=10,
            pady=5,
        )
        self._model_badge.grid(row=0, column=1, rowspan=2, sticky="e")
        self._header_frame.columnconfigure(0, weight=1)

    def _build_chat_area(self) -> None:
        self._chat_container = tk.Frame(self._main_frame, bg=COLOR_CHAT_BG)
        self._chat_container.grid(row=1, column=0, sticky="nsew", padx=22)

        self._chat_canvas = tk.Canvas(
            self._chat_container,
            bg=COLOR_CHAT_BG,
            highlightthickness=0,
            bd=0,
        )
        self._chat_scrollbar = ttk.Scrollbar(
            self._chat_container,
            orient=tk.VERTICAL,
            command=self._chat_canvas.yview,
        )
        self._messages_frame = tk.Frame(self._chat_canvas, bg=COLOR_CHAT_BG)
        self._messages_window = self._chat_canvas.create_window(
            (0, 0),
            window=self._messages_frame,
            anchor="nw",
        )
        self._chat_canvas.configure(yscrollcommand=self._chat_scrollbar.set)
        self._chat_canvas.grid(row=0, column=0, sticky="nsew")
        self._chat_scrollbar.grid(row=0, column=1, sticky="ns")

        self._messages_frame.bind("<Configure>", self._on_messages_configure)
        self._chat_canvas.bind("<Configure>", self._on_chat_canvas_configure)

        self._chat_container.columnconfigure(0, weight=1)
        self._chat_container.rowconfigure(0, weight=1)

    def _build_composer(self) -> None:
        self._composer_frame = tk.Frame(self._main_frame, bg=COLOR_BG)
        self._composer_frame.grid(row=2, column=0, sticky="ew", padx=22, pady=(12, 8))

        self._attachment_button = tk.Button(
            self._composer_frame,
            text="+",
            command=lambda: self._show_placeholder_feature_message(
                "Dosya yükleme özelliği henüz aktif değil İlhan."
            ),
            width=3,
            bg=COLOR_BUTTON,
            fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
        )
        self._attachment_button.grid(row=0, column=0, sticky="ns", padx=(0, 8))

        self._message_input = tk.Text(
            self._composer_frame,
            height=3,
            width=56,
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            wrap=tk.WORD,
        )
        self._message_input.grid(row=0, column=1, sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)
        self._message_input.bind("<Up>", self._handle_history_previous)
        self._message_input.bind("<Down>", self._handle_history_next)

        self._mic_button = tk.Button(
            self._composer_frame,
            text="Mic",
            command=self._handle_mic,
            bg=COLOR_BUTTON,
            fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
        )
        self._mic_button.grid(row=0, column=2, sticky="ns", padx=(8, 0))

        self._screen_button = tk.Button(
            self._composer_frame,
            text="Screen",
            command=lambda: self._show_placeholder_feature_message(
                "Ekran paylaşımı/görme özelliği henüz aktif değil İlhan."
            ),
            bg=COLOR_BUTTON,
            fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
        )
        self._screen_button.grid(row=0, column=3, sticky="ns", padx=(8, 0))

        self._send_button = tk.Button(
            self._composer_frame,
            text="Gönder",
            command=self.send_message,
            bg=COLOR_ACCENT,
            fg=COLOR_TEXT,
            activebackground=COLOR_USER_BUBBLE,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=14,
        )
        self._send_button.grid(row=0, column=4, sticky="ns", padx=(8, 0))

        self._controls_frame = tk.Frame(self._main_frame, bg=COLOR_BG)
        self._controls_frame.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 8))

        self._clear_button = tk.Button(
            self._controls_frame,
            text="Sohbeti Temizle",
            command=self.clear_chat,
            bg=COLOR_BUTTON,
            fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
            pady=5,
        )
        self._clear_button.pack(side=tk.LEFT)

        self._copy_button = tk.Button(
            self._controls_frame,
            text="Son Cevabı Kopyala",
            command=self.copy_last_response,
            bg=COLOR_BUTTON,
            fg=COLOR_TEXT,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT,
            relief=tk.FLAT,
            padx=10,
            pady=5,
        )
        self._copy_button.pack(side=tk.LEFT, padx=(8, 0))

        self._composer_frame.columnconfigure(1, weight=1)

    def _build_status_bar(self) -> None:
        self._status_frame = tk.Frame(self._main_frame, bg=COLOR_BG)
        self._status_frame.grid(row=4, column=0, sticky="ew", padx=22, pady=(0, 10))

        self._status_text = tk.StringVar(value="Hazır")
        self._status_label = tk.Label(
            self._status_frame,
            textvariable=self._status_text,
            bg=COLOR_BG,
            fg=COLOR_MUTED,
            font=self._status_font,
            anchor="w",
        )
        self._status_label.pack(side=tk.LEFT)

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

    def _handle_history_previous(self, event: tk.Event) -> str:
        self._navigate_input_history(-1)
        return "break"

    def _handle_history_next(self, event: tk.Event) -> str:
        self._navigate_input_history(1)
        return "break"

    def _handle_new_chat(self) -> None:
        self.clear_chat()
        self._update_status_text("Yeni sohbet mevcut oturumu temizledi.")

    def _show_history_placeholder(self) -> None:
        self._show_placeholder_feature_message(
            "Sohbet geçmişi özelliği henüz aktif değil İlhan."
        )

    def _handle_mic(self) -> None:
        if self._is_waiting_for_response:
            return

        if self._speech_service is None:
            self._show_speech_unavailable()
            return

        try:
            is_available = self._speech_service.is_stt_available()
        except Exception:
            _logger.exception("Could not check speech-to-text availability")
            self._show_speech_error()
            return

        if not is_available:
            self._show_speech_unavailable()
            return

        self._set_waiting_state(True)
        self._update_status_text("Konuşma metne çevriliyor...")
        thread = self._thread_factory(
            target=self._transcribe_speech,
            args=(),
            daemon=True,
        )
        thread.start()

    def _transcribe_speech(self) -> None:
        if self._speech_service is None:
            self._root.after(0, self._show_speech_unavailable)
            return

        try:
            result = self._speech_service.transcribe_once()
        except SpeechServiceError:
            _logger.exception("Speech transcription could not be completed")
            self._root.after(0, self._show_speech_error)
            return
        except Exception:
            _logger.exception("Unexpected error while transcribing speech")
            self._root.after(0, self._show_speech_error)
            return

        self._root.after(0, self._show_transcription, result)

    def _show_transcription(self, result: SpeechTranscriptionResult) -> None:
        text = result.text.strip()
        if not text:
            self._show_speech_error()
            return

        self._set_input_text(text)
        message = "Konuşmanı yazıya çevirdim İlhan. Kontrol edip gönderebilirsin."
        self._append_message("Lina", message)
        self._last_response_text = message
        self._set_waiting_state(False)
        self._update_status_text("Hazır")
        self._focus_input()

    def _show_speech_unavailable(self) -> None:
        message = (
            "Mikrofon özelliği henüz hazır değil İlhan. Speech motoru "
            "bağlandığında konuşmanı metne çevirebileceğim."
        )
        self._append_message("Lina", message)
        self._last_response_text = message
        self._set_waiting_state(False)
        self._update_status_text("Speech kullanılamıyor")
        self._focus_input()

    def _show_speech_error(self) -> None:
        message = "Konuşma metne çevrilemedi. Tekrar deneyebilirsin İlhan."
        self._append_message("Lina", message)
        self._last_response_text = message
        self._set_waiting_state(False)
        self._update_status_text("Speech hatası")
        self._focus_input()

    def _show_placeholder_feature_message(self, message: str) -> None:
        self._append_message("Lina", message)
        self._last_response_text = message
        self._update_status_text("Hazır")

    def _get_input_text(self) -> str:
        return self._message_input.get("1.0", tk.END).strip()

    def _clear_input(self) -> None:
        self._message_input.delete("1.0", tk.END)

    def _set_input_text(self, text: str) -> None:
        self._message_input.delete("1.0", tk.END)
        self._message_input.insert("1.0", text)

    def _record_input_history(self, message: str) -> None:
        text = message.strip()
        if not text:
            return
        if not self._input_history or self._input_history[-1] != text:
            self._input_history.append(text)
        self._input_history_index = len(self._input_history)

    def _navigate_input_history(self, direction: int) -> None:
        if self._is_waiting_for_response or not self._input_history:
            return

        if str(self._message_input.cget("state")) == str(tk.DISABLED):
            return

        if direction < 0:
            self._input_history_index = max(0, self._input_history_index - 1)
        elif direction > 0:
            self._input_history_index = min(
                len(self._input_history),
                self._input_history_index + 1,
            )

        if self._input_history_index == len(self._input_history):
            self._set_input_text("")
            return

        self._set_input_text(self._input_history[self._input_history_index])

    def _append_message(self, sender: str, message: str) -> None:
        if hasattr(self, "_messages_frame"):
            self._append_bubble(sender, message)
            return

        self._append_text_message(sender, message)

    def _append_bubble(self, sender: str, message: str) -> None:
        normalized_message = normalize_chat_message(sender, message)
        is_user = sender.casefold() in {"ilhan", "i̇lhan", "sen"}
        row = tk.Frame(self._messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill=tk.X, padx=10, pady=6)

        side = tk.RIGHT if is_user else tk.LEFT
        bubble_color = COLOR_USER_BUBBLE if is_user else COLOR_ASSISTANT_BUBBLE
        bubble = tk.Frame(row, bg=bubble_color, padx=12, pady=9)
        bubble.pack(side=side, anchor="e" if is_user else "w")

        if not is_user:
            sender_label = tk.Label(
                bubble,
                text="Lina",
                bg=bubble_color,
                fg=COLOR_MUTED,
                font=self._status_font,
                anchor="w",
            )
            sender_label.pack(fill=tk.X, anchor="w", pady=(0, 4))

        message_label = tk.Label(
            bubble,
            text=normalized_message,
            bg=bubble_color,
            fg=COLOR_TEXT,
            font=self._chat_font,
            justify=tk.LEFT,
            anchor="w",
            wraplength=560,
        )
        message_label.pack(fill=tk.BOTH, expand=True)

        self._message_widgets.append(row)
        self._root.update_idletasks()
        self._chat_canvas.yview_moveto(1.0)

    def _append_text_message(self, sender: str, message: str) -> None:
        self._chat_log.configure(state=tk.NORMAL)
        start_index = self._chat_log.index("end-1c")
        self._chat_log.insert("end-1c", format_chat_message(sender, message))
        end_index = self._chat_log.index("end-1c")
        self._message_ranges.append((start_index, end_index))
        self._chat_log.configure(state=tk.DISABLED)
        self._chat_log.see(tk.END)

    def _remove_last_message(self) -> None:
        message_widgets = getattr(self, "_message_widgets", [])
        if message_widgets:
            widget = message_widgets.pop()
            widget.destroy()
            self._root.update_idletasks()
            self._chat_canvas.yview_moveto(1.0)
            return

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

    def _on_messages_configure(self, event: tk.Event) -> None:
        self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox("all"))

    def _on_chat_canvas_configure(self, event: tk.Event) -> None:
        self._chat_canvas.itemconfigure(self._messages_window, width=event.width)

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
