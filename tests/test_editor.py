import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication
import yaml

from YamlEditor.editor_window import GitHubActionsEditor
from YamlEditor.preset_validation import validate_preset

APP = QApplication.instance() or QApplication([])


class PresetTests(unittest.TestCase):
    def setUp(self):
        self.window = GitHubActionsEditor()
        self.addCleanup(self.window.close)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'preset.yaml'
        self.warning = patch('YamlEditor.editor_window.QMessageBox.warning').start()
        self.addCleanup(patch.stopall)

    def load(self, text):
        self.path.write_text(text, encoding='utf-8')
        with patch('YamlEditor.editor_window.QFileDialog.getOpenFileName',
                   return_value=(str(self.path), '')):
            self.window._on_load_preset()

    def test_valid_preset_round_trip_and_unknown_fields(self):
        self.load('name: שלום\njobs:\n  - name: Hello\n    runs-on: custom-runner\n'
                  '    steps:\n      - run: echo hello\n    env: {FOO: bar}\n    timeout-minutes: 5\n')
        expected = {'name': 'שלום', 'jobs': self.window.presets['שלום']}
        self.window._on_job_selected_in_list(0)
        self.assertEqual(self.window.job_editor.job_runs_on_combo.currentText(), 'custom-runner')
        with patch('YamlEditor.editor_window.QFileDialog.getSaveFileName',
                   return_value=(str(self.path), '')):
            self.window._save_current_preset()
        self.assertEqual(yaml.safe_load(self.path.read_text(encoding='utf-8')), expected)
        self.warning.assert_not_called()

    def test_legacy_string_jobs_and_null_fields_are_supported(self):
        name, jobs = validate_preset({'jobs': ['legacy', {'name': 'empty', 'steps': None, 'env': None}]})
        self.assertEqual(name, 'UnnamedPreset')
        self.assertEqual(jobs[0]['name'], 'legacy')
        self.assertEqual(jobs[1]['steps'], [])
        self.assertEqual(jobs[1]['env'], {})

    def test_duplicate_names_keep_existing_preset(self):
        self.load('name: Same\njobs: [original]\n')
        self.load('name: Same\njobs: [new]\n')
        self.assertEqual(self.window.presets['Same'][0]['name'], 'original')
        self.assertEqual(self.window.presets['Same_1'][0]['name'], 'new')
        self.assertEqual(self.window.current_preset, 'Same_1')

    def test_malformed_presets_do_not_change_state(self):
        self.load('name: Existing\njobs: [original]\n')
        for text in ['', '[]', 'name: [bad]', 'name: ""', 'jobs: {}',
                     'jobs: [42]', 'jobs: [{name: 42}]',
                     'jobs: [{runs-on: [linux]}]', 'jobs: [{steps: {run: hello}}]',
                     'jobs: [{steps: [42]}]', 'jobs: [{env: []}]',
                     'jobs: [{env: {42: value}}]', 'jobs: [']:
            with self.subTest(text=text):
                self.warning.reset_mock()
                self.load(text)
                self.warning.assert_called_once()
                self.assertEqual(list(self.window.presets), ['Existing'])
                self.assertEqual(self.window.current_preset, 'Existing')

    def test_unreadable_and_invalid_utf8_files_show_load_error(self):
        for data in [None, b'\xff']:
            if data is not None:
                self.path.write_bytes(data)
            with patch('YamlEditor.editor_window.QFileDialog.getOpenFileName',
                       return_value=(str(self.path), '')):
                self.window._on_load_preset()
            self.assertEqual(self.warning.call_args.args[1], 'Load Error')
            self.assertEqual(self.window.presets, {})

    def test_invalid_steps_and_env_do_not_emit_job_saved(self):
        self.load('name: Existing\njobs: [original]\n')
        self.window._on_job_selected_in_list(0)
        editor = self.window.job_editor
        saved = []
        editor.jobSaved.connect(saved.append)
        for steps, env in [('steps: []', '{}'), ('[42]', '{}'), ('[', '{}'),
                           ('[]', '[]'), ('[]', '{')]:
            with self.subTest(steps=steps, env=env):
                self.warning.reset_mock()
                editor.job_steps_edit.setPlainText(steps)
                editor.job_env_edit.setPlainText(env)
                editor._on_save_job()
                self.warning.assert_called_once()
                self.assertEqual(saved, [])
                self.assertEqual(self.window.presets['Existing'][0]['name'], 'original')

    def test_valid_job_edit_preserves_extra_fields(self):
        self.load('name: Existing\njobs: [{name: original, timeout-minutes: 5}]\n')
        self.window._on_job_selected_in_list(0)
        editor = self.window.job_editor
        editor.job_name_edit.setText('updated')
        editor.job_steps_edit.setPlainText('- run: echo hello')
        editor.job_env_edit.setPlainText('GREETING: hello')
        editor._on_save_job()
        job = self.window.presets['Existing'][0]
        self.assertEqual(job['name'], 'updated')
        self.assertEqual(job['steps'], [{'run': 'echo hello'}])
        self.assertEqual(job['env'], {'GREETING': 'hello'})
        self.assertEqual(job['timeout-minutes'], 5)
        self.assertNotIn('__index__', job)
        self.warning.assert_not_called()


if __name__ == '__main__':
    unittest.main()
