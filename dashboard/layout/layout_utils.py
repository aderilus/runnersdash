from pathlib import Path


def get_project_root(test=False):
    root = Path(__file__).parent.parent.parent
    if test:
        print('Project root: ', root)
    return root
