from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QGroupBox, QFormLayout, QComboBox, QPlainTextEdit, QMessageBox
)
import yaml

# ----------------------------------------------------------------------
# JobEditorWidget
#    - Displays fields for a single job (name, runs-on, steps, env)
#    - Allows saving changes back to the data model
# ----------------------------------------------------------------------
class JobEditorWidget(QGroupBox):
    jobSaved = pyqtSignal(dict)   # Emitted with the updated job dictionary

    def __init__(self, parent=None):
        super().__init__("Job Editor", parent)
        self.setVisible(False)  # hidden until a job is selected

        form_layout = QFormLayout()
        self.setLayout(form_layout)

        # Fields
        self.job_name_edit = QLineEdit()
        self.job_runs_on_combo = QComboBox()
        self.job_runs_on_combo.addItems([
            "ubuntu-latest", "windows-latest", "macos-latest",
            "ubuntu-22.04", "ubuntu-20.04",
            "windows-2022", "macos-12"
        ])
        self.job_steps_edit = QPlainTextEdit()
        self.job_steps_edit.setPlaceholderText(
            "steps:\n  - name: Checkout code\n    uses: actions/checkout@v2"
        )
        self.job_env_edit = QPlainTextEdit()
        self.job_env_edit.setPlaceholderText(
            "env:\n  FOO: bar\n  BAZ: 123"
        )

        self.btn_save_job = QPushButton("Save Changes")

        form_layout.addRow("Job Name:", self.job_name_edit)
        form_layout.addRow("Runs On:", self.job_runs_on_combo)
        form_layout.addRow("Steps (YAML):", self.job_steps_edit)
        form_layout.addRow("Environment (YAML):", self.job_env_edit)
        form_layout.addWidget(self.btn_save_job)

        # Internal tracking of current job index or data
        self._current_job_index = None
        self._current_job = None

        # Connections
        self.btn_save_job.clicked.connect(self._on_save_job)

    def load_job(self, job_dict, job_index):
        """
        Populate fields from the given job dict.
        Store job_index so we can identify which job we are editing.
        """
        self._current_job_index = job_index
        self._current_job = job_dict

        self.job_name_edit.setText(job_dict.get("name", ""))
        runs_on_value = job_dict.get("runs-on", "")
        idx = self.job_runs_on_combo.findText(runs_on_value)
        if idx == -1 and runs_on_value:
            self.job_runs_on_combo.addItem(runs_on_value)
            idx = self.job_runs_on_combo.count() - 1
        self.job_runs_on_combo.setCurrentIndex(idx if idx >= 0 else 0)

        # Steps
        steps_data = job_dict.get("steps", [])
        steps_yaml = yaml.dump(steps_data, default_flow_style=False, sort_keys=False)
        self.job_steps_edit.setPlainText(steps_yaml)

        # Env
        env_data = job_dict.get("env", {})
        env_yaml = yaml.dump(env_data, default_flow_style=False, sort_keys=False)
        self.job_env_edit.setPlainText(env_yaml)

        self.setVisible(True)

    def clear_job(self):
        """Hide and clear the form."""
        self._current_job_index = None
        self._current_job = None
        self.setVisible(False)

    def _on_save_job(self):
        """Gather data from fields and emit jobSaved signal with updated job data."""
        if self._current_job is None:
            return

        job_name = self.job_name_edit.text()
        runs_on_value = self.job_runs_on_combo.currentText()

        # Steps
        steps_yaml = self.job_steps_edit.toPlainText().strip()
        steps_data = []
        if steps_yaml:
            try:
                steps_data = yaml.safe_load(steps_yaml)
            except yaml.YAMLError as e:
                QMessageBox.warning(self, "YAML Error", f"Error parsing steps:\n{e}")
                return

        # Env
        env_yaml = self.job_env_edit.toPlainText().strip()
        env_data = {}
        if env_yaml:
            try:
                env_data = yaml.safe_load(env_yaml)
                if not isinstance(env_data, dict):
                    QMessageBox.warning(self, "YAML Error", "Env must be a YAML dictionary.")
                    return
            except yaml.YAMLError as e:
                QMessageBox.warning(self, "YAML Error", f"Error parsing env:\n{e}")
                return

        updated_job = {
            "name": job_name,
            "runs-on": runs_on_value,
            "steps": steps_data,
            "env": env_data
        }
        # We can store the index if needed, or just send the dict
        updated_job["__index__"] = self._current_job_index

        self.jobSaved.emit(updated_job)
