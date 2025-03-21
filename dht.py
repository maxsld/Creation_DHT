import simpy
import random

class Message:
    def __init__(self, sender, receiver, content):
        self.sender = sender
        self.receiver = receiver
        self.content = content

class Donnees:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"Données({self.key}: {self.value})"

class Node:
    existing_ids = set()

    def __init__(self, env, identifier):
        if identifier in Node.existing_ids:
            raise ValueError(f"Nœud avec l'identifiant {identifier} existe déjà!")
        Node.existing_ids.add(identifier)

        self.env = env
        self.identifier = identifier
        self.left = self
        self.right = self
        self.data_store = []

        self.env.process(self.run())

    def __repr__(self):
        return f"Node({self.identifier})"

    def run(self):
        while True:
            yield self.env.timeout(1)

    def send_join_message(self, recipient):
        message = Message(self, recipient, "nouveau nœud")
        print(f"[{self.env.now}] {self.identifier} envoie le message '{message.content}' à {recipient.identifier}")
        recipient.received_join_message(message)

    def received_join_message(self, message):
        print(f"[{self.env.now}] {self.identifier} a reçu le message '{message.content}' de {message.sender.identifier}")
        if message.content == "nouveau nœud":
            self.insert_node(message.sender)

    def insert_node(self, new_node):
        print(f"[{self.env.now}] Le nœud {self.identifier} reçoit le message 'nouveau nœud' et va l'insérer.")
        if self.right == self:
            self.left = new_node
            self.right = new_node
            new_node.left = self
            new_node.right = self
        else:
            position = self.find_position(new_node)
            new_node.left = position
            new_node.right = position.right
            position.right.left = new_node
            position.right = new_node
        self.display_ring()

    def find_position(self, new_node):
        current = self
        while not (current.identifier < new_node.identifier <= current.right.identifier or
                   (current.right.identifier < current.identifier and
                    (new_node.identifier > current.identifier or new_node.identifier < current.right.identifier))):
            current = current.right
            if current == self:
                break
        return current

    def remove(self):
        if self.left == self and self.right == self:
            print(f"[{self.env.now}] Dernier nœud {self.identifier} supprimé, l'anneau est vide.")
            Node.existing_ids.remove(self.identifier)
            return None

        self.left.right = self.right
        self.right.left = self.left
        print(f"[{self.env.now}] Nœud {self.identifier} supprimé, {self.left.identifier} et {self.right.identifier} sont maintenant connectés.")
        Node.existing_ids.remove(self.identifier)
        return self.right

    def display_ring(self):
        current = self
        min_node = self
        while True:
            if current.identifier < min_node.identifier:
                min_node = current
            current = current.right
            if current == self:
                break

        current = min_node
        nodes = []
        while True:
            nodes.append(f"[{current.identifier}]")
            current = current.right
            if current == min_node:
                break
        print("")
        print("--->".join(nodes))
        print("")

    def send(self, target_id, content):
        message = Message(self, target_id, content)
        print(f"[{self.env.now}] {self.identifier} envoie '{content}' à {target_id}")
        self.forward(message)

    def forward(self, message):
        current = self.right
        while current != self:
            if current.identifier == message.receiver:
                current.deliver(message)
                return
            print(f"[{self.env.now}] {current.identifier} forward le message '{message.content}'")
            current = current.right
        print(f"[{self.env.now}] Message pour {message.receiver} introuvable dans l'anneau!")

    def deliver(self, message):
        print(f"[{self.env.now}] {self.identifier} a reçu le message: '{message.content}' de {message.sender.identifier}")

    def store_data(self, key, value):
        data = Donnees(key, value)
        responsible_node = self.find_responsible_node(key)
        responsible_node.data_store.append(data)
        print(f"[{self.env.now}] {responsible_node.identifier} stocke {data}.")

        # Stocker sur les voisins immédiats (degré de réplication == 3)
        responsible_node.left.data_store.append(data)
        responsible_node.right.data_store.append(data)
        print(f"[{self.env.now}] {responsible_node.left.identifier} et {responsible_node.right.identifier} stockent également {data}.")

    def find_responsible_node(self, key):
        current = self
        closest_node = current  # Initialisation du nœud le plus proche avec le nœud de départ
        min_distance = abs(current.identifier - key)  # Distance initiale (directe)
        
        while True:
            # Calcul de la distance directe entre le nœud actuel et la clé
            direct_distance = abs(current.identifier - key)

            # Si le nœud actuel est plus proche que le précédent, on met à jour
            if direct_distance < min_distance:
                closest_node = current
                min_distance = direct_distance

            # On passe au nœud suivant
            current = current.right
            
            # Si on a parcouru tout l'anneau (on revient au nœud de départ)
            if current == self:
                break

        return closest_node



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

# Fonction principale pour orchestrer les opérations
def main(env):
    yield env.process(add_initial_nodes(env, nodes))
    yield env.process(remove_node(env, nodes))
    yield env.process(send_message(env, nodes))
    print("")
    yield env.process(store_data(env, nodes))

# Exécuter la simulation
env.process(main(env))
env.run(until=100)