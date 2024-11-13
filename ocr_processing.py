# ocr_processing.py

import pytesseract
import re
import ast
import cv2
from constants import allowed_operators
import numpy as np
import base64
import io


def safe_eval(node):
    if isinstance(node, ast.Num):  # Nombre
        return node.n
    elif isinstance(node, ast.BinOp):  # Opération binaire
        op_type = type(node.op)
        if op_type in allowed_operators:
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            # Gérer la division par zéro
            if op_type == ast.Div and right == 0:
                raise ZeroDivisionError("Division par zéro")
            return allowed_operators[op_type](left, right)
        else:
            raise ValueError(f"Opérateur non supporté: {op_type}")
    elif isinstance(node, ast.UnaryOp):  # Opération unaire (ex : négation)
        op_type = type(node.op)
        if op_type in allowed_operators:
            operand = safe_eval(node.operand)
            return allowed_operators[op_type](operand)
        else:
            raise ValueError(f"Opérateur unaire non supporté: {op_type}")
    else:
        raise ValueError(f"Expression non supportée: {node}")


def image_processing(image):
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    return thresh

    

def get_clean_text_from_image(image, div_mode=False):
    
    
    processed_image = image_processing(image)
    ori_text = pytesseract.image_to_string(processed_image)

    # Nettoyer le texte pour ne conserver que les caractères valides
    text = ori_text.replace(' ', '')  # Supprimer les espaces
    text = text.replace('—', '-')
    text = text.replace('/1', '7')
    text = text.replace('÷', '/')  # Remplacer le symbole de division
    text = text.replace('x', '*')  # Remplacer le symbole de multiplication en minuscule
    text = text.replace('X', '*')  # Remplacer le symbole de multiplication en majuscule
    text = text.replace(',', '.')  # Remplacer la virgule par un point pour les décimales
    # Supprimer tous les caractères non autorisés
    text = re.sub(r'[^0-9\.\+\-\*/\(\)]', '', text)
    
    if div_mode:
        text.replace('+','/')
    
    return text, ori_text


def get_text_from_im_easy(image, reader):
    
    image_np = np.array(image)
    results = reader.readtext(image_np)
    ori_text = "".join([result for _, result, _ in results])
    
    text = ori_text.replace(' ', '')  # Supprimer les espaces
    text = text.replace('—', '-')
    text = text.replace('÷', '/')  # Remplacer le symbole de division
    text = text.replace('x', '*')  # Remplacer le symbole de multiplication en minuscule
    text = text.replace('X', '*')  # Remplacer le symbole de multiplication en majuscule
    text = text.replace(',', '.')  # Remplacer la virgule par un point pour les décimales
    text = text.replace('_', '-')
    text = text.replace('~', '-')
    # Supprimer tous les caractères non autorisés
    text = re.sub(r'[^0-9\.\+\-\*/\(\)]', '', text)
    
    return text, ori_text


def get_text_from_im_gpt(image, client):
    prompt = "Extract mathematical expression from the image. Just send the text, no more."
    # Chargez l'image en tant que fichier binaire
    buffered = io.BytesIO()
    # Save the image to the buffer in PNG format
    image.save(buffered, format="PNG")
    # Retrieve the byte data from the buffer
    image_data = buffered.getvalue()
    base64_image = base64.b64encode(image_data).decode('utf-8')

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"
                    },
                }
            ],
        }
    ]
    )
    ori_text = response.choices[0].message.content
    
    text = ori_text.replace(' ', '')  # Supprimer les espaces
    text = text.replace('—', '-')
    text = text.replace('÷', '/')  # Remplacer le symbole de division
    text = text.replace('x', '*')  # Remplacer le symbole de multiplication en minuscule
    text = text.replace('X', '*')  # Remplacer le symbole de multiplication en majuscule
    text = text.replace(',', '.')  # Remplacer la virgule par un point pour les décimales
    text = text.replace('_', '-')
    text = text.replace('~', '-')
    text = text.replace('×', '*')
    text = text.replace(':', '/')
    text = text.replace('=', '/')
    # Supprimer tous les caractères non autorisés
    text = re.sub(r'[^0-9\.\+\-\*/\(\)]', '', text)
    
    return text, ori_text

def solve_operation(text):
    try:
        # Parser l'expression en un arbre syntaxique
        expr_ast = ast.parse(text, mode='eval').body
        # Évaluer l'expression en toute sécurité
        result = safe_eval(expr_ast)
        return None, result
    except ZeroDivisionError:
        return "Erreur : Division par zéro", ""
    except Exception as e:
        return f"Erreur lors de l'évaluation de l'expression : {e}", ""

