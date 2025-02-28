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
    
    def send_message(self, target_id, message):
        self.env.process(self.forward_message(target_id, message))
        yield self.env.timeout(0)
    
    def forward_message(self, target_id, message):
        current = self
        clockwise_distance = (target_id - current.identifier) % 100
        counterclockwise_distance = (current.identifier - target_id) % 100
        direction = "right" if clockwise_distance <= counterclockwise_distance else "left"
        
        while current.identifier != target_id:
            print(f"[{self.env.now}] Message transféré par {current.identifier}")
            current = current.right if direction == "right" else current.left
            yield self.env.timeout(1)  # Simulation du délai de transmission
        
        print(f"[{self.env.now}] Message reçu par {current.identifier}: {message}")

class DHT:
    def __init__(self, env):
        self.env = env
        self.nodes = []
    
    def insert(self, identifier):
        new_node = Node(self.env, identifier)
        print(f"[{self.env.now}] Nœud {identifier} ajouté")
        if not self.nodes:
            self.nodes.append(new_node)
        else:
            for i, node in enumerate(self.nodes):
                if identifier < node.identifier:
                    self.nodes.insert(i, new_node)
                    break
            else:
                self.nodes.append(new_node)
            
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
            print(f"Nœud {identifier} supprimé")
    
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

# Simulation
env = simpy.Environment()
dht = DHT(env)

# Processus pour ajouter des nœuds dynamiquement
def add_nodes(env, dht, count):
    for _ in range(count):
        dht.insert(random.randint(1, 100))
        yield env.timeout(2)  # Attente entre chaque insertion

env.process(add_nodes(env, dht, 2))
env.run(until=10)

dht.display_ring()

# Exécution de la simulation
env.process(dht.nodes[0].send_message(dht.nodes[1].identifier, "Hello, Word!"))
env.run(20)

env.process(add_nodes(env, dht, 1))
env.run(until=30)

dht.display_ring()
