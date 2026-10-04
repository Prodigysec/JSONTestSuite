#!/usr/bin/env python3
"""Validate roadmap ordering and completion evidence without inferring results."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'todo', 'in_progress', 'done', 'blocked'}
BASES = {'Measured', 'Documented', 'Heuristic'}


def validate(data):
    tasks = data['tasks']
    ids = [task['id'] for task in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate task ID')
    seen = set()
    unfinished = False
    active = 0
    for task in tasks:
        for key in ('id', 'title', 'dependencies', 'deliverables', 'acceptance_commands', 'status'):
            if key not in task:
                raise ValueError('Missing task field: ' + key)
        if task['status'] not in STATUSES:
            raise ValueError('Unknown task status')
        if not set(task['dependencies']) <= seen:
            raise ValueError('Task dependency must precede the task')
        if not task['deliverables'] or not task['acceptance_commands']:
            raise ValueError('Deliverables and acceptance commands are required')
        if not all(isinstance(command, str) and command for command in task['acceptance_commands']):
            raise ValueError('Acceptance commands must be nonempty strings')
        if unfinished and task['status'] in {'done', 'in_progress'}:
            raise ValueError('Task execution must follow roadmap order')
        if task['status'] == 'done' and not task.get('verification'):
            raise ValueError('Done task needs recorded verification')
        active += task['status'] == 'in_progress'
        unfinished |= task['status'] != 'done'
        seen.add(task['id'])
    if active > 1:
        raise ValueError('Only one task may be active')
    parsers = data['parsers']
    if len({entry['id'] for entry in parsers}) != len(parsers):
        raise ValueError('Duplicate parser ID')
    for entry in parsers:
        for key in ('id', 'title', 'language', 'tier', 'basis_tag', 'source_url',
                    'version_to_pin', 'build_steps', 'priority', 'status'):
            if key not in entry:
                raise ValueError('Missing parser field: ' + key)
        if entry['status'] not in STATUSES or entry['basis_tag'] not in BASES:
            raise ValueError('Invalid parser status or external basis tag')
        if entry.get('task_id') and entry['task_id'] not in seen:
            raise ValueError('Parser references unknown task')
        if entry['source_verified'] and not all(entry.get(key) for key in
                                                ('source_url', 'version_to_pin', 'license', 'source_verification')):
            raise ValueError('Verified source requires pin, license, and provenance')
        if entry['status'] == 'done' and entry.get('disposition') != 'excluded-pure-wrapper':
            evidence = entry.get('verification', {})
            if not evidence:
                raise ValueError('Done parser needs observed evidence or explicit exclusion')
    return tasks, parsers


def check_task(data, task_id):
    tasks, parsers = validate(data)
    task = next((task for task in tasks if task['id'] == task_id), None)
    if task is None:
        raise ValueError('Unknown task ID: ' + task_id)
    for path in task['deliverables']:
        if path.startswith(('docs/', 'tools/', 'tests/', 'parsers/', 'test_features/', 'metadata/')) or path.endswith('.py'):
            if not (ROOT / path).exists():
                raise ValueError('Missing deliverable: ' + path)
    if task_id.startswith('P3-'):
        for entry in parsers:
            if entry['id'] in task['parser_ids'] and not entry.get('verification') and not entry.get('disposition'):
                raise ValueError('Parser lacks verification/disposition: ' + entry['title'])
    print(task_id + ': deliverables and recorded evidence checked')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--task')
    args = parser.parse_args(argv)
    try:
        data = json.loads((ROOT / 'docs/roadmap/backlog.json').read_text())
        tasks, parsers = validate(data)
        if args.task:
            check_task(data, args.task)
        print('Roadmap valid: %d ordered tasks, %d parser leads; %d tasks done.' %
              (len(tasks), len(parsers), sum(task['status'] == 'done' for task in tasks)))
    except (KeyError, OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    sys.exit(main())
