import simpy
import random

class Node:
    def __init__(self, env, identifier):
        self.env = env
        self.identifier = identifier
        self.left = self  # Initialement seul dans l'anneau
        self.right = self
        self.env.process(self.run())

    def __repr__(self):
        return f"Node({self.identifier})"
    
    def run(self):
        while True:
            yield self.env.timeout(1)  # Simulation d'une action périodique
    
    def insert(self, new_node):
        """Insère un nouveau nœud dans l'anneau en respectant l'ordre."""
        current = self

        # Cas particulier : si le nouvel identifiant est le plus petit ou le plus grand
        if new_node.identifier < current.identifier:
            while current.right != self and current.right.identifier > current.identifier:
                current = current.right

        # Parcours pour trouver la bonne position
        while current.right != self and current.right.identifier < new_node.identifier:
            current = current.right

        # Insertion du nouveau nœud
        new_node.right = current.right
        new_node.left = current
        current.right.left = new_node
        current.right = new_node
        print(f"[{self.env.now}] Nœud {new_node.identifier} ajouté entre {current.identifier} et {new_node.right.identifier}")
    
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
        """Affiche la structure de l'anneau en commençant par le plus petit identifiant."""
        # Trouver le nœud avec l'identifiant le plus petit
        current = self
        while current.right != self and current.right.identifier > current.identifier:
            current = current.right
        smallest = current.right if current.right.identifier < current.identifier else self

        # Parcourir et afficher l'anneau en commençant par le plus petit
        nodes = []
        current = smallest
        while True:
            nodes.append(str(current.identifier))
            current = current.right
            if current == smallest:
                break

        print("DHT Ring: " + " -> ".join(nodes))

# Simulation
env = simpy.Environment()
bootstrap_node = Node(env, 50)
nodes = [bootstrap_node]  # Liste pour suivre les nœuds

def add_node(env, bootstrap_node, nodes):
    """Ajoute un nœud aléatoire au réseau après un certain temps."""
    yield env.timeout(random.randint(1, 5))  # Chaque ajout a un délai aléatoire
    new_node = Node(env, random.randint(1, 100))
    bootstrap_node.insert(new_node)
    nodes.append(new_node)

# Ajouter plusieurs nœuds
for _ in range(5):
    env.process(add_node(env, bootstrap_node, nodes))

# Exécuter la simulation une seule fois sur une durée suffisante
env.run(until=10)

# Affichage après l'ajout des nœuds
bootstrap_node.display_ring()

# Supprimer un nœud spécifique
if len(nodes) > 2:
    node_to_remove = nodes[2]  # On choisit arbitrairement le 3e nœud ajouté
    next_node = node_to_remove.remove()

    # Affichage après suppression
    if next_node:
        next_node.display_ring()
