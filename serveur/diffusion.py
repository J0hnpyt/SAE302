import json
import threading

clients = []  # liste des sockets des clients connectés (partagée avec main.py)
verrouillage_clients = threading.Lock()  # protège l'accès à la liste clients entre les threads


def diffuser(message):
    """Envoie un message à tous les clients connectés, expéditeur compris.

    message : dictionnaire Python, ex. {"type": "MSG", "from": "Alice", "content": "salut"}
    """
    donnees = (json.dumps(message) + "\n").encode("utf-8")

    with verrouillage_clients:
        for c in clients[:]:
            try:
                c.sendall(donnees)
            except OSError:
                clients.remove(c)  # client déconnecté : on le retire
                c.close()

        if len(clients) == 0:
            print("Aucun client connecté.")


def deconnexion(client):
    """Retire un client qui se déconnecte et prévient les autres clients."""
    # Vérification ET retrait sous le même verrou : aucun autre thread ne peut passer entre les deux
    with verrouillage_clients:
        if client not in clients:
            return  # déjà retiré (par exemple par diffuser) : rien à faire
        clients.remove(client)

    # Le socket n'est pas encore fermé : on peut tenter de lire l'adresse
    try:
        adresse = client.getpeername()
    except OSError:
        adresse = "Un client"  # connexion déjà coupée

    client.close()

    # Hors du verrou : diffuser prend elle-même le verrou (sinon blocage)
    diffuser({"type": "INFO", "content": f"{adresse} s'est déconnecté."})