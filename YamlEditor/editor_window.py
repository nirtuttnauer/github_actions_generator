import sys
import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox
)
from YamlEditor.job_editor_widget import JobEditorWidget
from YamlEditor.job_list_widget import JobListWidget
from YamlEditor.preset_manager_widget import PresetManagerWidget


class GitHubActionsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Actions Editor - Enhanced (Split Objects)")
        self.resize(1920, 1080)

        # Data Model: dict of { preset_name -> list of job dicts }
        self.presets = {}
        self.current_preset = None

        # ----------------------------
        # Styling
        # ----------------------------
        self.setStyleSheet("""
            QListWidget, QTreeWidget {
                border: 1px solid #CCCCCC;
            }
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 4px 8px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QGroupBox {
                background-color: #0B0B0B;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                margin-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLabel {
                font-size: 14px;
                color: #ffffff;
            }
            QLineEdit, QPlainTextEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 2px;
            }
        """)

        # ----------------------------
        # Main Splitter (2 columns)
        # ----------------------------
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)
        main_splitter.setHandleWidth(1)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStyleSheet("QSplitter::handle { background: #cccccc; }")

        # Left: PresetManagerWidget
        self.preset_manager = PresetManagerWidget()
        main_splitter.addWidget(self.preset_manager)

        # Right: Another splitter (vertical)
        self.right_splitter = QSplitter(Qt.Vertical)  # Store a reference
        self.right_splitter.setHandleWidth(1)
        self.right_splitter.setChildrenCollapsible(False)
        self.right_splitter.setStyleSheet("QSplitter::handle { background: #cccccc; }")
        main_splitter.addWidget(self.right_splitter)

        # Force left column ~300px, rest ~1620
        main_splitter.setSizes([300, 1620])

        # Top: JobListWidget
        self.job_list_widget = JobListWidget()
        self.right_splitter.addWidget(self.job_list_widget)

        # Bottom: JobEditorWidget
        self.job_editor = JobEditorWidget()
        self.right_splitter.addWidget(self.job_editor)

        # Hide the right splitter at first (if no preset selected)
        self.right_splitter.setVisible(False)

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        # PresetManagerWidget signals
        self.preset_manager.createRequested.connect(self._on_create_preset)
        self.preset_manager.loadRequested.connect(self._on_load_preset)
        self.preset_manager.presetDeleted.connect(self._on_delete_preset)
        self.preset_manager.presetSelected.connect(self._on_preset_selected)

        # JobListWidget signals
        self.job_list_widget.addJobRequested.connect(self._on_add_job)
        self.job_list_widget.removeJobRequested.connect(self._on_remove_job)
        self.job_list_widget.jobSelected.connect(self._on_job_selected_in_list)
        self.job_list_widget.savePresetRequested.connect(self._on_save_current_preset)

        # JobEditorWidget signals
        self.job_editor.jobSaved.connect(self._on_job_saved)

    # --------------------------------------------------------------------------
    # Preset Handling
    # --------------------------------------------------------------------------
    def _on_create_preset(self):
        new_name = self._get_unique_preset_name("NewPreset")
        self.presets[new_name] = []
        self.preset_manager.refresh_list(self.presets.keys())
        self.preset_manager.set_current_preset(new_name)
        self.current_preset = new_name

        # Show right splitter now that we have a selected preset
        self.right_splitter.setVisible(True)
        self._populate_jobs()

    def _on_load_preset(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Preset File", "", "YAML Files (*.yaml *.yml)"
        )
        if file_name:
            with open(file_name, "r") as file:
                data = yaml.safe_load(file) or {}
            preset_name = data.get("name", "UnnamedPreset")
            raw_jobs = data.get("jobs", [])
            jobs = []
            for j in raw_jobs:
                if isinstance(j, dict):
                    jobs.append(j)
                elif isinstance(j, str):
                    jobs.append({"name": j, "runs-on": ""})
            self.presets[preset_name] = jobs
            self.preset_manager.refresh_list(self.presets.keys())
            self.preset_manager.set_current_preset(preset_name)
            self.current_preset = preset_name

            # Show the right splitter
            self.right_splitter.setVisible(True)
            self._populate_jobs()

    def _on_delete_preset(self, preset_name):
        if preset_name in self.presets:
            del self.presets[preset_name]
        self.preset_manager.refresh_list(self.presets.keys())

        # If we deleted the preset that was currently selected, reset
        if self.current_preset == preset_name:
            self.current_preset = None
            self.job_list_widget.refresh_jobs([])
            self.job_editor.clear_job()
            # Hide the right splitter since no preset is selected
            self.right_splitter.setVisible(False)

    def _on_preset_selected(self, preset_name):
        """
        Called when user selects a preset in the left list.
        If preset_name is valid, show right side; else hide it.
        """
        self.current_preset = preset_name

        if not preset_name:
            # Hide the right side if no preset
            self.right_splitter.setVisible(False)
            return

        # Otherwise, show the right side
        self.right_splitter.setVisible(True)
        self._populate_jobs()

    # --------------------------------------------------------------------------
    # Job List Handling
    # --------------------------------------------------------------------------
    def _populate_jobs(self):
        """Refresh the job list for the currently selected preset."""
        if not self.current_preset:
            self.job_list_widget.refresh_jobs([])
            self.job_editor.clear_job()
            # Right side is hidden, done
            return

        jobs = self.presets[self.current_preset]
        self.job_list_widget.refresh_jobs(jobs)
        self.job_editor.clear_job()

    def _on_add_job(self):
        if not self.current_preset:
            return
        jobs = self.presets[self.current_preset]
        new_job = {
            "name": "New Job",
            "runs-on": "",
            "steps": [],
            "env": {}
        }
        jobs.append(new_job)
        self._populate_jobs()
        # Select the new job
        index = len(jobs) - 1
        self.job_list_widget.set_current_job_index(index)

    def _on_remove_job(self, job_index):
        if not self.current_preset:
            return
        jobs = self.presets[self.current_preset]
        if 0 <= job_index < len(jobs):
            jobs.pop(job_index)
        self._populate_jobs()

    def _on_job_selected_in_list(self, job_index):
        if not self.current_preset:
            return
        jobs = self.presets[self.current_preset]
        if 0 <= job_index < len(jobs):
            job_dict = jobs[job_index]
            self.job_editor.load_job(job_dict, job_index)

    def _on_save_current_preset(self):
        self._save_current_preset()

    # --------------------------------------------------------------------------
    # Job Editor Handling
    # --------------------------------------------------------------------------
    def _on_job_saved(self, updated_job):
        if not self.current_preset:
            return
        idx = updated_job.pop("__index__", None)
        if idx is None:
            return
        jobs = self.presets[self.current_preset]
        if 0 <= idx < len(jobs):
            jobs[idx].update(updated_job)
            self._populate_jobs()

    # --------------------------------------------------------------------------
    # Saving the Current Preset to File
    # --------------------------------------------------------------------------
    def _save_current_preset(self):
        if not self.current_preset:
            return
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Preset As", f"{self.current_preset}.yaml",
            "YAML Files (*.yaml *.yml)"
        )
        if file_name:
            data = {
                "name": self.current_preset,
                "jobs": self.presets[self.current_preset]
            }
            try:
                with open(file_name, "w") as f:
                    yaml.dump(
                        data, f,
                        default_flow_style=False,
                        sort_keys=False,
                        indent=2,
                        width=80
                    )
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Could not save file:\n{e}")

    # --------------------------------------------------------------------------
    # Utility
    # --------------------------------------------------------------------------
    def _get_unique_preset_name(self, base):
        """Generate a unique preset name if base already exists."""
        name = base
        i = 1
        while name in self.presets:
            name = f"{base}_{i}"
            i += 1
        return name

    # --------------------------------------------------------------------------
    # Close
    # --------------------------------------------------------------------------
    def closeEvent(self, event):
        super().closeEvent(event)