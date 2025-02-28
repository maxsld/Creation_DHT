import simpy
import random

class Node:
    def __init__(self, env, identifier):
        self.env = env
        self.identifier = identifier
        self.left = self  # Au début, il est son propre voisin
        self.right = self

    def __repr__(self):
        return f"Node({self.identifier})"

class DHT:
    def __init__(self, env):
        self.env = env
        self.nodes = []
    
    def insert(self, identifier):
        new_node = Node(self.env, identifier)
        
        if not self.nodes:
            self.nodes.append(new_node)
        else:
            # Trouver la position correcte pour insérer le nœud
            self.nodes.append(new_node)
            self.nodes.sort(key=lambda node: node.identifier)
            
            # Mettre à jour les voisins
            for i in range(len(self.nodes)):
                self.nodes[i].left = self.nodes[i-1]
                self.nodes[i].right = self.nodes[(i+1) % len(self.nodes)]
        
    def remove(self, identifier):
        node_to_remove = next((node for node in self.nodes if node.identifier == identifier), None)
        
        if node_to_remove:
            left_node = node_to_remove.left
            right_node = node_to_remove.right
            left_node.right = right_node
            right_node.left = left_node
            self.nodes.remove(node_to_remove)
    
    def display_ring(self):
        if not self.nodes:
            print("DHT vide")
            return
        
        start = self.nodes[0]
        current = start
        
        print("DHT Ring:")
        while True:
            print(f"[{current.identifier}] -> ", end="")
            current = current.right
            if current == start:
                break
        print("...")

# Exemple d'utilisation
env = simpy.Environment()
dht = DHT(env)
identifiers = sorted([random.randint(1, 100) for _ in range(3)])

for id_ in identifiers:
    dht.insert(id_)

dht.display_ring()
dht.remove(identifiers[2])
dht.display_ring()