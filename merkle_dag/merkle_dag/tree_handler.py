import hashlib
import json
import secrets
import os

'''
    This module lays the foundation for the project 
    discussed in Ben Beehler's Research Report on implementating a
    Merkle DAG within WO for data validation. At the moment, support 
    only exists for session files, containing individual logs, that are 
    arranged within dirs in a linked list structure. JSON is used for 
    its high versatility and ability to be stored as a DA in string form.
'''

def jsonify(value):
    return json.loads(json.dumps(value))

def default_salt():
    return secrets.token_hex(8)

def hash(value, salt) -> str:
    hash_value = hashlib.sha512()
    hash_value.update(value.encode('utf8'))
    hash_value.update(salt.encode('utf8'))
    
    return hash_value.hexdigest()

'''
    Construct log files stored in session files within lists
'''
def construct_log_dump(log, salt, previous_log_hash):
    value = hash(log, salt)
    
    if previous_log_hash == None:
        previous_log_hash = 'undefined'
    
    return {
                'value': value, 
                'salt': salt, 
                'previous': previous_log_hash
            }

'''
    Construct session files that contain logs. Student files (like git commits)
    will serve as pointers to these files.
'''
def construct_session_dump(hashed_logs, previous_session, student_name, salt, timestamp):
    str_hashes = list(map(lambda x: str(x), hashed_logs))
    
    primitive_value = "".join(str_hashes)
    
    value = hash(primitive_value, default_salt())
    
    if previous_session == None:
        previous_session = 'undefined'
    
    return {
                'header': {
                    'student_name': student_name,
                    'salt': salt,
                    'timestamp': timestamp,
                    'value': value,
                    'previous': previous_session,
                },
                'logs': hashed_logs
            }
        
'''
    Retrieve a new session file.
'''
def get_session(hash, path):
    f_name = os.path.join(path, hash + ".session")
    
    with open(f_name) as f:
        f_lines = f.readlines()
        
        f_content = "".join(f_lines)
        
        return json.loads(f_content)

'''
    Retrieve a list of sessions coming before 
    a given session in the linked list structure.
'''
def get_session_list(hash, path):
    session = get_session(hash, path)
    
    session_list = []
    session_list.append(jsonify(session))
    
    previous = session['header']['previous']
    
    while previous != 'undefined':        
        session = get_session(previous, path)
        previous = session['header']['previous']
        
        session_list.append(jsonify(session))
        
    return session_list
    
'''
    Correctly generate a new session file within a log.
    These sessions are immutable.
'''
def io_new_session(session_obj, path):
    f_name = session_obj['header']['value'] + ".session"
    
    f_path = os.path.join(path, f_name)
    
    f = open(f_path, "x")
    f.write(json.dumps(session_obj))
    f.close()
