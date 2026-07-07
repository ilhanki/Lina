"""Command-line interface for Lina."""

import sys
from typing import TextIO

from lina.brain.model_provider import ModelProviderError
from lina.services.conversation_service import ConversationService


class LinaCli:
    """Simple terminal chat interface."""

    def __init__(
        self,
        conversation_service: ConversationService,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ) -> None:
        self._conversation_service = conversation_service
        self._input_stream = input_stream
        self._output_stream = output_stream

    def run(self) -> None:
        self._write_banner()

        while True:
            self._output_stream.write("> ")
            self._output_stream.flush()

            user_input = self._input_stream.readline()
            if user_input == "":
                break

            message = user_input.strip()
            if message.lower() in {"exit", "quit"}:
                break
            if message.lower() in {"help", "?"}:
                self._write_help()
                continue
            if not message:
                continue

            try:
                response = self._conversation_service.handle_message(message)
            except ModelProviderError as error:
                self._output_stream.write(f"Lina şu anda cevap üretemedi: {error}\n")
                self._output_stream.flush()
                continue

            self._output_stream.write(f"{response.text}\n")
            self._output_stream.flush()

    def _write_banner(self) -> None:
        self._output_stream.write("----------------------------------------\n\n")
        self._output_stream.write("Lina v0.3.0-alpha\n\n")
        self._output_stream.write("Merhaba İlhan.\n\n")
        self._output_stream.write("Hazırım.\n\n")
        self._output_stream.write("----------------------------------------\n\n")
        self._output_stream.flush()

    def _write_help(self) -> None:
        self._output_stream.write("Komutlar: help, ?, exit, quit\n")
        self._output_stream.flush()
