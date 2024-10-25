'''
Commonplace for learning observer constants.
Many of these are dictionary keys we access frequently.
Using the constants protect us from typos.

Over time, we plan to add migrate more constants here,
but adding ALL constants here is not a goal. Many
constants are better locally-scoped (or otherwise have
good reason to live elsewhere.
'''
# used in request headers to hold auth information
AUTH_HEADERS = 'auth_headers'
CANVAS_AUTH_HEADERS = 'canvas_auth_headers'
# used for storing impersonation information in session
IMPERSONATING_AS = 'impersonating_as'

# used for fetching user object from request or session
USER = 'user'
# common user id reference for user object
USER_ID = 'user_id'

# used to identify LMSes
GOOGLE = 'google'
CANVAS = 'canvas'
