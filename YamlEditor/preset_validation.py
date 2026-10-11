"""Validate the editor's preset format before changing its in-memory state."""


def validate_job(job):
    if not isinstance(job, dict):
        raise ValueError('Each job must be a YAML mapping.')
    result = dict(job)
    for field, default in [('name', 'Unnamed Job'), ('runs-on', '')]:
        value = result.get(field, default)
        if not isinstance(value, str):
            raise ValueError(f'Job {field} must be text.')
        result[field] = value
    steps = result.get('steps')
    if steps is None:
        steps = []
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise ValueError('Steps must be a YAML list of mappings, without an outer steps: key.')
    environment = result.get('env')
    if environment is None:
        environment = {}
    if not isinstance(environment, dict) or any(not isinstance(key, str) for key in environment):
        raise ValueError('Env must be a YAML mapping with text keys, without an outer env: key.')
    result['steps'] = steps
    result['env'] = environment
    return result


def validate_preset(data):
    if not isinstance(data, dict):
        raise ValueError('A preset must be a YAML mapping containing name and jobs.')
    name = data.get('name', 'UnnamedPreset')
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Preset name must be non-empty text.')
    raw_jobs = data.get('jobs', [])
    if not isinstance(raw_jobs, list):
        raise ValueError('Preset jobs must be a YAML list; workflow job mappings are not presets.')
    jobs = []
    for index, job in enumerate(raw_jobs, 1):
        if isinstance(job, str):
            job = {'name': job, 'runs-on': ''}
        try:
            jobs.append(validate_job(job))
        except ValueError as error:
            raise ValueError(f'Job {index}: {error}') from error
    return name, jobs
