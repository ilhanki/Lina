"""Tkinter desktop interface for Lina."""

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from lina.brain.model_provider import ModelResponse
from lina.services.conversation_service import ConversationService


class LinaGui:
    """Simple Tkinter chat window for Lina."""

    def __init__(
        self,
        conversation_service: ConversationService,
        root: tk.Tk | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._root = root or tk.Tk()
        self._root.title("Lina")

        self._chat_log = ScrolledText(
            self._root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=72,
            height=24,
        )
        self._chat_log.grid(row=0, column=0, columnspan=2, padx=12, pady=12, sticky="nsew")

        self._message_input = tk.Text(self._root, height=3, width=56)
        self._message_input.grid(row=1, column=0, padx=(12, 8), pady=(0, 12), sticky="ew")
        self._message_input.bind("<Return>", self._handle_enter)

        self._send_button = tk.Button(
            self._root,
            text="Gönder",
            command=self.send_message,
        )
        self._send_button.grid(row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="ew")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        self._append_message("Lina", "Merhaba İlhan. Hazırım.")

    def run(self) -> None:
        self._root.mainloop()

    def send_message(self) -> None:
        message = self._get_input_text()
        if not message:
            return

        self._clear_input()
        self._append_message("İlhan", message)
        response = self._conversation_service.handle_message(message)
        self._append_message("Lina", response.text)

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


def format_chat_message(sender: str, message: str) -> str:
    return f"{sender}: {message.strip()}\n\n"
