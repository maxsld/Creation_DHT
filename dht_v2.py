import simpy
import random
import matplotlib.pyplot as plt
import numpy as np

# -------------------------------
# Classes de base
# -------------------------------

class Data:
    def __init__(self, key, content):
        self.key = key
        self.content = content

class Message:
    def __init__(self, sender, receiver, content):
        self.sender = sender
        self.receiver = receiver
        self.content = content

# -------------------------------
# Classe Node
# -------------------------------

class Node:
    def __init__(self, env, node_id):
        self.env = env
        self.node_id = node_id
        self.left = self  # Voisin gauche (initialement lui-même)
        self.right = self  # Voisin droit (initialement lui-même)
        self.data_store = []
        self.env.process(self.listen())

    def listen(self):
        """ Simule l'écoute des messages entrants. """
        while True:
            yield self.env.timeout(random.uniform(1, 3))  # Attente aléatoire avant de recevoir le message
    
    def store_data(self, data):
        """ Stocke ou transfère la donnée jusqu'au bon nœud """
        print(f"{self.env.now:.2f} 📦 Nœud {self.node_id} reçoit la demande de stockage de la clé {data.key}")

        if self.is_responsible_for(data.key):
            self.data_store.append(data)
            self.left.data_store.append(data)
            self.right.data_store.append(data)
            print(f"{self.env.now:.2f} ✅ Nœud {self.node_id} stocke la clé {data.key} : {data.content}")
            print(f"{self.left.env.now:.2f} ✅ Nœud {self.left.node_id} stocke la clé {data.key} : {data.content}")
            print(f"{self.right.env.now:.2f} ✅ Nœud {self.right.node_id} stocke la clé {data.key} : {data.content}")
        else:
            print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transfère la clé {data.key} à {self.right.node_id}")
            yield self.env.timeout(random.uniform(1, 2))  # Simule le délai de transfert
            self.env.process(self.right.store_data(data))
    
    def retrieve_data(self, key):
        """ Récupère ou transfère la demande de récupération de donnée jusqu'au bon nœud. """
        print(f"{self.env.now:.2f} 🔍 Nœud {self.node_id} cherche la donnée avec la clé {key}")

        # Vérifier si la donnée est dans le nœud actuel
        for data in self.data_store:
            if data.key == key:
                print(f"{self.env.now:.2f} ✅ Nœud {self.node_id} a trouvé la donnée avec la clé {key}: {data.content}")
                return data.content  # Retourne le contenu de la donnée

        # Si la donnée n'est pas ici, la transmettre au voisin droit
        print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transmet la demande de récupération à {self.right.node_id}")
        yield self.env.timeout(random.uniform(1, 2))  # Délai de transfert de la demande
        self.env.process(self.right.retrieve_data(key))  # Recherche de la donnée sur le voisin droit

    def is_responsible_for(self, key):
        """ Détermine si ce nœud est responsable du stockage de la clé en prenant en compte la distance circulaire absolue. """
        if self.node_id <= key <= self.right.node_id:
            # Calcul de la distance absolue entre ce nœud et la clé
            dist_self = min(abs(key - self.node_id), 100 - abs(key - self.node_id))
            # Calcul de la distance absolue entre le voisin droit et la clé
            dist_right = min(abs(key - self.right.node_id), 100 - abs(key - self.right.node_id))
            # Ce nœud est responsable si la clé est plus proche de lui que de son voisin droit
            return dist_self < dist_right
        elif self.left.node_id <= key <= self.node_id:
            # Calcul de la distance absolue entre ce nœud et la clé
            dist_self = min(abs(key - self.node_id), 100 - abs(key - self.node_id))
            # Calcul de la distance absolue entre le voisin gauche et la clé
            dist_left = min(abs(key - self.left.node_id), 100 - abs(key - self.left.node_id))
            # Ce nœud est responsable si la clé est plus proche de lui que de son voisin gauche
            return dist_self < dist_left
        elif self.node_id > self.right.node_id:
            # Calcul de la distance absolue entre ce nœud et la clé
            dist_self = min(abs(key - self.node_id), 100 - abs(key - self.node_id))
            # Calcul de la distance absolue entre le voisin droit et la clé
            dist_right = min(abs(key - self.right.node_id), 100 - abs(key - self.right.node_id))
            # Ce nœud est responsable si la clé est plus proche de lui que de son voisin droit
            return dist_self < dist_right

    def receive_message(self, message):
        """ Traite la réception d'un message et le transmet si nécessaire. """
        print(f"{self.env.now:.2f} 📩 Nœud {self.node_id} reçoit le message de {message.sender} : {message.content}")

        # Si le message est destiné à ce nœud, on l'affiche, sinon on le transmet.
        if self.node_id == message.receiver:
            print(f"{self.env.now:.2f} ✅ Nœud {self.node_id} a reçu le message.")
        else:
            # Le message n'est pas pour ce nœud, donc le transmettre.
            print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transmet le message à {self.right.node_id}")
            yield self.env.timeout(random.uniform(1, 2))  # Délai de transmission du message
            self.right.receive_message(message)  # Transfert du message à son voisin droit

    def send_message(self, sender, receiver, content):
        """ Envoie un message à un autre nœud du réseau, et chaque nœud le transmet. """
        print(f"{self.env.now:.2f} ➡️ Nœud {sender.node_id} veut envoyer un message à {receiver.node_id} : {content}")
        message = Message(sender=sender.node_id, receiver=receiver.node_id, content=content)
        # Commencer à transférer le message à partir du nœud sender
        self.env.process(self.transfer_message(sender, message))

    def transfer_message(self, sender, message):
        """ Transfert le message à travers les nœuds de l'anneau. """
        current_node = sender
        while current_node.node_id != message.receiver:
            print(f"{self.env.now:.2f} ➡️ Nœud {current_node.node_id} transmet le message à {current_node.right.node_id}")
            yield self.env.timeout(random.uniform(1, 2))  # Temps de transfert
            current_node = current_node.right  # Transfert au voisin droit
        # Lorsque le message atteint le destinataire, le récepteur prend en charge.
        current_node.receive_message(message)
        # Ajouter un message final lorsque le récepteur reçoit le message
        print(f"{self.env.now:.2f} ✅ Nœud {current_node.node_id} a reçu le message de {message.sender} : {message.content}")

    def receive_join_request(self, message):
        """ Traite la demande d'ajout d'un nœud en transmettant le message. """
        print(f"{self.env.now:.2f} 📩 Nœud {self.node_id} reçoit une demande d'ajout de {message.sender}")

        # Si l'anneau est vide (le nœud est le seul), insérer immédiatement le nouveau nœud
        if self.right == self:
            self.insert_new_node(message.sender)
        else:
            if self.should_insert(message.sender):
                self.insert_new_node(message.sender)
            else:
                print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transmet la requête à {self.right.node_id}")
                self.right.receive_join_request(message)

    def should_insert(self, new_node_id):
        """ Vérifie si le nœud actuel est celui qui doit insérer le nouveau nœud. """
        return (self.node_id < new_node_id < self.right.node_id or
                (self.node_id > self.right.node_id and (new_node_id > self.node_id or new_node_id < self.right.node_id)))

    def insert_new_node(self, new_node_id):
        """ Insère le nouveau nœud dans l'anneau. """
        new_node = Node(self.env, new_node_id)
        new_node.left = self
        new_node.right = self.right
        self.right.left = new_node
        self.right = new_node
        print(f"{self.env.now:.2f} ✅ Nœud {new_node.node_id} inséré entre {self.node_id} et {new_node.right.node_id}")

    def remove_node(self, node_to_remove):
        """ Permet de retirer un nœud de l'anneau. """
        yield self.env.timeout(random.uniform(1, 2))  # Délai aléatoire pour simuler l'attente de traitement

        print(f"{self.env.now:.2f} ❌ Nœud {self.node_id} retire le nœud {node_to_remove.node_id}")

        # Si le nœud à retirer est celui-ci, on le supprime en ajustant les voisins
        if self == node_to_remove:
            self.left.right = self.right
            self.right.left = self.left
            print(f"{self.env.now:.2f} ✅ Nœud {self.node_id} supprimé de l'anneau.")
        else:
            # Si ce n'est pas le nœud actuel, on transmet la demande à son voisin droit
            print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transmet la demande de suppression à {self.right.node_id}")
            yield from self.right.remove_node(node_to_remove)  # Appel récursif avec `yield from`

    def display_ring(self):
        """ Affiche l'anneau DHT avec les données stockées sous chaque nœud """
        nodes = []
        current = first_node
        while True:
            nodes.append(current)
            current = current.right
            if current == first_node:
                break

        n = len(nodes)
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        radius = 1

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect('equal')
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_axis_off()

        for i, node in enumerate(nodes):
            x = radius * np.cos(angles[i])
            y = radius * np.sin(angles[i])
            
            # Dessiner le noeud
            ax.plot(x, y, 'o', markersize=15, color="lightblue", markeredgecolor='black')

            # Afficher l'ID du nœud
            ax.text(x, y, f"{node.node_id}", fontsize=12, ha='center', va='center', fontweight='bold')

            # Afficher les données stockées sous chaque nœud
            if node.data_store:
                data_text = "\n".join([str(data.key) for data in node.data_store])

                # Ajuster la position pour éviter le chevauchement
                offset_x, offset_y = 0.1 * np.cos(angles[i]), 0.1 * np.sin(angles[i])
                
                # Ajouter un rectangle blanc derrière le texte
                ax.text(
                    x + offset_x, y + offset_y - 0.2, data_text,
                    fontsize=10, ha='center', va='top', color='black',
                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3')
                )

        # Dessiner l'anneau
        circle = plt.Circle((0, 0), radius, color='b', fill=False, linewidth=2)
        ax.add_artist(circle)
        
        plt.title("Structure de l'anneau DHT avec données", fontsize=14, fontweight='bold')
        plt.show()

# -------------------------------
# Fonctions de simulation
# -------------------------------

def add_nodes(env, first_node):
    """ Fonction pour ajouter des nœuds progressivement après le lancement de la simulation. """
    node_ids = sorted(random.sample(range(1, 100), 20))  # Générer des noeuds aléatoires
    for node_id in node_ids:
        # Générer un délai aléatoire pour chaque nœud avant de l'ajouter
        delay = random.uniform(1, 2)
        yield env.timeout(delay)  # Ajout après un délai aléatoire
        print(f"{env.now:.2f} ➡️ Demande d'ajout de nœud {node_id} envoyée.")
        message = Message(sender=node_id, receiver=first_node.node_id, content="Join Request")
        first_node.receive_join_request(message)

def send_sample_messages(env, first_node, first_node_receiver):
    """ Envoie des messages à travers l'anneau après un certain délai. """
    yield env.timeout(10)  # Attendre un certain temps avant d'envoyer le message
    first_node.send_message(first_node, first_node_receiver, content="Bonjour 1")  # Exemple d'envoi

# -------------------------------
# Simulation
# -------------------------------

env = simpy.Environment()

# Le premier nœud a un identifiant aléatoire et est la racine de l'anneau.
first_node = Node(env, 50)

# Planifier l'ajout des nœuds progressivement
env.process(add_nodes(env, first_node))

# Exécuter la simulation pendant 20 unités de temps
env.run(until=100)

# Afficher l'anneau avec matplotlib une fois que la simulation est terminée
first_node.display_ring()

# Exemple de suppression d'un nœud après un délai
node_to_remove = first_node.right  # Exemple, retirer le deuxième nœud
env.process(first_node.remove_node(node_to_remove))

# Exécuter la simulation après la suppression
env.run(until=150)

# Planifier l'envoi de messages
first_node_receiver = first_node.right.right.right.right.right.right  # Receveur du message
env.process(send_sample_messages(env, first_node, first_node_receiver))

env.run(until=200)

# Stocker des données
env.process(first_node.store_data(Data(7, "Donnée :D")))
env.process(first_node.store_data(Data(25, "Donnée 2 :D")))
env.process(first_node.store_data(Data(79, "Donnée 3 :D")))

env.run(until=250)

# Récupérer des données
env.process(first_node.retrieve_data(7))

env.run(until=300)

# Afficher l'anneau mis à jour
first_node.display_ring()