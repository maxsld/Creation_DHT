import simpy
import random

class Node:
    existing_ids = set()
    
    def __init__(self, env, identifier):
        if identifier in Node.existing_ids:
            raise ValueError(f"Nœud avec l'identifiant {identifier} existe déjà!")
        Node.existing_ids.add(identifier)
        
        self.env = env
        self.identifier = identifier
        self.left = self  # Initialement seul dans l'anneau
        self.right = self
        self.data = {}  # Stockage clé-valeur pour la DHT
        
        self.env.process(self.run())
    
    def __repr__(self):
        return f"Node({self.identifier})"
    
    def run(self):
        while True:
            yield self.env.timeout(1)
    
    def find_position(self, new_node):
        current = self
        while not (current.identifier < new_node.identifier <= current.right.identifier or (current.right.identifier < current.identifier and (new_node.identifier > current.identifier or new_node.identifier < current.right.identifier))):
            current = current.right
            if current == self:
                break
        return current
    
    def insert(self, new_node):
        position = self.find_position(new_node)
        new_node.right = position.right
        new_node.left = position
        position.right.left = new_node
        position.right = new_node
        print(f"[{self.env.now}] Nœud {new_node.identifier} ajouté entre {position.identifier} et {new_node.right.identifier}")
    
    def remove(self):
        if self.right == self:
            print(f"[{self.env.now}] Dernier nœud {self.identifier} supprimé, anneau vide.")
            Node.existing_ids.remove(self.identifier)
            return None
        
        self.left.right = self.right
        self.right.left = self.left
        
        # Transférer les données au nœud suivant
        for key, value in self.data.items():
            self.right.store(key, value)
        
        Node.existing_ids.remove(self.identifier)
        print(f"[{self.env.now}] Nœud {self.identifier} supprimé, données transférées à {self.right.identifier}")
        return self.right
    
    def store(self, key, value):
        responsible = self.find_successor(key)
        responsible.data[key] = value
        print(f"[{self.env.now}] Clé {key} stockée sur le nœud {responsible.identifier}")
    
    def find_successor(self, key):
        current = self
        while not (current.identifier <= key < current.right.identifier or (current.right.identifier < current.identifier and (key > current.identifier or key < current.right.identifier))):
            current = current.right
            if current == self:
                break
        return current.right
    
    def lookup(self, env, key):
        yield env.timeout(random.randint(1, 3))
        responsible = self.find_successor(key)
        result = responsible.data.get(key, None)
        print(f"[{env.now}] Recherche clé {key}: {result}")
    
    def display_ring(self):
        current = self
        smallest = self
        while True:
            if current.identifier < smallest.identifier:
                smallest = current
            current = current.right
            if current == self:
                break
        
        start = smallest
        nodes = []
        current = start
        while True:
            nodes.append(str(current.identifier))
            current = current.right
            if current == start:
                break
        print("DHT Ring: " + " -> ".join(nodes))

# Simulation
env = simpy.Environment()
nodes = []

def add_node(env, nodes):
    yield env.timeout(random.randint(1, 5))
    while True:
        new_id = random.randint(1, 100)
        if new_id not in Node.existing_ids:
            break
    
    new_node = Node(env, new_id)
    if nodes:
        nodes[0].insert(new_node)
    nodes.append(new_node)
    nodes.sort(key=lambda node: node.identifier)

def remove_node(env, nodes, index):
    yield env.timeout(random.randint(1, 5))
    if len(nodes) > index:
        node_to_remove = nodes[index]
        next_node = node_to_remove.remove()
        nodes.remove(node_to_remove)
        if next_node:
            next_node.display_ring()

def store_key(env, nodes, key, value):
    yield env.timeout(random.randint(1, 5))
    if nodes:
        nodes[0].store(key, value)

def lookup_key(env, nodes, key):
    yield env.timeout(random.randint(1, 5))
    if nodes:
        env.process(nodes[0].lookup(env, key))

for _ in range(5):
    env.process(add_node(env, nodes))

env.run(until=10)

if nodes:
    nodes[0].display_ring()
    env.process(store_key(env, nodes, 42, "Donnée Importante"))
    env.process(lookup_key(env, nodes, 42))

env.run(until=15)

if len(nodes) > 2:
    env.process(remove_node(env, nodes, 2))

env.run(until=20)