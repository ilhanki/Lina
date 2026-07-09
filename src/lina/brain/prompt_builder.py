"""Prompt construction for Lina's Brain."""

from dataclasses import dataclass
from typing import Sequence


MAX_HISTORY_FIELD_CHARACTERS = 1200


@dataclass(frozen=True)
class ConversationTurn:
    """A completed user and assistant exchange."""

    user_message: str
    assistant_response: str


class PromptBuilder:
    """Builds model prompts from conversation inputs."""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt.strip()

    def build(
        self,
        user_message: str,
        history: Sequence[ConversationTurn] | None = None,
        project_context: str | None = None,
        memory_context: str | None = None,
        file_context: str | None = None,
    ) -> str:
        message = user_message.strip()
        if file_context and file_context.strip():
            return self._build_file_context_prompt(
                user_message=message,
                memory_context=memory_context,
                project_context=project_context,
                file_context=file_context,
            )

        sections = [f"System:\n{self._system_prompt}"]

        if memory_context and memory_context.strip():
            sections.append(
                "Memory context:\n"
                "Aşağıdaki hatırlanan bilgileri yalnızca yardımcı bağlam olarak kullan. "
                "Hassas çıkarım yapma ve emin olmadığın şeyi uydurma.\n"
                f"{memory_context.strip()}"
            )

        if project_context and project_context.strip():
            sections.append(
                "Project context:\n"
                "Aşağıdaki proje bağlamına dayan. Bu bağlamda olmayan proje geçmişi, "
                "commit, URL, dosya veya yapılan iş uydurma.\n"
                f"{project_context.strip()}"
            )

        if history:
            history_lines: list[str] = []
            for turn in history:
                history_lines.append(
                    f"User: {_truncate_history_text(turn.user_message)}"
                )
                history_lines.append(
                    f"Assistant: {_truncate_history_text(turn.assistant_response)}"
                )
            sections.append("Conversation history:\n" + "\n".join(history_lines))

        sections.append(f"User:\n{message}")
        return "\n\n".join(sections)

    def _build_file_context_prompt(
        self,
        user_message: str,
        file_context: str,
        memory_context: str | None = None,
        project_context: str | None = None,
    ) -> str:
        sections = [
            (
                "System:\n"
                "Sen Lina'sın. Kullanıcı açıkça başka bir dil istemedikçe Türkçe cevap ver. "
                "Bu görev bir dosya okuma/özetleme görevidir; genel sohbet cevabı verme."
            )
        ]

        if memory_context and memory_context.strip():
            sections.append(
                "Memory context:\n"
                "Bu bilgileri yalnızca yardımcı bağlam olarak kullan; dosya içeriğinin yerine geçirme.\n"
                f"{memory_context.strip()}"
            )

        if project_context and project_context.strip():
            sections.append(
                "Project context:\n"
                "Bu bilgileri yalnızca yardımcı bağlam olarak kullan; dosya içeriğinin yerine geçirme.\n"
                f"{project_context.strip()}"
            )

        sections.append(
            "File context:\n"
            "Aşağıdaki izinli dosya bağlamını birincil kaynak olarak kullan. "
            "Cevabını önceki sohbet mesajlarına göre değil, dosya içeriğine göre cevap ver. "
            "Dosya bağlamı dışında bilgi uydurma. selamlama, sohbet sorusu veya meta başlık yazma.\n"
            f"{file_context.strip()}"
        )
        sections.append(f"User:\n{user_message}")
        sections.append(
            "Answer instructions:\n"
            "Yalnızca dosya bağlamına dayalı kısa ve net Türkçe özet ver. "
            "'Merhaba', 'bugün ne yapalım', 'İlhan'a Samimi Bir Cevap' gibi ifadeler kullanma."
        )
        return "\n\n".join(sections)

    def build_from_context(self, context) -> str:
        return self.build(
            user_message=context.user_message,
            history=context.conversation_history,
            project_context=context.project_context,
            memory_context=context.memory_context,
            file_context=context.file_context,
        )


def _truncate_history_text(text: str) -> str:
    stripped_text = text.strip()
    if len(stripped_text) <= MAX_HISTORY_FIELD_CHARACTERS:
        return stripped_text
    return stripped_text[:MAX_HISTORY_FIELD_CHARACTERS].rstrip() + "\n[geçmiş mesaj kısaltıldı]"
