import streamlit as st
import json
from datetime import datetime

GRUPOS_FILE    = "grupos.json"
CUADERNO_FILE  = "cuadernoclase.json"

# ——— Helpers de JSON ————————————————————————
@st.cache_data
def load_grupos():
    try:
        return json.load(open(GRUPOS_FILE, "r"))
    except FileNotFoundError:
        return {}

@st.cache_data
def load_cuaderno():
    try:
        return json.load(open(CUADERNO_FILE, "r"))
    except FileNotFoundError:
        return {}

def save_grupos(grupos):
    with open(GRUPOS_FILE, "w") as f:
        json.dump(grupos, f, indent=4)
    load_grupos.clear()

def save_cuaderno(cuaderno):
    with open(CUADERNO_FILE, "w") as f:
        json.dump(cuaderno, f, indent=4)
    load_cuaderno.clear()

# ——— Cálculo de nota ————————————————————————
def calcular_nota(hubo_teo, participacion, no_part, hubo_prac, material, trabajo):
    # Exclusión por justificada
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
    # Ambas clases: promedio
    nt = 10 if participacion in ("Kahoot", "Mentimeter", "Apuntes") else 0
    np = 10 if material == "Sí" and trabajo == "Sí" else (5 if trabajo == "Parcialmente" else 0)
    return (nt + np) / 2

# ——— UI de Streamlit ——————————————————————————
st.set_page_config(page_title="Cuaderno de Clase", layout="wide")
grupos   = load_grupos()
cuaderno = load_cuaderno()

tab1, tab2, tab3 = st.tabs(["Evaluar Jornada", "Calcular Resultados", "Grupos"])

# — Pestaña 1: Evaluar Jornada —————————————————
with tab1:
    st.header("Evaluar Jornada")
    if not grupos:
        st.warning("No hay grupos definidos. Ve a la pestaña 'Grupos' para crear uno.")
    else:
        grupo = st.selectbox("Grupo", list(grupos.keys()))
        fecha = st.date_input("Fecha", datetime.today())
        hubo_teo = st.checkbox("Hubo clase teórica?")
        if hubo_teo:
            participacion = st.selectbox("Participación", ["", "Kahoot", "Mentimeter", "Apuntes"])
            no_part       = st.selectbox("¿No participa?", ["", "Justificada", "Injustificada"])
        else:
            participacion = ""
            no_part       = ""
        hubo_prac = st.checkbox("Hubo clase práctica?")
        if hubo_prac:
            material = st.selectbox("Material", ["", "Sí", "No (Justificada)", "No (Injustificada)"])
            trabajo  = st.selectbox(
                "Trabajo",
                ["", "Sí", "Parcialmente", "No (Justificada)", "No (Injustificada)"]
            )
        else:
            material = ""
            trabajo  = ""

        if st.button("Grabar evaluación"):
            nota = calcular_nota(hubo_teo, participacion, no_part, hubo_prac, material, trabajo)
            regs = cuaderno.get(grupo, [])
            regs = [r for r in regs if r["fecha"] != fecha.strftime("%d-%m-%Y")]
            regs.append({"fecha": fecha.strftime("%d-%m-%Y"), "nota": nota})
            cuaderno[grupo] = regs
            save_cuaderno(cuaderno)
            if nota is None:
                st.error("Excluido")
            else:
                st.success(f"Nota guardada: {nota:.2f}")

# — Pestaña 2: Calcular Resultados ———————————————
with tab2:
    st.header("Calcular Resultados")
    if not grupos:
        st.warning("No hay grupos para calcular resultados.")
    else:
        grupo = st.selectbox("Grupo", list(grupos.keys()), key="res_grupo")
        tipo  = grupos[grupo]["tipo"]
        fechas = grupos[grupo]["fechas"]
        if tipo == "Ciclos Formativos":
            periodos = ["Primera", "Segunda", "Tercera", "Curso completo"]
        else:
            periodos = ["Curso completo"]
        periodo = st.selectbox("Periodo", periodos)
        if tipo == "Ciclos Formativos" and periodo != "Curso completo":
            idx = ["Primera", "Segunda", "Tercera"].index(periodo)
            inicio, fin = fechas[idx]
        else:
            inicio, fin = fechas[0] if tipo != "Ciclos Formativos" else (fechas[0][0], fechas[-1][1])

        if st.button("Mostrar resultados"):
            fmt = "%d-%m-%Y"
            di = datetime.strptime(inicio, fmt)
            df = datetime.strptime(fin, fmt)
            regs = cuaderno.get(grupo, [])
            summary = []
            for alum in grupos[grupo]["alumnos"]:
                vals = [
                    r["nota"] for r in regs
                    if di <= datetime.strptime(r["fecha"], fmt) <= df and r["nota"] is not None
                ]
                exc = sum(
                    1 for r in regs
                    if di <= datetime.strptime(r["fecha"], fmt) <= df and r["nota"] is None
                )
                media = sum(vals) / len(vals) if vals else 0
                summary.append({"Alumno": alum, "Media": f"{media:.2f}", "Excluidos": exc})
            st.table(summary)

# — Pestaña 3: Crear/Editar Grupos —————————————————
with tab3:
    st.header("Grupos")
    modo = st.radio("¿Qué quieres hacer?", ["Crear grupo", "Editar grupo"])
    if modo == "Crear grupo":
        nm  = st.text_input("Nombre del grupo")
        tp  = st.selectbox("Tipo", ["Ciclos Formativos", "Estudios Superiores"])
        fechas_sel = []
        labels = ["Primera", "Segunda", "Tercera"] if tp == "Ciclos Formativos" else ["Curso completo"]
        for lbl in labels:
            d1 = st.date_input(f"{lbl} inicio", key=f"{lbl}i")
            d2 = st.date_input(f"{lbl} fin",    key=f"{lbl}f")
            fechas_sel.append((d1.strftime("%d-%m-%Y"), d2.strftime("%d-%m-%Y")))
        if st.button("Guardar nuevo grupo"):
            grupos[nm] = {"tipo": tp, "fechas": fechas_sel, "alumnos": []}
            save_grupos(grupos)
            st.success(f"Grupo '{nm}' creado.")
    else:
        sel = st.selectbox("Selecciona un grupo", list(grupos.keys()))
        info = grupos[sel]
        st.subheader(f"Editando: {sel}")

        # Editar fechas con manejo de IndexError
        nuevas = []
        labels = ["Primera", "Segunda", "Tercera"] if info["tipo"] == "Ciclos Formativos" else ["Curso completo"]
        for idx, lbl in enumerate(labels):
            try:
                f1_str, f2_str = info["fechas"][idx]
                f1 = datetime.strptime(f1_str, "%d-%m-%Y")
                f2 = datetime.strptime(f2_str, "%d-%m-%Y")
            except Exception:
                f1 = f2 = datetime.today()
            d1 = st.date_input(f"{lbl} inicio", f1, key=f"e{lbl}i")
            d2 = st.date_input(f"{lbl} fin",    f2, key=f"e{lbl}f")
            nuevas.append((d1.strftime("%d-%m-%Y"), d2.strftime("%d-%m-%Y")))

        if st.button("Guardar cambios de fechas"):
            grupos[sel]["fechas"] = nuevas
            save_grupos(grupos)
            st.success("Fechas actualizadas.")

        st.markdown("---")
        # Editar alumnos
        st.write("Alumnos actuales:", info["alumnos"])
        nuevo = st.text_input("Añadir alumno")
        if st.button("Añadir alumno"):
            if nuevo.strip():
                info["alumnos"].append(nuevo.strip())
                save_grupos(grupos)
                st.experimental_rerun()

        rem = st.selectbox("Eliminar alumno", info["alumnos"] + [""])
        if rem and st.button("Eliminar alumno"):
            info["alumnos"].remove(rem)
            save_grupos(grupos)
            st.experimental_rerun()

        st.markdown("---")
        # Borrar grupo completo con confirmación
        if st.button("❌ Borrar grupo completo", key="del_grp"):
            confirm = st.checkbox("Confirmar borrado de este grupo")
            if confirm and st.button("Confirmar eliminación", key="confirm_del"):
                grupos.pop(sel, None)
                save_grupos(grupos)
                st.success(f"Grupo '{sel}' eliminado.")
                st.experimental_rerun()
