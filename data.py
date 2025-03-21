class Donnees:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"Données({self.key}: {self.value})"
