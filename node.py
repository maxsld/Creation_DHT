import random
import numpy as np
import matplotlib.pyplot as plt
from message import Message
from data import Donnees
import simpy

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

    def request_data(self, key):
        print(f"[{self.env.now}] {self.identifier} demande la donnée pour la clé {key}.")
        self.forward_data_request(key)

    def forward_data_request(self, key):
        current = self.right
        while current != self:
            if current.has_data(key):
                current.deliver_data(key)
                return
            print(f"[{self.env.now}] {current.identifier} forward la demande de donnée pour la clé {key}.")
            current = current.right
        print(f"[{self.env.now}] Donnée pour la clé {key} introuvable dans l'anneau!")

    def has_data(self, key):
        return any(data.key == key for data in self.data_store)

    def deliver_data(self, key):
        for data in self.data_store:
            if data.key == key:
                print(f"[{self.env.now}] {self.identifier} a trouvé la donnée pour la clé {key}: {data.value}.")
                return data.value
        print(f"[{self.env.now}] {self.identifier} n'a pas trouvé la donnée pour la clé {key}.")

    def draw_ring(self):
        # Récupérer tous les nœuds dans l'anneau
        nodes = []
        current = self
        while True:
            nodes.append(current)
            current = current.right
            if current == self:
                break

        # Calculer les positions des nœuds sur un cercle
        num_nodes = len(nodes)
        angles = np.linspace(0, 2 * np.pi, num_nodes, endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # Fermer le cercle
        radius = 1

        # Positions des nœuds
        x = radius * np.cos(angles)
        y = radius * np.sin(angles)

        # Créer le graphique
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, 'o-', markersize=10)  # Nœuds
        plt.xlim(-1.5, 1.5)
        plt.ylim(-1.5, 1.5)
        plt.gca().set_aspect('equal', adjustable='box')

        # Modifier l'apparence de la figure (fond blanc sans lignes noires)
        plt.gca().set_facecolor('white')
        plt.grid(False)  # Désactiver la grille
        plt.axis('off')

        # Annoter les nœuds
        for i, node in enumerate(nodes):
            plt.annotate(f"{node.identifier}", (x[i], y[i]), textcoords="offset points", xytext=(0,10), ha='center')

        plt.title("Anneau des Nœuds")
        plt.show()
