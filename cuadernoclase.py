import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import json
from datetime import datetime

GRUPOS_FILE = "grupos.json"
CUADERNO_FILE = "cuadernoclase.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de Grupos y Evaluación")
        self.geometry("800x600")
        self.grupos = {}
        self.load_data()
        self.create_widgets()

    def load_data(self):
        try:
            with open(GRUPOS_FILE, "r") as f:
                self.grupos = json.load(f)
        except FileNotFoundError:
            self.grupos = {}

    def save_data(self):
        with open(GRUPOS_FILE, "w") as f:
            json.dump(self.grupos, f, indent=4)

    def create_widgets(self):
        self.nb = ttk.Notebook(self)
        frame_eval = ttk.Frame(self.nb)
        self.nb.add(frame_eval, text="Evaluar Jornada")
        self.nb.pack(fill="both", expand=True)

        ttk.Label(frame_eval, text="Grupo:").pack(pady=5)
        self.cb_eval = ttk.Combobox(frame_eval, state="readonly", values=list(self.grupos.keys()))
        self.cb_eval.pack(pady=5)
        if self.grupos:
            self.cb_eval.current(0)
        ttk.Button(frame_eval, text="Evaluar Jornada", command=self.open_evaluation).pack(pady=5)

    def open_evaluation(self):
        grupo = self.cb_eval.get()
        if grupo:
            VentanaEvaluacion(self, grupo)

    def _load_cuaderno(self):
        try:
            with open(CUADERNO_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

class VentanaEvaluacion(tk.Toplevel):
    def __init__(self, parent, group):
        super().__init__(parent)
        self.parent  = parent
        self.group   = group
        self.title(f"Evaluar Jornada – {group}")
        self.geometry("520x500")
        self.data    = parent._load_cuaderno()
        self.alumnos = parent.grupos[group]['alumnos']
        self.idx     = 0

        self.lbl = ttk.Label(self, text=f"Alumno: {self.alumnos[self.idx]}")
        self.lbl.pack(pady=5)

        ttk.Label(self, text="Fecha:").pack()
        self.fecha = tk.StringVar()
        self.cal   = DateEntry(self, textvariable=self.fecha, date_pattern="dd-MM-yyyy")
        self.cal.pack(pady=5)
        self.cal.set_date(datetime.now())

        self.ct = tk.BooleanVar()
        self.chk_teo = ttk.Checkbutton(self, text="Hubo clase teórica?", variable=self.ct, command=self._on_change)
        self.chk_teo.pack(pady=5)

        ttk.Label(self, text="Participación:").pack()
        self.part = ttk.Combobox(self, state="disabled",
                                 values=["Kahoot", "Mentimeter", "Apuntes"])
        self.part.pack(pady=2)
        self.part.bind("<<ComboboxSelected>>", lambda e: self._on_change())  # << ACTUALIZA EN TIEMPO REAL

        self.nr = tk.StringVar(value="")
        self.rbj = ttk.Radiobutton(self, text="No participa (Justificada)", variable=self.nr, value="just", command=self._on_change)
        self.rbi = ttk.Radiobutton(self, text="No participa (Injustificada)", variable=self.nr, value="injust", command=self._on_change)
        self.rbj.pack()
        self.rbi.pack()

        self.cp = tk.BooleanVar()
        self.chk_prac = ttk.Checkbutton(self, text="Hubo clase práctica?", variable=self.cp, command=self._on_change)
        self.chk_prac.pack(pady=5)

        ttk.Label(self, text="Material:").pack()
        self.mat = ttk.Combobox(self, state="disabled",
                                values=["Sí", "No (Justificada)", "No (Injustificada)"])
        self.mat.pack(pady=2)
        self.mat.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        ttk.Label(self, text="Trabajo:").pack()
        self.trab = ttk.Combobox(self, state="disabled",
                                 values=["Sí", "Parcialmente", "No (Justificada)", "No (Injustificada)"])
        self.trab.pack(pady=2)
        self.trab.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        self.lbl_nota = ttk.Label(self, text="Nota prevista: 0.00")
        self.lbl_nota.pack(pady=10)

        self._on_change()

    def _on_change(self):
        if self.ct.get():
            self.part.config(state="readonly")
            self.rbj.config(state="normal")
            self.rbi.config(state="normal")
        else:
            self.part.set("")
            self.nr.set("")
            self.part.config(state="disabled")
            self.rbj.config(state="disabled")
            self.rbi.config(state="disabled")

        if self.cp.get():
            self.mat.config(state="readonly")
            self.trab.config(state="readonly")
        else:
            self.mat.set("")
            self.trab.set("")
            self.mat.config(state="disabled")
            self.trab.config(state="disabled")

        nota = self.calcular_nota()
        texto = f"Nota prevista: {'Excluido' if nota is None else f'{nota:.2f}'}"
        self.lbl_nota.config(text=texto)

    def calcular_nota(self):
        notas = []

        # --- CLASE TEÓRICA ---
        if self.ct.get():
            # 1. Participación válida → 10 (IGNORA radio)
            if self.part.get() in ("Kahoot", "Mentimeter", "Apuntes"):
                notas.append(10)
            # 2. Justificada → excluida
            elif self.nr.get() == "just":
                return None
            # 3. Injustificada → 0
            elif self.nr.get() == "injust":
                notas.append(0)
            # 4. Nada → 0
            else:
                notas.append(0)
        # --- CLASE PRÁCTICA ---
        if self.cp.get():
            if self.mat.get() == "No (Justificada)" or self.trab.get() == "No (Justificada)":
                return None
            elif self.mat.get() == "Sí" and self.trab.get() == "Sí":
                notas.append(10)
            elif self.trab.get() == "Parcialmente":
                notas.append(5)
            elif self.mat.get() == "No (Injustificada)":
                notas.append(0)
        if notas:
            return sum(notas) / len(notas)
        return 0

if __name__ == "__main__":
    app = App()
    app.mainloop()









