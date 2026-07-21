"""Responsive, non-destructive Codex diff review dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSplitter,
    QVBoxLayout, QWidget,
)

from lina.codex.changes import CodexChangeSet, CodexFileChange, CodexReviewDecision


class CodexDiffReviewDialog(QDialog):
    decision_requested = Signal(object)
    review_completed = Signal()

    def __init__(self, change_set: CodexChangeSet, *, task_title: str = "Codex görevi",
                 workspace_name: str = "Çalışma alanı", parent=None) -> None:
        super().__init__(parent)
        self.change_set = change_set
        self._current: CodexFileChange | None = None
        self.setWindowTitle("Codex Değişiklik İncelemesi")
        self.setObjectName("codexDiffReviewDialog")
        self.resize(1100, 720)
        self.setMinimumSize(640, 480)
        root = QVBoxLayout(self)
        self.summary_label = QLabel(
            f"{task_title} · {workspace_name}\n"
            f"{change_set.changed_file_count} dosya · +{change_set.additions} / -{change_set.deletions}",
            self,
        )
        self.summary_label.setObjectName("codexDiffSummary")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        toolbar = QHBoxLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Değişikliklerde ara")
        self.previous_button = QPushButton("Önceki", self)
        self.next_button = QPushButton("Sonraki", self)
        self.wrap_toggle = QCheckBox("Satırları kaydır", self)
        self.copy_hunk_button = QPushButton("Seçili bölümü kopyala", self)
        for widget in (self.search, self.previous_button, self.next_button,
                       self.wrap_toggle, self.copy_hunk_button):
            toolbar.addWidget(widget)
        root.addLayout(toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setObjectName("codexDiffSplitter")
        self.file_list = QListWidget(self.splitter)
        self.file_list.setAccessibleName("Değişen Codex dosyaları")
        self.diff_view = QPlainTextEdit(self.splitter)
        self.diff_view.setReadOnly(True)
        self.diff_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.diff_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.diff_view.setAccessibleName("Birleştirilmiş Codex değişiklikleri")
        self.review_panel = QWidget(self.splitter)
        actions = QVBoxLayout(self.review_panel)
        self.file_status = QLabel("Bir dosya seç.", self.review_panel)
        self.file_status.setWordWrap(True)
        self.accept_file_button = QPushButton("Dosyayı kabul et", self.review_panel)
        self.reject_file_button = QPushButton("Dosyayı reddet", self.review_panel)
        self.accept_all_button = QPushButton("Tümünü kabul et", self.review_panel)
        self.inspect_only_button = QPushButton("Yalnız inceledim", self.review_panel)
        self.explain_button = QPushButton("Açıklama iste", self.review_panel)
        self.send_back_button = QPushButton("Codex'e düzeltme gönder", self.review_panel)
        for widget in (self.file_status, self.accept_file_button, self.reject_file_button,
                       self.accept_all_button, self.inspect_only_button,
                       self.explain_button, self.send_back_button):
            actions.addWidget(widget)
        actions.addStretch(1)
        self.splitter.addWidget(self.file_list)
        self.splitter.addWidget(self.diff_view)
        self.splitter.addWidget(self.review_panel)
        self.splitter.setSizes([240, 620, 240])
        self.splitter.setChildrenCollapsible(False)
        root.addWidget(self.splitter, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.close_button = QPushButton("Kapat", self)
        footer.addWidget(self.close_button)
        root.addLayout(footer)

        self.file_list.currentRowChanged.connect(self._select_file)
        self.search.returnPressed.connect(self._find_next)
        self.next_button.clicked.connect(self._find_next)
        self.previous_button.clicked.connect(self._find_previous)
        self.wrap_toggle.toggled.connect(self._set_wrap)
        self.copy_hunk_button.clicked.connect(self._copy_selection)
        self.accept_file_button.clicked.connect(lambda: self._emit("accept"))
        self.reject_file_button.clicked.connect(lambda: self._emit("reject"))
        self.accept_all_button.clicked.connect(self._accept_all)
        self.inspect_only_button.clicked.connect(lambda: self._emit("inspect"))
        self.explain_button.clicked.connect(lambda: self._emit("request_explanation"))
        self.send_back_button.clicked.connect(lambda: self._emit("send_back"))
        self.close_button.clicked.connect(self.accept)
        self.render(change_set)

    def render(self, change_set: CodexChangeSet) -> None:
        self.change_set = change_set
        self.file_list.clear()
        for change in change_set.files:
            marker = {
                "added": "A", "modified": "M", "deleted": "D",
                "renamed": "R", "mode_changed": "T",
            }.get(change.change_type, "?")
            warning = " ⚠" if change.forbidden or change.truncated else ""
            item = QListWidgetItem(
                f"{marker}  {change.relative_path}  +{change.additions}/-{change.deletions}{warning}"
            )
            item.setData(Qt.ItemDataRole.UserRole, change.relative_path)
            self.file_list.addItem(item)
        if self.file_list.count():
            self.file_list.setCurrentRow(0)
        else:
            self.diff_view.setPlainText("Herhangi bir dosya değiştirilmedi.")

    def resizeEvent(self, event) -> None:
        self.splitter.setOrientation(
            Qt.Orientation.Vertical if self.width() < 820 else Qt.Orientation.Horizontal
        )
        super().resizeEvent(event)

    def _select_file(self, row: int) -> None:
        if not 0 <= row < len(self.change_set.files):
            self._current = None
            return
        self._current = self.change_set.files[row]
        change = self._current
        self.file_status.setText(
            f"{change.relative_path}\n{change.change_type} · {change.review_status.value}\n"
            f"+{change.additions} / -{change.deletions}"
        )
        blocked = change.forbidden
        self.accept_file_button.setEnabled(not blocked)
        self.reject_file_button.setEnabled(not blocked)
        if change.forbidden:
            text = "Hassas dosya değişikliği engellendi. Değişiklik içeriği gösterilmiyor."
        elif change.binary:
            text = (f"Binary dosya · önce {change.size_before} bayt · "
                    f"sonra {change.size_after} bayt. İçerik gösterilmiyor.")
        elif change.diff_available:
            text = change.unified_diff
            if change.truncated:
                text += "\n\n[Değişiklik içeriği güvenli boyut sınırında kısaltıldı.]"
        else:
            text = "Bu dosya için güvenli metin diff'i kullanılamıyor."
        self.diff_view.setPlainText(text)
        self.diff_view.moveCursor(QTextCursor.MoveOperation.Start)

    def _emit(self, action: str) -> None:
        if self._current is None:
            return
        self.decision_requested.emit(CodexReviewDecision(action, self._current.relative_path))

    def _accept_all(self) -> None:
        for change in self.change_set.files:
            if not change.forbidden:
                self.decision_requested.emit(CodexReviewDecision("accept", change.relative_path))
        self.review_completed.emit()

    def _set_wrap(self, enabled: bool) -> None:
        mode = (QPlainTextEdit.LineWrapMode.WidgetWidth if enabled
                else QPlainTextEdit.LineWrapMode.NoWrap)
        self.diff_view.setLineWrapMode(mode)

    def _find_next(self) -> None:
        if self.search.text():
            self.diff_view.find(self.search.text())

    def _find_previous(self) -> None:
        if self.search.text():
            self.diff_view.find(self.search.text(), QTextDocument.FindFlag.FindBackward)

    def _copy_selection(self) -> None:
        selected = self.diff_view.textCursor().selectedText().replace("\u2029", "\n")
        if selected:
            QApplication.clipboard().setText(selected[:100_000])
