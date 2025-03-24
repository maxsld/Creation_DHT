import simpy
import random
import matplotlib.pyplot as plt
import numpy as np

class Node:
    def __init__(self, env, node_id):
        self.env = env
        self.node_id = node_id
        self.left = self  # Voisin gauche (initialement lui-même)
        self.right = self  # Voisin droit (initialement lui-même)
        self.env.process(self.listen())

    def listen(self):
        """ Simule l'écoute des messages entrants. """
        while True:
            yield self.env.timeout(random.uniform(1, 3))  # Attente aléatoire avant de recevoir le message

    def receive_join_request(self, sender_id, origin_node):
        """ Traite la demande d'ajout d'un nœud en transmettant le message. """
        print(f"{self.env.now:.2f} 📩 Nœud {self.node_id} reçoit une demande d'ajout de {sender_id}")

        # Si l'anneau est vide (le nœud est le seul), insérer immédiatement le nouveau nœud
        if self.right == self:
            self.insert_new_node(sender_id, origin_node)
        else:
            if self.should_insert(sender_id):
                self.insert_new_node(sender_id, origin_node)
            else:
                print(f"{self.env.now:.2f} ➡️ Nœud {self.node_id} transmet la requête à {self.right.node_id}")
                self.right.receive_join_request(sender_id, origin_node)

    def should_insert(self, new_node_id):
        """ Vérifie si le nœud actuel est celui qui doit insérer le nouveau nœud. """
        return (self.node_id < new_node_id < self.right.node_id or
                (self.node_id > self.right.node_id and (new_node_id > self.node_id or new_node_id < self.right.node_id)))
    
    def insert_new_node(self, new_node_id, origin_node):
        """ Insère le nouveau nœud dans l'anneau. """
        new_node = Node(self.env, new_node_id)
        new_node.left = self
        new_node.right = self.right
        self.right.left = new_node
        self.right = new_node
        print(f"{self.env.now:.2f} ✅ Nœud {new_node.node_id} inséré entre {self.node_id} et {new_node.right.node_id}")
        
        # Vérifier si le nouvel ID est le plus petit et doit devenir le premier
        if new_node.node_id < origin_node.node_id:
            return new_node
        return origin_node

    def display_ring(self):
        """ Affiche l'anneau DHT avec matplotlib sous forme de cercle. """
        nodes = []
        current = self
        while True:
            nodes.append(current)
            current = current.right
            if current == self:
                break
        
        # On calcule les positions angulaires pour chaque noeud
        n = len(nodes)
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)  # Angles également espacés
        radius = 1  # Rayon du cercle

        # Création de la figure
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_aspect('equal')  # Pour un cercle parfait
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)

        # Désactiver les axes et la grille
        ax.set_axis_off()

        # Tracer les nœuds comme des points plus gros et avec des couleurs aléatoires
        for i, node in enumerate(nodes):
            x = radius * np.cos(angles[i])
            y = radius * np.sin(angles[i])
            color = np.random.rand(3,)  # Couleur aléatoire pour chaque point
            ax.plot(x, y, 'o', markersize=15, color=color)  # Augmenter la taille du marqueur
            ax.text(x, y, f"{node.node_id}", fontsize=12, ha='center', va='center')

        # Afficher le cercle représentant l'anneau
        circle = plt.Circle((0, 0), radius, color='b', fill=False, linewidth=2)
        ax.add_artist(circle)

        plt.title("Structure de l'anneau DHT")
        plt.show()


def add_nodes(env, first_node):
    """ Fonction pour ajouter des nœuds progressivement après le lancement de la simulation. """
    node_ids = sorted(random.sample(range(1, 100), 20))  # Générer des noeuds aléatoires
    for node_id in node_ids:
        # Générer un délai aléatoire pour chaque nœud avant de l'ajouter
        delay = random.uniform(1, 2)
        yield env.timeout(delay)  # Ajout après un délai aléatoire
        print(f"{env.now:.2f} ➡️ Demande d'ajout de nœud {node_id} envoyée.")
        first_node.receive_join_request(node_id, first_node)

# Simulation
env = simpy.Environment()

# Le premier nœud a un identifiant aléatoire et est la racine de l'anneau.
first_node = Node(env, random.randint(1, 100))

# Planifier l'ajout des nœuds progressivement
env.process(add_nodes(env, first_node))

# Exécuter la simulation pendant 20 unités de temps
env.run(until=20)

# Afficher l'anneau avec matplotlib une fois que la simulation est terminée
first_node.display_ring()
