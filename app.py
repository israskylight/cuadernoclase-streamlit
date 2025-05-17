import streamlit as st
import json
from datetime import datetime

GRUPOS_FILE = "grupos.json"
CUADERNO_FILE = "cuadernoclase.json"

# --- Función de cálculo de nota ---
def calcular_nota(hubo_teo, participacion, no_part, hubo_prac, material, trabajo):
    # Exclusión si hay justificada en cualquier casilla
    if no_part == "Justificada" or material == "No (Justificada)" or trabajo == "No (Justificada)":
        return None
    # Sin clases
    if not hubo_teo and not hubo_prac:
        return None
    # Solo práctica
    if not hubo_teo and hubo_prac:
        if material == "Sí" or trabajo in ("Sí", "Parcialmente"):
            return 5
        return 0
    # Solo teórica
    if hubo_teo and not hubo_prac:
        if no_part == "Injustificada":
            return 0
        if participacion in ("Kahoot", "Mentimeter", "Apuntes"):
            return 10
        return 0
    # Ambas clases: promediar
    nt = 10 if participacion in ("Kahoot", "Mentimeter", "Apuntes") else 0
    np = 10 if material == "Sí" and trabajo == "Sí" else (5 if trabajo == "Parcialmente" else 0)
    return (nt + np) / 2

# --- Carga de datos ---
try:
    grupos = json.load(open(GRUPOS_FILE, "r"))
except FileNotFoundError:
    grupos = {}

st.title("Gestión de Grupos y Evaluación")

# 1) Selección de grupo
grupo = st.selectbox("Selecciona un grupo", list(grupos.keys()))

# 2) Fecha de evaluación
fecha = st.date_input("Fecha de evaluación", datetime.today())

# 3) Clase teórica
hubo_teo = st.checkbox("Hubo clase teórica?")
if hubo_teo:
    participacion = st.selectbox("Participación", ["", "Kahoot", "Mentimeter", "Apuntes"])
    no_part = st.selectbox("¿No participa?", ["", "Justificada", "Injustificada"])
else:
    participacion = ""
    no_part = ""

# 4) Clase práctica
hubo_prac = st.checkbox("Hubo clase práctica?")
if hubo_prac:
    material = st.selectbox("Material", ["", "Sí", "No (Justificada)", "No (Injustificada)"])
    trabajo  = st.selectbox("Trabajo", ["", "Sí", "Parcialmente", "No (Justificada)", "No (Injustificada)"])
else:
    material = ""
    trabajo  = ""

# 5) Botón y resultado
if st.button("Calcular nota prevista"):
    nota = calcular_nota(hubo_teo, participacion, no_part, hubo_prac, material, trabajo)
    if nota is None:
        st.error("Excluido")
    else:
        st.success(f"Nota prevista: {nota:.2f}")
