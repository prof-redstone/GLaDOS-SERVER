import signal
import socket
import threading
import time
import subprocess
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Variable pour indiquer si le serveur doit continuer à fonctionner
running = True

def generateResponse(inputText="Hello"):
    subprocess.Popen(["ollama", "start"])
    # Local Llama3 
    llm = ChatOllama(
        model="llama3",
        keep_alive=-1,  # keep the model loaded indefinitely
        temperature=1.0,
        max_new_tokens=512)

    prompt = ChatPromptTemplate.from_template(
        "Now you are Glados the voice assistant from the game Portal, you will respond like her to the text that I am going to give you. Do not add anything except the voice text, avoid question mark, exclamation mark, dash, or quote. But you must use a lot of comma and point to give rhythm to the sentence. Your response should not exceed a maximum 30 words. Chell voice text : {textInput}")

    chain = prompt | llm | StrOutputParser()

    response = ""
    for chunk in chain.stream({"textInput": inputText}):
        print(chunk, end="", flush=True)
        response = response + chunk

    return response #return response[1:-1]  # retirer " au début et la fin

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Reçu : {request}")
        
        response = generateResponse(request)
        client_socket.send(response.encode('utf-8'))
    finally:
        client_socket.close()

def start_server():
    global running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Serveur en attente de connexions...")

    while running:
        try:
            server.settimeout(1)
            client_socket, addr = server.accept()
            print(f"Connexion acceptée de {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Erreur: {e}")
            break

    server.close()
    print("Serveur arrêté.")

def signal_handler(sig, frame):
    global running
    print("Interruption reçue, arrêt du serveur...")
    running = False

if __name__ == "__main__":
    # Associer la fonction de gestion du signal SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    start_server()
