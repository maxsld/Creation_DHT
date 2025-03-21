import simpy
import random
from node import Node

# Simulation
env = simpy.Environment()
nodes = []

# Ajout initial de nœuds
def add_initial_nodes(env, nodes):
    for _ in range(10):
        yield env.process(add_node(env, nodes))

def add_node(env, nodes):
    yield env.timeout(random.randint(1, 5))
    while True:
        new_id = random.randint(1, 100)
        if new_id not in Node.existing_ids:
            break
    new_node = Node(env, new_id)
    if nodes:
        random_node = random.choice(nodes)
        print(f"[{env.now}] Nouveau nœud {new_node.identifier} tente de rejoindre l'anneau.")
        new_node.send_join_message(random_node)
    nodes.append(new_node)
    nodes.sort(key=lambda node: node.identifier)

def remove_node(env, nodes):
    yield env.timeout(1)  # Attendre un peu avant de supprimer un nœud
    if nodes:
        index = random.randint(0, len(nodes) - 1)
        node_to_remove = nodes[index]
        next_node = node_to_remove.remove()
        nodes.remove(node_to_remove)
        if next_node:
            next_node.display_ring()

def send_message(env, nodes):
    yield env.timeout(1)  # Attendre un peu avant d'envoyer un message
    if nodes:
        sender = nodes[0]
        receiver = nodes[-1].identifier
        sender.send(receiver, "Hello, this is a test message!")

def store_data(env, nodes):
    yield env.timeout(1)  # Attendre un peu avant de stocker des données
    if nodes:
        key = random.randint(1, 100)
        value = f"Value for {key}"
        responsible_node = nodes[0].find_responsible_node(key)
        responsible_node.store_data(key, value)

def get_data(env, nodes):
    yield env.timeout(1)  # Attendre un peu avant de récupérer des données
    if nodes:
        requester = nodes[0]
        key = random.randint(1, 100)  # Choisir une clé aléatoire
        requester.request_data(key)

# Fonction principale pour orchestrer les opérations
def main(env):
    yield env.process(add_initial_nodes(env, nodes))
    yield env.process(remove_node(env, nodes))
    yield env.process(send_message(env, nodes))
    print("")
    yield env.process(store_data(env, nodes))
    yield env.process(store_data(env, nodes))
    yield env.process(store_data(env, nodes))
    print("")
    yield env.process(get_data(env, nodes))  # Ajout de la récupération de données
    nodes[0].draw_ring()  # Dessiner l'anneau après les opérations

# Exécuter la simulation
env.process(main(env))
env.run(until=100)
