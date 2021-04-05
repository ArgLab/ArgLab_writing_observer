'''
This is just a thin wrapper to load out configuration YAML file
from disk.

At some point, it might make sense to make this a thicker wrapper, so
we can have multiple configuration files with includes. As is, we have
credentials in the same place as module configuration, which is not
ideal.

We might also want multiple configuration files on the same system, so
we can run in different modes.
'''

import enum
import sys

import yaml

import learning_observer.paths


print("Startup: Loading settings file")

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)


settings = yaml.safe_load(open(learning_observer.paths.config_file()))

RUN_MODES = enum.Enum('RUN_MODES', 'DEV DEPLOY')

RUN_MODE = None

if 'config' not in settings or 'run_mode' not in settings['config']:
    print("Configuration file must specify a run mode (dev versus deploy)")
    sys.exit(-1)

if settings['config']['run_mode'] == 'dev':
    RUN_MODE = RUN_MODES.DEV
elif settings['config']['run_mode'] == 'deploy':
    RUN_MODE = RUN_MODES.DEPLOY
else:
    print("Configuration setting for run_mode must be either 'dev' or 'deploy'")
    sys.exit(-1)

if 'repos' in settings:
    for repo in settings['repos']:
        # In the future, we might allow dicts if we e.g. want more metadata
        if isinstance(settings['repos'][repo], str):
            learning_observer.paths.register_repo(repo, settings['repos'][repo])
        else:
            print("settings.repos.{repo} should be a string. Fix the settings file.")
            print("We might allow dicts with metadata someday. That day is not today.")
            sys.exit(-1)
