# screen_capture.py

import pyautogui
import time
import tkinter as tk

def select_region(main_root):
    root = tk.Toplevel(main_root)
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.1)
    root.config(bg='gray')
    root.attributes("-topmost", True)

    start_x = start_y = end_x = end_y = 0

    # Canvas pour dessiner le rectangle blanc
    canvas = tk.Canvas(root, bg='gray', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Variable pour le rectangle
    rect_id = None

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x_root, event.y_root
        # Crée un rectangle blanc transparent initialement
        rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='white', fill='white', stipple='gray12')

    def on_mouse_move(event):
        nonlocal rect_id
        # Met à jour le rectangle en temps réel en ajustant les coins
        if rect_id:
            canvas.coords(rect_id, start_x, start_y, event.x_root, event.y_root)

    def on_mouse_up(event):
        nonlocal end_x, end_y
        end_x, end_y = event.x_root, event.y_root
        root.quit()

    # Liaisons des événements
    root.bind('<Button-1>', on_mouse_down)
    root.bind('<B1-Motion>', on_mouse_move)
    root.bind('<ButtonRelease-1>', on_mouse_up)
    root.bind('<Escape>', lambda e: root.destroy())

    root.mainloop()
    root.destroy()

    # Calcul et retour des coordonnées et dimensions
    x = min(start_x, end_x)
    y = min(start_y, end_y)
    width = abs(end_x - start_x)
    height = abs(end_y - start_y)

    return x, y, width, height


def capture_screenshot(region, save_image=False):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    image = pyautogui.screenshot(region=region)
    if save_image:
        image.save(filename)  # Enregistre l'image pour référence
    return image
