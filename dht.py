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
        self.neighbors = []  # Liste pour stocker les voisins avec lesquels échanger des messages

        self.env.process(self.run())

    def __repr__(self):
        return f"Node({self.identifier})"

    def run(self):
        while True:
            yield self.env.timeout(1)  # Le nœud est en pause dans l'anneau

    def send_message(self, recipient, message):
        print(f"[{self.env.now}] {self.identifier} envoie le message '{message}' à {recipient.identifier}")
        recipient.receive_message(self, message)

    def receive_message(self, sender, message):
        print(f"[{self.env.now}] {self.identifier} a reçu le message '{message}' de {sender.identifier}")
        if message == "nouveau nœud":
            self.insert_new_node(sender)

    def insert_new_node(self, new_node):
        print(f"[{self.env.now}] Le nœud {self.identifier} reçoit le message 'nouveau nœud' et va l'insérer.")
        position = self.find_position(new_node)
        self.send_message(position, "nouveau nœud - insérer")
        position.insert(new_node)

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

    def connect_neighbors(self, left_neighbor, right_neighbor):
        self.left = left_neighbor
        self.right = right_neighbor
        left_neighbor.right = self
        right_neighbor.left = self
        print(f"[{self.env.now}] Nœud {self.identifier} connecté entre {left_neighbor.identifier} et {right_neighbor.identifier}")

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
        # Choisir un nœud au hasard dans la liste existante pour que le nouveau nœud contacte
        random_node = random.choice(nodes)
        print(f"[{env.now}] Nouveau nœud {new_node.identifier} tente de rejoindre l'anneau.")
        # Le nouveau nœud envoie un message pour rejoindre l'anneau
        new_node.send_message(random_node, "nouveau nœud")
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

def connect_neighbors_after_removal(env, nodes, index):
    yield env.timeout(random.randint(1, 5))
    if len(nodes) > index:
        node_to_remove = nodes[index]
        if node_to_remove.left != node_to_remove and node_to_remove.right != node_to_remove:
            left_neighbor = node_to_remove.left
            right_neighbor = node_to_remove.right
            node_to_remove.connect_neighbors(left_neighbor, right_neighbor)

# Initialisation
for _ in range(2):
    env.process(add_node(env, nodes))

env.run(until=10)

if nodes:
    nodes[0].display_ring()
    env.process(add_node(env, nodes))

env.run(until=15)


env.run(until=20)
