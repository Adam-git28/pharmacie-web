# pharmacie_web/app.py
from flask import Flask, render_template, request, redirect, send_from_directory
from stock import charger_stock, sauvegarder_stock, ajouter_produit, mise_a_jour_stock
from comptoir import vendre_produit, enregistrer_vente
from fpdf import FPDF
import os
import csv
import datetime

app = Flask(__name__)

STOCK_FILE = "produits.csv"
VENTES_FILE = "ventes.csv"
CLIENT_FILE = "clients.csv"
FACTURE_DIR = "factures"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stock")
def stock():
    stock = charger_stock(STOCK_FILE)
    return render_template("stock.html", stock=stock)

@app.route("/ajout-produit", methods=["GET", "POST"])
def ajout_produit():
    if request.method == "POST":
        nom = request.form["nom"]
        prix = float(request.form["prix"])
        quantite = int(request.form["quantite"])
        stock = charger_stock(STOCK_FILE)
        ajouter_produit(stock, nom, prix, quantite)
        sauvegarder_stock(STOCK_FILE, stock)
        return redirect("/stock")
    return render_template("ajout_produit.html")

@app.route("/vente", methods=["GET", "POST"])
def vente():
    if request.method == "POST":
        nom = request.form["nom"]
        quantite = int(request.form["quantite"])
        client = request.form["client"]
        stock = charger_stock(STOCK_FILE)
        total = vendre_produit(stock, nom, quantite)
        if total is not None:
            enregistrer_vente(VENTES_FILE, nom, quantite, total)
            sauvegarder_stock(STOCK_FILE, stock)

            # Générer la facture PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Facture Pharmacie", ln=True, align="C")
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Client : {client}", ln=True)
            pdf.cell(200, 10, txt=f"Produit : {nom}", ln=True)
            pdf.cell(200, 10, txt=f"Quantité : {quantite}", ln=True)
            pdf.cell(200, 10, txt=f"Total : {total:.2f} $", ln=True)

            # Dossier factures et fichier unique
            os.makedirs(FACTURE_DIR, exist_ok=True)
            horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"facture_{client}_{horodatage}.pdf"
            chemin = os.path.join(FACTURE_DIR, nom_fichier)
            pdf.output(chemin)

            return redirect("/")
        else:
            return "Erreur : Stock insuffisant ou produit introuvable."
    return render_template("vente.html")

@app.route("/facture/<filename>")
def telecharger_facture(filename):
    return send_from_directory(FACTURE_DIR, filename)

@app.route("/factures")
def liste_factures():
    fichiers = os.listdir(FACTURE_DIR)
    fichiers.sort(reverse=True)
    return render_template("factures.html", factures=fichiers)

@app.route("/ajout-client", methods=["GET", "POST"])
def ajout_client():
    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        telephone = request.form["telephone"]
        email = request.form["email"]
        with open(CLIENT_FILE, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([nom, prenom, telephone, email])
        return redirect("/")
    return render_template("ajout_client.html")

if __name__ == '__main__':
    os.makedirs(FACTURE_DIR, exist_ok=True)
    app.run(debug=True)
