NAME = "Logging Structure Base"

# Outgoing APIs
#
# Generically, these would usually serve JSON to dashboards written as JavaScript and
# HTML. These used to be called 'dashboards,' but we're now hosting those as static
# files.

COURSE_AGGREGATORS = {
    # "writing-observer": {
    #     "sources": [  # These are the reducers whose outputs we aggregate
    #         learning_observer.stream_analytics.writing_analysis.time_on_task,
    #         learning_observer.stream_analytics.writing_analysis.reconstruct
    #         # TODO: "roster"
    #     ],
    #     #  Then, we pass the per-student data through the cleaner, if provided.
    #     "cleaner": learning_observer.writing_observer.aggregator.sanitize_and_shrink_per_student_data,
    #     #  And we pass an array of the output of that through the aggregator
    #     "aggregator": learning_observer.writing_observer.aggregator.aggregate_course_summary_stats,
    #     "name": "This is the main Writing Observer dashboard."
    # }
}

STUDENT_AGGREGATORS = {
}

# Incoming event APIs
REDUCERS = [
]


# Required client-side JavaScript downloads
THIRD_PARTY = {
}


# We're still figuring this out, but we'd like to support hosting static files
# from the git repo of the module.
#
# This allows us to have a Merkle-tree style record of which version is deployed
# in our log files.
STATIC_FILE_GIT_REPOS = {
    # 'writing_observer': {
    #     # Where we can grab a copy of the repo, if not already on the system
    #     'url': 'https://github.com/ETS-Next-Gen/writing_observer.git',
    #     # Where the static files in the repo lie
    #     'prefix': 'learning_observer/learning_observer/static',
    #     # Branches we serve. This can either be a whitelist (e.g. which ones
    #     # are available) or a blacklist (e.g. which ones are blocked)
    #     'whitelist': ['master']
    # }
}


# We're kinda refactoring the stuff above to below
#
# The stuff above will become APIs to dashboards. The stuff below
# will register the actual dashboards.
COURSE_DASHBOARDS = [
    # {
    #     'name': "Writing Observer",
    #     'url': "/static/repos/lo_core/writing_observer/master/wobserver.html",
    #     "icon": {
    #         "type": "fas",
    #         "icon": "fa-pen-nib"
    #     }
    # }
]

STUDENT_DASHBOARDS = {
}
