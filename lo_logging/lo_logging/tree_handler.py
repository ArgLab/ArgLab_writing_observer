import hashlib

def compute_hash_str(input: str) -> str:
    return hashlib.sha256(input.encode('utf-8')).hexdigest() 

#This is highly inefficient, but it works for now.
def compute_root(nodes):
    paired_nodes = []
    resultant = []
    
    if len(nodes) % 2 != 0:
        nodes.extend(nodes[-1:])
        
    for i in range(0, len(nodes), 2):
        paired_nodes.append([nodes[i], nodes[i+1]])
        
    if len(paired_nodes) == 1:
        return Node(paired_nodes[0][0].get_hash() + paired_nodes[0][1].get_hash())
    
    for x in range(0, len(paired_nodes)):
        left = paired_nodes[x][0]
        right = paired_nodes[x][1]
        
        lefthash = left.get_hash()
        righthash = right.get_hash()
        
        resultant.append(Node(lefthash + righthash))
    
    if len(resultant) != 2:
        return compute_root(resultant)
    
    return Node(resultant[0].get_hash() + resultant[1].get_hash())


class Node:
    def __init__(self, value: str):
        self.value = value
        self.hash = compute_hash_str(self.value)
        
    def get_hash(self) -> str:
        return self.hash
    
    @staticmethod
    def get_nodes(values: str):
        return list(map(lambda x: Node(x), values))


class Tree:
    def __init__(self):
        self.root_hash = None
        self.values = []
        self.nodes = []
    
    def set_values(self, values):
        self.values = values
        
    def append(self, value):
        self.values.append(value)
        
    def remove(self, value):
        self.values.remove(value)
        
    def get_nodes(self):
        return self.nodes

    def generate(self):
        self.nodes = Node.get_nodes(self.values)
        
        self.root_hash = compute_root(self.nodes)
        
    def get_root(self):
        return self.root_hash