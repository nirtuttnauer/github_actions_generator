from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
     QLabel, QListWidget, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------
# PresetManagerWidget
#    - Handles the list of presets on the left
#    - Create/Load/Delete
#    - Emits signals when something changes
# ----------------------------------------------------------------------
class PresetManagerWidget(QWidget):
    presetSelected = pyqtSignal(str)    # Emitted when user selects a preset
    presetDeleted = pyqtSignal(str)     # Emitted when user deletes a preset
    createRequested = pyqtSignal()      # Emitted when user clicks "Create Preset"
    loadRequested = pyqtSignal()        # Emitted when user clicks "Load Preset"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(8, 8, 8, 8)
        self.layout().setSpacing(8)

        # Title
        presets_label = QLabel("Presets", alignment=Qt.AlignCenter)
        presets_label.setStyleSheet("font-weight: bold;")

        self.layout().addWidget(presets_label)

        # List of presets
        self.presets_list = QListWidget()
        self.layout().addWidget(self.presets_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.btn_create = QPushButton("Create Preset")
        self.btn_load = QPushButton("Load Preset")
        self.btn_delete = QPushButton("Delete Preset")

        button_layout.addWidget(self.btn_create)
        button_layout.addWidget(self.btn_load)
        button_layout.addWidget(self.btn_delete)
        self.layout().addLayout(button_layout)

        # Connections
        self.presets_list.currentItemChanged.connect(self._on_current_item_changed)
        self.btn_create.clicked.connect(lambda: self.createRequested.emit())
        self.btn_load.clicked.connect(lambda: self.loadRequested.emit())
        self.btn_delete.clicked.connect(self._on_delete_clicked)

    def refresh_list(self, preset_names):
        """Rebuild the list of presets from the given iterable of names."""
        self.presets_list.clear()
        for name in sorted(preset_names):
            self.presets_list.addItem(name)

    def set_current_preset(self, preset_name):
        """Select a preset in the list if it exists."""
        matches = self.presets_list.findItems(preset_name, Qt.MatchExactly)
        if matches:
            self.presets_list.setCurrentItem(matches[0])

    def _on_current_item_changed(self, current, previous):
        if current:
            self.presetSelected.emit(current.text())

    def _on_delete_clicked(self):
        item = self.presets_list.currentItem()
        if item:
            preset_name = item.text()
            self.presetDeleted.emit(preset_name)
