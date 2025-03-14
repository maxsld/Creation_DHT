import simpy
import random

class Node:
    def __init__(self, env, identifier):
        self.env = env
        self.identifier = identifier
        self.left = self  # Au départ, seul dans l'anneau
        self.right = self
        self.env.process(self.run())

    def __repr__(self):
        return f"Node({self.identifier})"
    
    def run(self):
        while True:
            yield self.env.timeout(1)  # Simulation d'une action périodique
    
    def find_position(self, new_node):
        """Recherche récursive de la position correcte pour insérer un nouveau nœud."""
        current = self
        while True:
            if current.identifier < new_node.identifier < current.right.identifier or (current.right == self and new_node.identifier > current.identifier):
                return current
            current = current.right
            if current == self:
                return current  # Retourne à lui-même en cas de boucle
    
    def insert(self, new_node):
        """Ajoute un nœud après avoir trouvé la bonne position en interrogeant les voisins."""
        position = self.find_position(new_node)
        new_node.right = position.right
        new_node.left = position
        position.right.left = new_node
        position.right = new_node
        print(f"[{self.env.now}] Nœud {new_node.identifier} ajouté entre {position.identifier} et {new_node.right.identifier}")
    
    def remove(self):
        """Supprime le nœud de l'anneau."""
        if self.right == self:
            print(f"[{self.env.now}] Dernier nœud {self.identifier} supprimé, anneau vide.")
            return None
        
        self.left.right = self.right
        self.right.left = self.left
        print(f"[{self.env.now}] Nœud {self.identifier} supprimé")
        return self.right
    
    def display_ring(self):
        """Affiche l'anneau en se déplaçant à travers les voisins."""
        current = self
        while current.left.identifier < current.identifier:
            current = current.left
        
        start = current
        nodes = []
        while True:
            nodes.append(str(current.identifier))
            current = current.right
            if current == start:
                break
        print("DHT Ring: " + " -> ".join(nodes))

# Simulation
env = simpy.Environment()
bootstrap_node = Node(env, 50)
nodes = [bootstrap_node]

def add_node(env, bootstrap_node, nodes):
    """Ajoute un nœud après interrogation des voisins."""
    yield env.timeout(random.randint(1, 5))
    new_node = Node(env, random.randint(1, 100))
    bootstrap_node.insert(new_node)
    nodes.append(new_node)

# Ajouter plusieurs nœuds
for _ in range(5):
    env.process(add_node(env, bootstrap_node, nodes))

# Exécuter la simulation
env.run(until=10)

# Affichage de l'anneau après l'ajout
temp_node = bootstrap_node
temp_node.display_ring()

# Suppression d'un nœud
if len(nodes) > 2:
    node_to_remove = nodes[2]
    next_node = node_to_remove.remove()
    if next_node:
        next_node.display_ring()