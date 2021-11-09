import lo_logging.tree_handler as tree_handler

'''
Current pathfinder implementation uses a stateful system
with a single tree that can be interacted with at any given
time.
'''

current_tree = tree_handler.Tree()

def get_current_tree():
    return current_tree