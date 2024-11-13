import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Allow multiple OpenMP instances
os.environ["OMP_NUM_THREADS"] = "1"

import threading
import queue
import time
import tkinter as tk
from os.path import join

import keyboard
import random
import pyautogui
from PIL import ImageTk
import easyocr
from openai import OpenAI
import yaml

  # Allow multiple OpenMP instances# Limit to one thread for OpenMP
from ocr_processing import get_clean_text_from_image, solve_operation, get_text_from_im_easy, get_text_from_im_gpt
from screen_capture import select_region, capture_screenshot

secret_path = 'secret.yaml'

with open(secret_path, 'r') as file:
    try:
        # Parse the YAML content
        keys = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        
OPENAI_KEY = keys['open_ai_key']
ZUKI_KEY = keys['zuki_key']




class MainApp:
    """
    Classe principale de l'application pour la capture d'écran et le traitement OCR.
    """

    def __init__(self, root, action_queue):
        """
        Initialise l'application principale.

        :param root: La fenêtre racine Tkinter.
        :param action_queue: Une queue pour recevoir les actions du listener clavier.
        """
        self.root = root
        self.action_queue = action_queue
        self.window = tk.Toplevel(root)
        self.div_mode = False
        self.region = tuple()
        self.ori_text = 'No text'
        self.clean_text = 'No text'
        self.result = int()
        self.image = None
        # Create an OCR reader object
        self.reader = easyocr.Reader(['en'])

        self.setup_gui()
        self.take_screenshot()
        self.check_queue()
        
        self.clients = {
            "open" : OpenAI(api_key = OPENAI_KEY),
            "zuki" : OpenAI(
                api_key=ZUKI_KEY,
                base_url="https://zukijourney.xyzbot.net/v1" # or "https://zukijourney.xyzbot.net/unf" 
            )
            }

    def setup_gui(self):
        """
        Configure les composants de l'interface graphique.
        """
        width, height, x, y = 1200, 400, 0, 45  # Largeur 1200, position (0, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Configuration de la grille
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Cadre principal
        self.main_frame = tk.Frame(self.window)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

        # Configuration de la grille dans le cadre principal
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Affichage de l'image
        self.image_label = tk.Label(self.main_frame)
        self.image_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        # Widget texte pour afficher les informations
        self.text_widget = tk.Text(self.main_frame, wrap=tk.WORD, height=5)
        self.text_widget.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

    def on_close(self):
        """
        Gère l'événement de fermeture de la fenêtre.
        """
        self.root.destroy()

    def display_image(self, image):
        """
        Affiche l'image donnée dans l'interface graphique.

        :param image: Objet PIL Image à afficher.
        """
        max_width = 1180  # Pour laisser un peu de marge avec les bordures
        max_height = 200
        image.thumbnail((max_width, max_height))
        self.image = image
        tk_image = ImageTk.PhotoImage(image)
        self.image_label.config(image=tk_image)
        self.image_label.image = tk_image  # Maintenir une référence pour éviter le garbage collection

    def display_text(self, text):
        """
        Affiche le texte donné dans le widget texte de l'interface graphique.

        :param text: Texte à afficher.
        """
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, text)
        self.text_widget.config(state=tk.DISABLED)

    def get_region(self, div_mode=False):
        """
        Permet à l'utilisateur de sélectionner une région sur l'écran.
        """
        self.region = select_region(self.root)
        self.take_screenshot(div_mode, model='gpt')

    def take_screenshot(self, div_mode=False, model='tessseract'):
        """
        Capture une capture d'écran de la région sélectionnée, effectue l'OCR et met à jour l'interface graphique.
        """
        if self.region:
            image = capture_screenshot(self.region)
            self.display_image(image)

            if model == 'easy':
                text, self.ori_text = get_text_from_im_easy(image, self.reader)
            elif model == 'gpt':
                text, self.ori_text = get_text_from_im_gpt(image, self.clients['open'])
            else:
                text, self.ori_text = get_clean_text_from_image(image, self.reader)
                
            if div_mode:
                text = text.replace('+', '/')
            self.clean_text = text

            error, result = solve_operation(self.clean_text)
            self.display_result(error, result)

        else:
            self.display_text('Aucune région sélectionnée.')
    
    def display_result(self, error, result):
        if error is None:
            self.result = result
            display_text = (f'Expression originale: {self.ori_text}\n'
                            f'Expression nettoyée: {self.clean_text}\n'
                            f'Résultat: {self.result}\n')
            self.display_text(display_text)
            self.input_result()
        else:
            display_text = (f'Expression originale: {self.ori_text}\n'
                            f'Erreur: {error}\n')
            self.display_text(display_text)
        
            
    def type_with_random_delay(self, word):
        """
        Types a word with random delays between each keystroke.

        Parameters:
        word (str): The word to type out.
        """
        for char in word:
            pyautogui.press(char)
            time.sleep(random.uniform(0.02, 0.05))
            

    def input_result(self):
        """
        Simule la saisie du résultat en utilisant pyautogui.
        """
        pyautogui.press('backspace', presses=10)
        self.type_with_random_delay(str(int(self.result)))

    def reset_result(self):
        """
        Simule l'appui sur la touche backspace pour réinitialiser le résultat.
        """
        for _ in range(10):
            pyautogui.press('backspace')
            

    def save_error(self):
        """
        Enregistre l'image actuelle dans le dossier des erreurs avec un nom de fichier horodaté.
        """
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        folder = 'error'
        filename = f"screenshot_{timestamp}.png"
        if self.image:
            self.image.save(join(folder, filename))
        else:
            print("Aucune image à enregistrer.")

    def check_queue(self):
        """
        Vérifie la queue des actions et exécute les méthodes correspondantes.
        """
        try:
            action = self.action_queue.get_nowait()
            if action == "get_region":
                self.get_region()
            elif action == "classic":
                self.take_screenshot(div_mode=False, model="tesseract")
            elif action == "division":
                self.take_screenshot(div_mode=True, model="tesseract")
            elif action == "easy":
                self.take_screenshot(div_mode=False, model="gpt")
            elif action == "easy_division":
                self.take_screenshot(div_mode=True, model="gpt")
            elif action == "save_error":
                self.save_error()
            elif action == "on_close":
                self.on_close()
        except queue.Empty:
            pass
        finally:
            # Continue de vérifier la queue toutes les 100 ms
            self.window.after(100, self.check_queue)


def keyboard_listener(action_queue):
    """
    Configure les raccourcis clavier pour mettre les actions dans la queue.

    :param action_queue: La queue pour mettre les actions.
    """
    keyboard.add_hotkey('f1', lambda: action_queue.put("get_region"), suppress=True)
    keyboard.add_hotkey('f2', lambda: action_queue.put("classic"), suppress=True)
    keyboard.add_hotkey('f3', lambda: action_queue.put("division"), suppress=True)
    keyboard.add_hotkey('f4', lambda: action_queue.put("easy"), suppress=True)
    #keyboard.add_hotkey('f5', lambda: action_queue.put("easy_division"), suppress=True)
    keyboard.add_hotkey('f10', lambda: action_queue.put("save_error"), suppress=True)


if __name__ == "__main__":
    # Crée la queue des actions
    action_queue = queue.Queue()

    # Configure la fenêtre racine Tkinter
    root = tk.Tk()
    root.withdraw()  # Masque la fenêtre racine

    # Initialise l'application principale
    app = MainApp(root, action_queue)

    # Démarre le listener clavier dans un thread séparé
    keyboard_thread = threading.Thread(target=keyboard_listener, args=(action_queue,))
    keyboard_thread.daemon = True
    keyboard_thread.start()

    # Démarre la boucle d'événements Tkinter
    root.mainloop()
    print('Application arrêtée')
