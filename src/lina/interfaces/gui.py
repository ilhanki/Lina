"""Tkinter desktop interface for Lina."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
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
from lina.interfaces.gui_theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_APP_BG,
    COLOR_ASSISTANT_BUBBLE,
    COLOR_BORDER,
    COLOR_BUTTON_BG,
    COLOR_BUTTON_HOVER,
    COLOR_CHAT_BG,
    COLOR_DISABLED,
    COLOR_INPUT_BG,
    COLOR_PANEL_BG,
    COLOR_SIDEBAR_BG,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_USER_BUBBLE,
    FONT_HEADER,
    FONT_LABEL,
    FONT_MESSAGE_DEFAULT,
    FONT_MUTED,
    FONT_TITLE,
    clamp_message_font_size,
    configure_tk_scaling,
    configure_windows_dpi_awareness,
    resolve_font_family,
)
from lina.interfaces.gui_components import Tooltip
from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechTranscriptionResult,
)
from lina.speech.service import SpeechService

if TYPE_CHECKING:
    from lina.services.model_diagnostics_service import DiagnosticsResult


_logger = logging.getLogger(__name__)

APP_VERSION = "v0.12.1-alpha"

COLOR_BG = COLOR_APP_BG
COLOR_SIDEBAR = COLOR_SIDEBAR_BG
COLOR_PANEL = COLOR_PANEL_BG
COLOR_TEXT = COLOR_TEXT_PRIMARY
COLOR_MUTED = COLOR_TEXT_MUTED
COLOR_BUTTON = COLOR_BUTTON_BG

SIDEBAR_WIDTH = 264
SIDEBAR_COLLAPSED_WIDTH = 76
INPUT_PLACEHOLDER = "Lina'ya bir mesaj yaz..."

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
        configure_windows_dpi_awareness()
        self._root = root or tk.Tk()
        configure_tk_scaling(self._root)
        self._thread_factory = thread_factory
        self._diagnostics_service = diagnostics_service
        self._speech_service = speech_service
        self._is_waiting_for_response = False
        self._is_closing = False
        self._last_response_text: str = ""
        self._input_history: list[str] = []
        self._input_history_index = 0
        self._sidebar_expanded = True
        self._input_has_placeholder = False
        self._message_labels: list[tk.Label] = []
        self._session_title_text = "Yeni Sohbet"
        self._tooltips: list[Tooltip] = []
        self._root.title("Lina")
        self._root.geometry("1200x760")
        self._root.minsize(1000, 650)
        self._message_ranges: list[tuple[str, str]] = []
        self._message_widgets: list[tk.Widget] = []
        self._font_family = resolve_font_family(font.families(self._root))
        self._message_font_size = FONT_MESSAGE_DEFAULT
        self._chat_font = font.Font(
            root=self._root,
            family=self._font_family,
            size=self._message_font_size,
        )
        self._header_font = font.Font(
            root=self._root,
            family=self._font_family,
            size=FONT_HEADER,
            weight="bold",
        )
        self._title_font = font.Font(
            root=self._root,
            family=self._font_family,
            size=FONT_TITLE,
            weight="bold",
        )
        self._status_font = font.Font(
            root=self._root,
            family=self._font_family,
            size=FONT_MUTED,
        )
        self._label_font = font.Font(
            root=self._root,
            family=self._font_family,
            size=FONT_LABEL,
            weight="bold",
        )
        self._logo_image: tk.PhotoImage | None = None
        self._icon_image: tk.PhotoImage | None = None

        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._root.bind("<Control-l>", self._handle_focus_shortcut)
        self._root.bind("<Control-n>", self._handle_new_chat_shortcut)
        self._root.bind("<Control-k>", self._handle_new_chat_shortcut)
        self._root.bind("<Escape>", self._handle_escape)
        self._load_branding_assets()
        self._configure_theme()
        self._build_sidebar()
        self._build_main_area()

        self._append_message("Lina", format_welcome_message())
        self._show_input_placeholder()
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
        self._update_session_title(message)
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
        getattr(self, "_message_labels", []).clear()
        self._last_response_text = ""
        self._set_session_title("Yeni Sohbet")
        self._append_message("Lina", format_welcome_message())

    def copy_last_response(self) -> None:
        """Copy last Lina response to clipboard."""
        if not self._last_response_text:
            return
        self._root.clipboard_clear()
        self._root.clipboard_append(self._last_response_text)
        self._update_status_text("Mesaj kopyalandı")

    def _copy_message(self, message: str) -> None:
        self._root.clipboard_clear()
        self._root.clipboard_append(message)
        self._update_status_text("Mesaj kopyalandı")

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
        self._sidebar = tk.Frame(
            self._root,
            bg=COLOR_SIDEBAR,
            width=SIDEBAR_WIDTH,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._build_sidebar_branding(self._sidebar)

        self._sidebar_toggle_button = self._build_button(
            self._sidebar,
            text="‹",
            command=self._toggle_sidebar,
            width=3,
        )
        self._sidebar_toggle_button.pack(anchor="e", padx=14, pady=(2, 12))
        self._tooltips.append(
            Tooltip(self._sidebar_toggle_button, "Sidebar'ı daralt veya genişlet")
        )

        self._new_chat_button = self._build_button(
            self._sidebar,
            text="Yeni Sohbet",
            command=self._handle_new_chat,
            accent=True,
        )
        self._new_chat_button.pack(fill=tk.X, padx=16, pady=(0, 16))

        self._sidebar_details = tk.Frame(self._sidebar, bg=COLOR_SIDEBAR)
        self._sidebar_details.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            self._sidebar_details,
            text="Lina",
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT,
            font=self._title_font,
            anchor="w",
        )
        title.pack(fill=tk.X, padx=18, pady=(4, 2))

        subtitle = tk.Label(
            self._sidebar_details,
            text="Local AI Desktop Assistant",
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT_SECONDARY,
            font=self._status_font,
            anchor="w",
        )
        subtitle.pack(fill=tk.X, padx=18, pady=(0, 22))

        section = tk.Label(
            self._sidebar_details,
            text="BU OTURUM",
            bg=COLOR_SIDEBAR,
            fg=COLOR_MUTED,
            font=self._status_font,
            anchor="w",
        )
        section.pack(fill=tk.X, padx=18, pady=(0, 8))

        self._sidebar_session_title = tk.StringVar(value=self._session_title_text)
        session_label = tk.Label(
            self._sidebar_details,
            textvariable=self._sidebar_session_title,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_PRIMARY,
            font=self._status_font,
            anchor="w",
            padx=12,
            pady=10,
        )
        session_label.pack(fill=tk.X, padx=16)

        history_note = tk.Label(
            self._sidebar_details,
            text="Kalıcı sohbet geçmişi henüz aktif değil.",
            bg=COLOR_SIDEBAR,
            fg=COLOR_MUTED,
            font=self._status_font,
            wraplength=220,
            justify=tk.LEFT,
            anchor="w",
        )
        history_note.pack(fill=tk.X, padx=18, pady=(10, 0))

        self._sidebar_footer = tk.Frame(self._sidebar, bg=COLOR_SIDEBAR)
        self._sidebar_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
        model_name = "Model yapılandırılmadı"
        if self._diagnostics_service is not None:
            model_name = self._diagnostics_service.configured_model
        footer_text = tk.Label(
            self._sidebar_footer,
            text=f"Local mode\n{model_name}\n{APP_VERSION}\nSes verisi yerelde işlenir",
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT_MUTED,
            font=self._status_font,
            justify=tk.LEFT,
            anchor="w",
        )
        footer_text.pack(fill=tk.X, pady=(0, 10))

        font_controls = tk.Frame(self._sidebar_footer, bg=COLOR_SIDEBAR)
        font_controls.pack(fill=tk.X)
        decrease = self._build_button(
            font_controls,
            text="A−",
            command=lambda: self._adjust_font_size(-1),
            width=4,
        )
        decrease.pack(side=tk.LEFT)
        increase = self._build_button(
            font_controls,
            text="A+",
            command=lambda: self._adjust_font_size(1),
            width=4,
        )
        increase.pack(side=tk.LEFT, padx=(8, 0))
        self._tooltips.extend(
            [
                Tooltip(decrease, "Yazı boyutunu küçült"),
                Tooltip(increase, "Yazı boyutunu büyüt"),
            ]
        )

    def _build_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        width: int | None = None,
        accent: bool = False,
    ) -> tk.Button:
        background = COLOR_ACCENT if accent else COLOR_BUTTON
        hover = COLOR_ACCENT_HOVER if accent else COLOR_BUTTON_HOVER
        options = {}
        if width is not None:
            options["width"] = width
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=hover,
            activeforeground=COLOR_TEXT_PRIMARY,
            disabledforeground=COLOR_DISABLED,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            padx=11,
            pady=8,
            cursor="hand2",
            **options,
        )
        button.bind(
            "<Enter>",
            lambda event: button.configure(bg=hover)
            if str(button.cget("state")) != str(tk.DISABLED)
            else None,
            add="+",
        )
        button.bind(
            "<Leave>",
            lambda event: button.configure(bg=background),
            add="+",
        )
        return button

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
            textvariable=self._create_header_title_variable(),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY,
            font=self._status_font,
            anchor="w",
        )
        self._header_subtitle.grid(row=1, column=0, sticky="w")

        self._model_badge = tk.Label(
            self._header_frame,
            text="Local Mode",
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            font=self._status_font,
            padx=10,
            pady=5,
        )
        self._model_badge.grid(row=0, column=1, rowspan=2, sticky="e", padx=(8, 0))
        self._speech_badge_text = tk.StringVar(value="Mic Hazır")
        self._speech_badge = tk.Label(
            self._header_frame,
            textvariable=self._speech_badge_text,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            font=self._status_font,
            padx=10,
            pady=5,
        )
        self._speech_badge.grid(row=0, column=2, rowspan=2, sticky="e", padx=(8, 0))
        self._header_frame.columnconfigure(0, weight=1)

    def _create_header_title_variable(self) -> tk.StringVar:
        self._header_session_title = tk.StringVar(value=self._session_title_text)
        return self._header_session_title

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
        self._chat_canvas.bind("<MouseWheel>", self._handle_mouse_wheel)

        self._chat_container.columnconfigure(0, weight=1)
        self._chat_container.rowconfigure(0, weight=1)

    def _build_composer(self) -> None:
        self._composer_frame = tk.Frame(
            self._main_frame,
            bg=COLOR_PANEL,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            padx=10,
            pady=10,
        )
        self._composer_frame.grid(row=2, column=0, sticky="ew", padx=22, pady=(12, 8))

        self._attachment_button = self._build_button(
            self._composer_frame,
            text="+",
            command=lambda: self._show_placeholder_feature_message(
                "Dosya yükleme özelliği henüz aktif değil İlhan."
            ),
            width=3,
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
            font=self._chat_font,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_ACCENT,
        )
        self._message_input.grid(row=0, column=1, sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)
        self._message_input.bind("<Up>", self._handle_history_previous)
        self._message_input.bind("<Down>", self._handle_history_next)
        self._message_input.bind("<FocusIn>", self._handle_input_focus_in)
        self._message_input.bind("<FocusOut>", self._handle_input_focus_out)
        self._message_input.bind("<KeyRelease>", self._handle_input_key_release)

        self._mic_button = self._build_button(
            self._composer_frame,
            text="Mic",
            command=self._handle_mic,
        )
        self._mic_button.grid(row=0, column=2, sticky="ns", padx=(8, 0))

        self._screen_button = self._build_button(
            self._composer_frame,
            text="Screen",
            command=lambda: self._show_placeholder_feature_message(
                "Ekran paylaşımı/görme özelliği henüz aktif değil İlhan."
            ),
        )
        self._screen_button.grid(row=0, column=3, sticky="ns", padx=(8, 0))

        self._send_button = self._build_button(
            self._composer_frame,
            text="Gönder",
            command=self.send_message,
            accent=True,
        )
        self._send_button.grid(row=0, column=4, sticky="ns", padx=(8, 0))

        self._controls_frame = tk.Frame(self._main_frame, bg=COLOR_BG)
        self._controls_frame.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 8))

        self._clear_button = self._build_button(
            self._controls_frame,
            text="Sohbeti Temizle",
            command=self.clear_chat,
        )
        self._clear_button.pack(side=tk.LEFT)

        self._copy_button = self._build_button(
            self._controls_frame,
            text="Son Cevabı Kopyala",
            command=self.copy_last_response,
        )
        self._copy_button.pack(side=tk.LEFT, padx=(8, 0))

        self._composer_frame.columnconfigure(1, weight=1)
        self._tooltips.extend(
            [
                Tooltip(self._attachment_button, "Dosya ekle - henüz aktif değil"),
                Tooltip(self._mic_button, "Konuşmayı metne çevir"),
                Tooltip(self._screen_button, "Ekran bağlamı - henüz aktif değil"),
                Tooltip(self._send_button, "Mesajı gönder"),
            ]
        )

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

    def _handle_enter(self, event: tk.Event) -> str | None:
        if event.state & 0x0001:
            return None
        self.send_message()
        return "break"

    def _handle_focus_shortcut(self, event: tk.Event | None = None) -> str:
        self._hide_input_placeholder()
        self._focus_input()
        return "break"

    def _handle_new_chat_shortcut(self, event: tk.Event | None = None) -> str:
        self._handle_new_chat()
        return "break"

    def _handle_escape(self, event: tk.Event | None = None) -> str:
        self._focus_input()
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

    def _toggle_sidebar(self) -> None:
        self._sidebar_expanded = not self._sidebar_expanded
        if self._sidebar_expanded:
            self._sidebar.configure(width=SIDEBAR_WIDTH)
            self._sidebar_details.pack(fill=tk.BOTH, expand=True)
            self._sidebar_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
            self._new_chat_button.configure(text="Yeni Sohbet", width=0)
            self._sidebar_toggle_button.configure(text="‹")
            return

        self._sidebar.configure(width=SIDEBAR_COLLAPSED_WIDTH)
        self._sidebar_details.pack_forget()
        self._sidebar_footer.pack_forget()
        self._new_chat_button.configure(text="+", width=3)
        self._sidebar_toggle_button.configure(text="›")

    def _adjust_font_size(self, delta: int) -> None:
        self._message_font_size = clamp_message_font_size(
            self._message_font_size + delta
        )
        self._chat_font.configure(size=self._message_font_size)
        self._update_status_text(f"Yazı boyutu: {self._message_font_size}")

    def _update_session_title(self, message: str) -> None:
        if getattr(self, "_session_title_text", "Yeni Sohbet") != "Yeni Sohbet":
            return
        title = derive_session_title(message)
        if title == "Yeni Sohbet":
            return
        self._set_session_title(title)

    def _set_session_title(self, title: str) -> None:
        self._session_title_text = title
        for variable_name in ("_header_session_title", "_sidebar_session_title"):
            variable = getattr(self, variable_name, None)
            if variable is not None:
                variable.set(title)

    def _show_history_placeholder(self) -> None:
        self._show_placeholder_feature_message(
            "Sohbet geçmişi özelliği henüz aktif değil İlhan."
        )

    def _handle_mic(self) -> None:
        if self._is_waiting_for_response:
            if (
                self._speech_service is not None
                and self._speech_service.get_state() is SpeechState.LISTENING
            ):
                self._speech_service.stop_listening()
                self._set_mic_button(text="Mic", enabled=False)
                self._update_status_text("Konuşma metne çevriliyor...")
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
        self._set_mic_button(text="Durdur", enabled=True)
        self._update_status_text("Dinliyorum...")
        thread = self._thread_factory(
            target=self._transcribe_speech,
            args=(),
            daemon=True,
        )
        thread.start()
        self._root.after(100, self._refresh_speech_status)

    def _refresh_speech_status(self) -> None:
        if not self._is_waiting_for_response or self._speech_service is None:
            return

        state = self._speech_service.get_state()
        if state is SpeechState.LISTENING:
            self._set_mic_button(text="Durdur", enabled=True)
            self._update_status_text("Dinliyorum...")
        elif state is SpeechState.TRANSCRIBING:
            self._set_mic_button(text="Mic", enabled=False)
            self._update_status_text(
                "Konuşma metne çevriliyor; ilk kullanımda model hazırlanabilir..."
            )
        else:
            return

        self._root.after(100, self._refresh_speech_status)

    def _transcribe_speech(self) -> None:
        if self._speech_service is None:
            self._schedule_speech_callback(self._show_speech_unavailable)
            return

        try:
            result = self._speech_service.transcribe_once()
        except SpeechServiceError:
            _logger.exception("Speech transcription could not be completed")
            self._schedule_speech_callback(self._show_speech_error)
            return
        except Exception:
            _logger.exception("Unexpected error while transcribing speech")
            self._schedule_speech_callback(self._show_speech_error)
            return

        self._schedule_speech_callback(self._show_transcription, result)

    def _schedule_speech_callback(self, callback, *args) -> None:
        if self._is_closing:
            return
        try:
            self._root.after(0, callback, *args)
        except (RuntimeError, tk.TclError):
            _logger.debug("Speech callback skipped because the GUI is closing")

    def _show_transcription(self, result: SpeechTranscriptionResult) -> None:
        text = result.text.strip()
        if not text:
            self._show_empty_transcription()
            return

        if not self._append_transcription_to_input(text):
            self._show_speech_input_error()
            return

        message = "Konuşmanı yazıya çevirdim İlhan. Kontrol edip gönderebilirsin."
        self._append_message("Lina", message)
        self._last_response_text = message
        self._reset_speech_ui("Metin hazır")

    def _append_transcription_to_input(self, text: str) -> bool:
        transcription = text.strip()
        if not transcription:
            return False

        original_state = str(self._message_input.cget("state"))
        try:
            if original_state == str(tk.DISABLED):
                self._message_input.configure(state=tk.NORMAL)

            current_text = self._get_input_text()
            combined_text = (
                f"{current_text.rstrip()} {transcription}"
                if current_text
                else transcription
            )
            self._set_input_text(combined_text)
            self._message_input.mark_set(tk.INSERT, tk.END)
            self._message_input.see(tk.END)
            return self._get_input_text() == combined_text
        except (RuntimeError, tk.TclError):
            _logger.exception("Could not write speech transcription into GUI input")
            return False
        finally:
            if original_state == str(tk.DISABLED):
                try:
                    self._message_input.configure(state=tk.DISABLED)
                except tk.TclError:
                    _logger.debug("GUI input state could not be restored")

    def _show_empty_transcription(self) -> None:
        message = "Net bir konuşma algılayamadım İlhan. Tekrar deneyebilirsin."
        self._append_message("Lina", message)
        self._last_response_text = message
        self._reset_speech_ui("Konuşma algılanamadı")

    def _show_speech_input_error(self) -> None:
        message = (
            "Konuşmanı metne çevirdim ancak giriş alanına yazamadım İlhan. "
            "Tekrar deneyebilirsin."
        )
        self._append_message("Lina", message)
        self._last_response_text = message
        self._reset_speech_ui("Metin girişine yazılamadı")

    def _show_speech_unavailable(self) -> None:
        message = (
            "Mikrofon özelliği henüz hazır değil İlhan. Speech motoru "
            "bağlandığında konuşmanı metne çevirebileceğim."
        )
        self._append_message("Lina", message)
        self._last_response_text = message
        self._reset_speech_ui("Speech kullanılamıyor")

    def _show_speech_error(self) -> None:
        message = "Konuşma metne çevrilemedi. Tekrar deneyebilirsin İlhan."
        self._append_message("Lina", message)
        self._last_response_text = message
        self._reset_speech_ui("Speech hatası")

    def _reset_speech_ui(self, status: str) -> None:
        self._set_waiting_state(False)
        self._set_mic_button(text="Mic", enabled=True)
        self._update_status_text(status)
        self._focus_input()

    def _set_mic_button(self, text: str, enabled: bool) -> None:
        if not hasattr(self, "_mic_button"):
            return
        state = tk.NORMAL if enabled else tk.DISABLED
        self._mic_button.configure(text=text, state=state)
        badge = getattr(self, "_speech_badge_text", None)
        if badge is not None:
            badge.set("Dinliyor" if text == "Durdur" else "Mic Hazır")

    def _show_placeholder_feature_message(self, message: str) -> None:
        self._append_message("Lina", message)
        self._last_response_text = message
        self._update_status_text("Hazır")

    def _get_input_text(self) -> str:
        if getattr(self, "_input_has_placeholder", False):
            return ""
        return self._message_input.get("1.0", tk.END).strip()

    def _clear_input(self) -> None:
        self._input_has_placeholder = False
        self._message_input.delete("1.0", tk.END)
        self._update_send_button_state()

    def _set_input_text(self, text: str) -> None:
        self._input_has_placeholder = False
        self._message_input.delete("1.0", tk.END)
        self._message_input.insert("1.0", text)
        self._message_input.configure(fg=COLOR_TEXT_PRIMARY)
        self._update_send_button_state()

    def _show_input_placeholder(self) -> None:
        if self._get_input_text():
            return
        self._message_input.delete("1.0", tk.END)
        self._message_input.insert("1.0", INPUT_PLACEHOLDER)
        self._message_input.configure(fg=COLOR_TEXT_MUTED)
        self._input_has_placeholder = True
        self._update_send_button_state()

    def _hide_input_placeholder(self) -> None:
        if not getattr(self, "_input_has_placeholder", False):
            return
        self._message_input.delete("1.0", tk.END)
        self._message_input.configure(fg=COLOR_TEXT_PRIMARY)
        self._input_has_placeholder = False
        self._update_send_button_state()

    def _handle_input_focus_in(self, event: tk.Event | None = None) -> None:
        self._hide_input_placeholder()

    def _handle_input_focus_out(self, event: tk.Event | None = None) -> None:
        self._show_input_placeholder()

    def _handle_input_key_release(self, event: tk.Event | None = None) -> None:
        self._update_send_button_state()

    def _update_send_button_state(self) -> None:
        button = getattr(self, "_send_button", None)
        if button is None:
            return
        enabled = bool(self._get_input_text()) and not self._is_waiting_for_response
        button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

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
        should_scroll = self._is_chat_near_bottom()
        row = tk.Frame(self._messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill=tk.X, padx=12, pady=8)

        side = tk.RIGHT if is_user else tk.LEFT
        bubble_color = COLOR_USER_BUBBLE if is_user else COLOR_ASSISTANT_BUBBLE
        bubble = tk.Frame(row, bg=bubble_color, padx=14, pady=11)
        bubble.pack(side=side, anchor="e" if is_user else "w")

        if not is_user:
            sender_label = tk.Label(
                bubble,
                text="Lina",
                bg=bubble_color,
                fg=COLOR_MUTED,
                font=self._label_font,
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

        metadata = tk.Frame(bubble, bg=bubble_color)
        metadata.pack(fill=tk.X, pady=(7, 0))
        timestamp = tk.Label(
            metadata,
            text=datetime.now().strftime("%H:%M"),
            bg=bubble_color,
            fg=COLOR_TEXT_MUTED,
            font=self._status_font,
        )
        timestamp.pack(side=tk.LEFT)
        copy_button = tk.Button(
            metadata,
            text="Kopyala",
            command=lambda text=normalized_message: self._copy_message(text),
            bg=bubble_color,
            fg=COLOR_TEXT_SECONDARY,
            activebackground=bubble_color,
            activeforeground=COLOR_TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            font=self._status_font,
            cursor="hand2",
        )
        copy_button.pack(side=tk.RIGHT)

        self._message_widgets.append(row)
        self._message_labels.append(message_label)
        self._root.update_idletasks()
        if should_scroll:
            self._chat_canvas.yview_moveto(1.0)

    def _is_chat_near_bottom(self) -> bool:
        try:
            _, bottom = self._chat_canvas.yview()
            return bottom >= 0.95
        except (AttributeError, tk.TclError):
            return True

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
            labels = getattr(self, "_message_labels", [])
            if labels:
                labels.pop()
            self._root.update_idletasks()
            if self._is_chat_near_bottom():
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
        self._update_send_button_state()

    def _focus_input(self) -> None:
        self._message_input.focus_set()

    def _on_messages_configure(self, event: tk.Event) -> None:
        self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox("all"))

    def _on_chat_canvas_configure(self, event: tk.Event) -> None:
        self._chat_canvas.itemconfigure(self._messages_window, width=event.width)
        wraplength = calculate_message_wraplength(event.width)
        for label in getattr(self, "_message_labels", []):
            label.configure(wraplength=wraplength)

    def _handle_mouse_wheel(self, event: tk.Event) -> str:
        self._chat_canvas.yview_scroll(int(-event.delta / 120), "units")
        return "break"

    def _on_close(self) -> None:
        """Handle window close gracefully."""
        self._is_closing = True
        if (
            self._speech_service is not None
            and self._speech_service.get_state() is SpeechState.LISTENING
        ):
            self._speech_service.stop_listening()
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


def derive_session_title(message: str, max_length: int = 40) -> str:
    """Create a deterministic session title from the first meaningful message."""
    normalized = " ".join(message.split())
    greeting = normalized.casefold().strip("!.,? ")
    if greeting in {"selam", "merhaba", "selam naber", "naber", "nasılsın"}:
        return "Yeni Sohbet"
    if not normalized:
        return "Yeni Sohbet"
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."


def calculate_message_wraplength(canvas_width: int) -> int:
    """Return a bounded bubble text width for the current chat canvas."""
    return max(280, min(int(canvas_width * 0.7), 760))


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
