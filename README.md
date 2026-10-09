# GitHub Actions Generator

A Python desktop editor built with PyQt5 for creating and editing named job
presets in YAML. Manage presets, add or remove jobs, and edit each job's name,
runner, steps, and environment variables.

## Run locally

Use Python 3 and a graphical desktop. From the repository root:

```sh
git clone https://github.com/nirtuttnauer/github_actions_generator.git
cd github_actions_generator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Qt requires a
working display and the platform libraries needed by PyQt5.

## Editing and saving

1. Click **Create Preset**, then **Add Job**.
2. Click the job in the list to open its editor.
3. Enter steps as a YAML list and environment variables as a YAML mapping.
   Enter the values directly, without outer `steps:` or `env:` keys:

   Steps:
   ```yaml
   - name: Say hello
     run: echo hello
   ```

   Environment:
   ```yaml
   GREETING: hello
   ```
4. Click **Save Changes** to update the job in memory.
5. Click **Save Preset** to write a YAML file. **Load Preset** reopens that file.

Save each preset before closing; there is no automatic persistence or unsaved
changes prompt. Deleting a preset removes it from memory, not from disk.
Only load trusted preset files; malformed input is not fully validated.

## Preset format and limitations

Saved files use this application-specific structure:

```yaml
name: Example
jobs:
  - name: Greeting
    runs-on: ubuntu-latest
    steps:
      - name: Say hello
        run: echo hello
    env:
      GREETING: hello
```

This is **not a ready-to-run GitHub Actions workflow**: jobs are stored as a
list rather than a mapping of job IDs, and workflow triggers are not generated.
Convert the preset into a complete workflow before placing it in
`.github/workflows/`. The application edits YAML; it does not execute jobs or
publish workflows to GitHub.

## Development

Runtime dependencies are listed in `requirements.txt`. There is currently no
automated test suite. A syntax-only check (not a GUI or behavior test) is:

```sh
python -m compileall -q main.py YamlEditor
```

Python bytecode, local virtual environments, and editor/OS artifacts are ignored
by Git.
