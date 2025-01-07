from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem
)

# ----------------------------------------------------------------------
# JobListWidget
#    - Displays the jobs (tree) for the current preset
#    - Add/Remove jobs
#    - Signal when a job is selected
# ----------------------------------------------------------------------
class JobListWidget(QWidget):
    jobSelected = pyqtSignal(int)          # Emitted with the job index
    addJobRequested = pyqtSignal()         # Emitted when user clicks Add Job
    removeJobRequested = pyqtSignal(int)   # Emitted when user clicks Remove Job on current job
    savePresetRequested = pyqtSignal()     # Emitted when user wants to save the preset

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(8, 8, 8, 8)
        self.layout().setSpacing(8)

        # Top row of buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Job")
        self.btn_remove = QPushButton("Remove Job")
        self.btn_save_preset = QPushButton("Save Preset")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_save_preset)
        self.layout().addLayout(btn_layout)

        # Jobs tree
        self.jobs_tree = QTreeWidget()
        self.jobs_tree.setHeaderLabels(["Jobs"])
        self.layout().addWidget(self.jobs_tree)

        # Connections
        self.btn_add.clicked.connect(lambda: self.addJobRequested.emit())
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        self.btn_save_preset.clicked.connect(lambda: self.savePresetRequested.emit())
        self.jobs_tree.itemClicked.connect(self._on_tree_item_clicked)

    def refresh_jobs(self, jobs):
        """Clear and rebuild the job tree from the given list of jobs (dicts)."""
        self.jobs_tree.clear()
        for job in jobs:
            name = job.get("name", "Unnamed Job")
            item = QTreeWidgetItem([name])
            self.jobs_tree.addTopLevelItem(item)

    def set_current_job_index(self, index):
        """Select a job by index in the tree if valid."""
        if 0 <= index < self.jobs_tree.topLevelItemCount():
            self.jobs_tree.setCurrentItem(self.jobs_tree.topLevelItem(index))

    def _on_tree_item_clicked(self, item, column):
        idx = self.jobs_tree.indexOfTopLevelItem(item)
        if idx >= 0:
            self.jobSelected.emit(idx)

    def _on_remove_clicked(self):
        item = self.jobs_tree.currentItem()
        if item:
            idx = self.jobs_tree.indexOfTopLevelItem(item)
            if idx >= 0:
                self.removeJobRequested.emit(idx)
