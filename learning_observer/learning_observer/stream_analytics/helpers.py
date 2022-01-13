'''
Common utility functions for working with analytics modules.

The goal is to have the modules be pluggable and independent of the
system. For now, our overall system diagram is:

+---------------+
|               |                                   +-------------+
| Event Source  ---|                                | Key-Value   |
|               |  |                                | Store       |
+---------------+  |                                |             |
+---------------+  |          +-----------+  <------|-- Internal  |
|               |  |          |           |  -------|-> State     |       +------------+      +------------+
| Event Source  --------|---->| Reducer   |         |             |       |            |      |            |
|               |   |   |     |           | --------|-> External -------->| Aggregator |----> | Dashboard  |
+---------------+   |   |     +-----------+         |   State     |       |            |      |            |
+---------------+   |   |                           |             |       +------------+      +------------+
|               |   |   |                           +-------------+
| Event Source  ----|   |
|               |       |
+---------------+       v
                  +------------+
                  |            |
                  |  Archival  |
                  | Repository |
                  |            |
                  +------------+

We create reducers with the `student_event_reducer` decorator. In the
longer term, we'll want to be able to plug together different
aggregators, state types, etc. We'll also want different keys for
reducers (per-student, per-resource, etc.). For now, though, this
works.
'''

import copy
import functools

import learning_observer.kvs
from learning_observer.stream_analytics.fields import KeyStateType, KeyField, EventField, Scope


def fully_qualified_function_name(func):
    '''
    Takes a function. Return a fully-qualified string with a name for
    that function. E.g.:

    >>> from math import sin
    >>> fully_qualified_function_name(math.sin)
    'math.sin'

    This is helpful for then giving unique names to analytics modules. Each module can
    be uniquely referenced based on its reduce function.
    '''
    return "{module}.{function}".format(
        module=func.__module__,
        function=func.__qualname__
    )


def make_key(func, key_dict, state_type):
    '''
    Create a KVS key.

    It combines:

    * A fully-qualified name for the reducer function
    * A dictionary of fields
    * Whether the key is internal or external

    Into a unique string

    For example:
    >>> make_key(
          some_module.reducer,
          {h.KeyField.STUDENT: 123}, 
          h.KeyStateType.INTERNAL
    )
    'Internal,some_module.reducer,STUDENT:123'
    '''
    # pylint: disable=isinstance-second-argument-not-valid-type
    assert isinstance(state_type, KeyStateType)
    assert callable(func)

    streammodule = fully_qualified_function_name(func)

    safe_user_id = key_dict[KeyField.STUDENT]

    # Key starts with whether it is internal versus external state, and what module it comes from
    key_list = [
        state_type.name.capitalize(),
        streammodule
    ]

    # It continues with the fields. These are organized as key-value
    # pairs. These need a well-defined order. I'm sure there's a
    # logical order here, but for now, we do alphabetical.
    #
    # We will want to be able to do reduce operations across multiple
    # axes. This is where an RDS with multiple indexes might be nice,
    # if we can figure out the sharding, etc. Another alternative
    # might be to use postgres to organize things (which changes
    # rarely), but to keep actual key/value pairs in redis (which
    # changes a lot).
    for key in sorted(key_dict.keys(), key = lambda x: x.name):
        key_list.append("{key}:{value}".format(key=key.name, value=key_dict[key]))

    # And we return this as comma-seperated values
    return ",".join(key_list)


def kvs_pipeline(
        null_state=None,
        scope=None
):
    '''
    Closures, anyone?

    There's a bit to unpack here.

    Top-level function. This allows us to configure the decorator (and
    returns the decorator).

    * `null_state` tells us the empty state, before any reduce operations have
      happened. This can be important for the aggregator. We're documenting the
      code before we've written it, so please make sure this works before using.
    '''
    if scope==None:
        print("TODO: explicitly specify a scope")
        print("Defaulting to student scope")
        scope = Scope([KeyField.STUDENT])

    def decorator(func):
        '''
        The decorator itself
        '''
        @functools.wraps(func)
        def wrapper_closure(metadata):
            '''
            The decorator itself. We create a function that, when called,
            creates an event processing pipeline. It keeps a pointer
            to the KVS inside of the closure. This way, each pipeline has
            its own KVS. This is the level at which we want consistency,
            want to allow sharding, etc. If two users are connected, each
            will have their own data store connection.
            '''
            taskkvs = learning_observer.kvs.KVS()
            keydict = {}

            if KeyField.STUDENT in scope:
                if metadata is not None and 'auth' in metadata:
                    safe_user_id = metadata['auth']['safe_user_id']
                else:
                    safe_user_id = '[guest]'
                keydict[KeyField.STUDENT] = safe_user_id

            async def process_event(event, **additional_metadata):
                '''
                This is the function which processes events. It calls the event
                processor, passes in the event(s) and state. It takes
                the internal state and the external state from the
                event processor. The internal state goes into the KVS
                for use in the next call, while the external state
                returns to the dashboard.

                The external state should include everything needed
                for the dashboard visualization and exclude anything
                large or private. The internal state needs everything
                needed to continue reducing the events.
                '''
                # TODO: Think through concurrency.
                #
                # We could put this inside of a transaction, but we
                # would lose a few orders of magnitude in performance.
                #
                # We could keep this outside of a transaction, and handle
                # occasional issues.
                #
                # It's worth noting that:
                #
                # 1. We have an archival record, and we can replay if there
                #    are issues
                # 2. We keep this open on a per-session basis. The only way
                #    we might run into concurrency issues is if a student
                #    is e.g. actively editing on two computers at the same
                #    time
                # 3. If we assume e.g. occasional disconnected operation, as
                #    on a mobile device, we'll have concurrency problems no
                #    matter what. In many cases, we should handle this
                #    explicitly rather than implicitly, for example, with
                #    conflict-free replicated data type (CRDTs) or explicit
                #    merge operation
                #
                # Fun!
                #
                # But we can think of more ways we might get concurrency
                # issues in the future, once we do per-class / per-resource /
                # etc. reducers.
                #
                # * We could funnel these into a common reducer. That'd be easy
                #   enough and probably the right long-term solution
                # * We could have modules explicitly indicate where they need
                #   thread safety and transactions. That'd be easy enough.
                for field in scope:
                    # Skip out-of-scope events. E.g. if we have an event stream
                    # where we're scoped to a document ID, we want to skip global events,
                    # which don't have that document ID
                    if field not in keydict and isinstance(field, EventField):
                        AMG = additional_metadata.get(field.event, None)
                        if AMG is None:
                            return None
                        keydict[field] = AMG

                internal_key = make_key(
                    func,
                    keydict,
                    KeyStateType.INTERNAL
                )
                external_key = make_key(
                    func,
                    keydict,
                    KeyStateType.EXTERNAL
                )

                internal_state = await taskkvs[internal_key]
                if internal_state is None:
                    internal_state = copy.deepcopy(null_state)
                    await taskkvs.set(internal_key, internal_state)

                internal_state, external_state = await func(
                    event, internal_state
                )

                # We would like to give reducers the option to /not/ write
                # on all events
                if internal_state is not False:
                    await taskkvs.set(internal_key, internal_state)
                if external_state is not False:
                    await taskkvs.set(external_key, external_state)
                return external_state
            return process_event
        return wrapper_closure
    return decorator

# `kvs_pipeline`, in it's current incarnation, is obsolete.
#
# We will now have reducers of multiple types.
#
# We will probably keep `kvs_pipeline` as a generic, and this is part of that
# transition.
student_event_reducer = functools.partial(kvs_pipeline, scope=Scope([KeyField.STUDENT]))
