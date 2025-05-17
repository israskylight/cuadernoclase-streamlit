import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import json
from datetime import datetime

# Archivos JSON
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
        # Crear pestañas
        self.nb = ttk.Notebook(self)
        frame_eval = ttk.Frame(self.nb)
        frame_res  = ttk.Frame(self.nb)
        frame_grp  = ttk.Frame(self.nb)
        self.nb.add(frame_eval, text="Evaluar Jornada")
        self.nb.add(frame_res,  text="Calcular Resultados")
        self.nb.add(frame_grp,  text="Grupos")
        self.nb.pack(fill="both", expand=True)

        # Evaluar Jornada
        ttk.Label(frame_eval, text="Grupo:").pack(pady=5)
        self.cb_eval = ttk.Combobox(frame_eval, state="readonly", values=list(self.grupos.keys()))
        self.cb_eval.pack(pady=5)
        if self.grupos:
            self.cb_eval.current(0)
        ttk.Button(frame_eval, text="Evaluar Jornada", command=self.open_evaluation).pack(pady=5)

        # Calcular Resultados
        ttk.Label(frame_res, text="Grupo:").pack(pady=5)
        self.cb_res_group = ttk.Combobox(frame_res, state="readonly", values=list(self.grupos.keys()))
        self.cb_res_group.pack(pady=5)
        if self.grupos:
            self.cb_res_group.current(0)
        ttk.Label(frame_res, text="Periodo:").pack(pady=5)
        self.cb_res_period = ttk.Combobox(frame_res, state="readonly")
        self.cb_res_period.pack(pady=5)
        ttk.Button(frame_res, text="Calcular", command=self.open_results).pack(pady=5)
        self.cb_res_group.bind("<<ComboboxSelected>>", self._update_periods)
        self._update_periods()

        # Grupos
        ttk.Button(frame_grp, text="Crear Grupo", command=self.open_create_group).pack(pady=10)
        ttk.Button(frame_grp, text="Editar Grupo", command=self.open_edit_group).pack(pady=10)

    def _update_periods(self, event=None):
        grupo = self.cb_res_group.get()
        if grupo in self.grupos:
            tipo = self.grupos[grupo]["tipo"]
            fechas = self.grupos[grupo].get("fechas", [])
            if tipo == "Ciclos Formativos":
                vals = ["Primera Evaluación", "Segunda Evaluación", "Tercera Evaluación", "Curso completo"]
            else:
                vals = ["Curso completo"]
            self.cb_res_period['values'] = vals
            if vals:
                self.cb_res_period.current(0)
        else:
            self.cb_res_period['values'] = []
            self.cb_res_period.set("")

    def open_evaluation(self):
        grupo = self.cb_eval.get()
        if grupo:
            VentanaEvaluacion(self, grupo)

    def open_results(self):
        grupo  = self.cb_res_group.get()
        periodo = self.cb_res_period.get()
        if not grupo or not periodo:
            return
        data = self._load_cuaderno()
        info = self.grupos[grupo]
        tipo, fechas = info["tipo"], info.get("fechas", [])
        if tipo == "Ciclos Formativos":
            if periodo == "Curso completo":
                inicio, fin = fechas[0]
            else:
                idx = ["Primera Evaluación","Segunda Evaluación","Tercera Evaluación"].index(periodo)
                inicio, fin = fechas[idx]
        else:
            inicio, fin = fechas[0]
        fmt = "%d-%m-%Y"
        d_inicio = datetime.strptime(inicio, fmt)
        d_fin    = datetime.strptime(fin, fmt)

        dlg = tk.Toplevel(self)
        dlg.title(f"Resultados – {grupo} – {periodo}")
        dlg.geometry("700x500")
        frm = ttk.Frame(dlg)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["Alumno", "Media", "Excluidos", "Detalles"]
        for c, h in enumerate(headers):
            ttk.Label(frm, text=h, font=("TkDefaultFont",10,"bold")).grid(row=0, column=c, padx=5, pady=5)

        for i, alumno in enumerate(info.get("alumnos", []), start=1):
            registros = data.get(alumno, [])
            notas = []
            excluidos = 0
            for r in registros:
                try:
                    fecha_reg = datetime.strptime(r["fecha"], fmt)
                except:
                    continue
                if d_inicio <= fecha_reg <= d_fin:
                    if r["nota"] is None:
                        excluidos += 1
                    else:
                        notas.append(r["nota"])
            media = sum(notas)/len(notas) if notas else 0
            ttk.Label(frm, text=alumno).grid(row=i, column=0, sticky="w")
            ttk.Label(frm, text=f"{media:.2f}").grid(row=i, column=1)
            ttk.Label(frm, text=str(excluidos)).grid(row=i, column=2)
            ttk.Button(
                frm, text="Ver Detalles",
                command=lambda a=alumno, regs=[r for r in registros if d_inicio<=datetime.strptime(r['fecha'],fmt)<=d_fin]: self.show_filtered_details(a, regs)
            ).grid(row=i, column=3)

        ttk.Button(dlg, text="Copiar todo", command=lambda: self.copy_all(grupo, d_inicio, d_fin)).pack(pady=10)

    def copy_all(self, grupo, di, df):
        data = self._load_cuaderno()
        texto = f"Resultados – {grupo}\n" + "="*50 + "\n"
        for alumno in self.grupos[grupo].get("alumnos", []):
            registros = data.get(alumno, [])
            notas = []
            excluidos = 0
            for r in registros:
                try:
                    fecha_reg = datetime.strptime(r["fecha"], "%d-%m-%Y")
                except:
                    continue
                if di <= fecha_reg <= df:
                    if r["nota"] is None:
                        excluidos += 1
                    else:
                        notas.append(r["nota"])
            media = sum(notas)/len(notas) if notas else 0
            texto += f"{alumno}: media {media:.2f} ({excluidos} excluidos)\n"
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Copiado", "Datos copiados al portapapeles", parent=self)

    def show_filtered_details(self, alumno, registros):
        dlg = tk.Toplevel(self)
        dlg.title(f"Historial – {alumno}")
        dlg.geometry("400x300")
        tx = tk.Text(dlg)
        tx.pack(fill="both", expand=True, padx=10, pady=10)
        tx.insert("end", f"Historial de {alumno}\n" + "-"*40 + "\n")
        for r in registros:
            val = "Excluida" if r["nota"] is None else f"{r['nota']:.2f}"
            tx.insert("end", f"{r['fecha']}: {val}\n")
        ttk.Button(dlg, text="Copiar historial", command=lambda: self._copy_text(tx)).pack(pady=5)

    def _copy_text(self, widget):
        self.clipboard_clear()
        self.clipboard_append(widget.get("1.0", "end"))

    def open_create_group(self):
        dlg = tk.Toplevel(self)
        dlg.title("Crear Grupo")
        dlg.geometry("400x450")
        nombre_var, tipo_var, date_vars = tk.StringVar(), tk.StringVar(), []

        def redraw_dates(*args):
            for w in dlg.winfo_children():
                if getattr(w, 'is_date', False):
                    w.destroy()
            date_vars.clear()
            evals = ["Primera Evaluación","Segunda Evaluación","Tercera Evaluación"] if tipo_var.get()=="Ciclos Formativos" else ["Curso completo"]
            for name in evals:
                ttk.Label(dlg, text=name).pack(pady=2)
                d1 = DateEntry(dlg, date_pattern="dd-MM-yyyy"); d1.is_date=True; d1.pack(pady=2)
                d2 = DateEntry(dlg, date_pattern="dd-MM-yyyy"); d2.is_date=True; d2.pack(pady=2)
                date_vars.append((d1,d2))

        ttk.Label(dlg, text="Nombre:").pack(pady=5)
        ttk.Entry(dlg, textvariable=nombre_var).pack(pady=5)
        ttk.Label(dlg, text="Tipo:").pack(pady=5)
        cb_tipo = ttk.Combobox(dlg, textvariable=tipo_var, state="readonly", values=["Ciclos Formativos","Estudios Superiores"])
        cb_tipo.pack(pady=5)
        cb_tipo.bind("<<ComboboxSelected>>", redraw_dates)
        redraw_dates()

        def save_group():
            nm, tp = nombre_var.get().strip(), tipo_var.get()
            if not nm or not tp:
                messagebox.showerror("Error","Nombre y tipo obligatorios",parent=dlg)
                return
            fechas = [(d1.get(),d2.get()) for d1,d2 in date_vars]
            self.grupos[nm] = {"tipo":tp, "fechas":fechas, "alumnos":[]}
            self.save_data()
            self.cb_eval['values'] = list(self.grupos.keys())
            self.cb_res_group['values'] = list(self.grupos.keys())
            messagebox.showinfo("OK","Grupo creado",parent=dlg)
            dlg.destroy()

        ttk.Button(dlg, text="Guardar", command=save_group).pack(pady=10)

    def open_edit_group(self):
        dlg = tk.Toplevel(self)
        dlg.title("Editar Grupo")
        dlg.geometry("400x550")
        sel_var, date_vars, alumnos = tk.StringVar(), [], []
        ttk.Label(dlg, text="Grupo:").pack(pady=5)
        cb_grupo = ttk.Combobox(dlg, textvariable=sel_var, state="readonly", values=list(self.grupos.keys()))
        cb_grupo.pack(pady=5)
        frame_ed = ttk.Frame(dlg)
        frame_ed.pack(fill="both", expand=True, padx=10, pady=10)

        def load_group(*args):
            for w in frame_ed.winfo_children(): w.destroy()
            date_vars.clear(); alumnos.clear()
            info = self.grupos[sel_var.get()]
            evnames = ["Primera Evaluación","Segunda Evaluación","Tercera Evaluación"] if info['tipo']=="Ciclos Formativos" else ["Curso completo"]
            for idx,(f1,f2) in enumerate(info['fechas']):
                ttk.Label(frame_ed, text=evnames[idx]).pack(pady=2)
                d1 = DateEntry(frame_ed); d1.pack(pady=2); d1.set_date(datetime.strptime(f1, "%d-%m-%Y"))
                d2 = DateEntry(frame_ed); d2.pack(pady=2); d2.set_date(datetime.strptime(f2, "%d-%m-%Y"))
                date_vars.append((d1,d2))
            ttk.Label(frame_ed, text="Alumnos:").pack(pady=5)
            lb = tk.Listbox(frame_ed)
            lb.pack(side="left", fill="both", expand=True, padx=5)
            alumnos.extend(info['alumnos'])
            for a in alumnos: lb.insert("end", a)
            subf = ttk.Frame(frame_ed); subf.pack(side="left", padx=5)
            var_new = tk.StringVar()
            ttk.Entry(subf, textvariable=var_new).pack(pady=2)
            ttk.Button(subf, text="Añadir", command=lambda: self._add_alumno(var_new, alumnos, lb)).pack(pady=2)
            ttk.Button(subf, text="Quitar", command=lambda: self._remove_alumno(alumnos, lb)).pack(pady=2)
            ttk.Button(subf, text="Guardar Cambios", command=save_changes).pack(pady=10)

        def save_changes():
            self.grupos[sel_var.get()]['fechas'] = [(d1.get(),d2.get()) for d1,d2 in date_vars]
            self.grupos[sel_var.get()]['alumnos'] = alumnos.copy()
            self.save_data()
            self.cb_eval['values'] = list(self.grupos.keys())
            self.cb_res_group['values'] = list(self.grupos.keys())
            messagebox.showinfo("OK","Cambios guardados",parent=dlg)

        cb_grupo.bind("<<ComboboxSelected>>", load_group)
        if self.grupos:
            cb_grupo.current(0)
            load_group()

    def _add_alumno(self, var, lista, lb):
        nombre = var.get().strip()
        if nombre and nombre not in lista:
            lista.append(nombre)
            lb.insert("end", nombre)
        var.set("")

    def _remove_alumno(self, lista, lb):
        sel = lb.curselection()
        if sel:
            lista.pop(sel[0])
            lb.delete(sel)

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

        # Alumno
        self.lbl = ttk.Label(self, text=f"Alumno: {self.alumnos[self.idx]}")
        self.lbl.pack(pady=5)
        # Fecha
        ttk.Label(self, text="Fecha:").pack()
        self.fecha = tk.StringVar()
        self.cal   = DateEntry(self, textvariable=self.fecha, date_pattern="dd-MM-yyyy")
        self.cal.pack(pady=5)
        self.cal.set_date(datetime.now())
        # Teórica
        self.ct      = tk.BooleanVar()
        self.chk_teo = ttk.Checkbutton(self, text="Hubo clase teórica?", variable=self.ct, command=self._on_change)
        self.chk_teo.pack(pady=5)
        ttk.Label(self, text="Participación:").pack()
        self.part    = ttk.Combobox(self, state="disabled", values=["Kahoot","Mentimeter","Apuntes"])
        self.part.pack(pady=2)
        self.part.bind("<<ComboboxSelected>>", lambda e: self._on_change())
        self.nr      = tk.StringVar()
        self.rbj     = ttk.Radiobutton(self, text="No participa (Justificada)", variable=self.nr, value="just", command=self._on_change)
        self.rbi     = ttk.Radiobutton(self, text="No participa (Injustificada)", variable=self.nr, value="injust", command=self._on_change)
        self.rbj.pack()
        self.rbi.pack()
        # Práctica
        self.cp       = tk.BooleanVar()
        self.chk_prac = ttk.Checkbutton(self, text="Hubo clase práctica?", variable=self.cp, command=self._on_change)
        self.chk_prac.pack(pady=5)
        ttk.Label(self, text="Material:").pack()
        self.mat      = ttk.Combobox(self, state="disabled",
                                   values=["Sí","No (Justificada)","No (Injustificada)"])
        self.mat.pack(pady=2)
        self.mat.bind("<<ComboboxSelected>>", lambda e: self._on_change())
        ttk.Label(self, text="Trabajo:").pack()
        self.trab     = ttk.Combobox(self, state="disabled",
                                   values=["Sí","Parcialmente","No (Justificada)","No (Injustificada)"])
        self.trab.pack(pady=2)
        self.trab.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        # Nota prevista
        self.lbl_nota = ttk.Label(self, text="Nota prevista: 0.00")
        self.lbl_nota.pack(pady=10)

        # Navegación
        nav = ttk.Frame(self)
        nav.pack(pady=10)
        self.btn_prev = ttk.Button(nav, text="Anterior", command=self.prev_student)
        self.btn_next = ttk.Button(nav, text="Guardar y Siguiente", command=self.next_student)
        self.btn_prev.grid(row=0, column=0, padx=5)
        self.btn_next.grid(row=0, column=1, padx=5)

        # Inicializar controles
        self._on_change()
        self._update_nav()

    def _on_change(self):
        # Gestión de habilitación de controles
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
        # Actualizar nota prevista
        nota = self.calcular_nota()
        texto = f"Nota prevista: {'Excluido' if nota is None else f'{nota:.2f}'}"
        self.lbl_nota.config(text=texto)

    def _update_nav(self):
        # Botón Anterior
        self.btn_prev.config(state="normal" if self.idx > 0 else "disabled")

    def calcular_nota(self):
        # Excluir si justificada en cualquier campo
        if self.nr.get() == "just" or self.mat.get() == "No (Justificada)" or self.trab.get() == "No (Justificada)":
            return None
        # Sin clases
        if not self.ct.get() and not self.cp.get():
            return None
        # Solo práctica
        if not self.ct.get() and self.cp.get():
            if self.mat.get() == "Sí" or self.trab.get() in ("Sí","Parcialmente"):
                return 5
            return 0
        # Solo teórica
        if self.ct.get() and not self.cp.get():
            if self.nr.get() == "injust":
                return 0
            if self.part.get() in ("Kahoot","Mentimeter","Apuntes"):
                return 10
            return 0
        # Ambas clases: promediar
        nt = 10 if self.part.get() in ("Kahoot","Mentimeter","Apuntes") else 0
        np = 10 if self.mat.get() == "Sí" and self.trab.get() == "Sí" else (5 if self.trab.get() == "Parcialmente" else 0)
        return (nt + np) / 2

    def prev_student(self):
        # Guardar y retroceder
        self._save_note()
        if self.idx > 0:
            self.idx -= 1
            self._load_student()

    def next_student(self):
        # Guardar y avanzar o finalizar
        self._save_note()
        if self.idx < len(self.alumnos) - 1:
            self.idx += 1
            self._load_student()
        else:
            messagebox.showinfo("Fin","Evaluación completada",parent=self)
            self.destroy()

    def _save_note(self):
        # Persistir nota
        nota = self.calcular_nota()
        alumno = self.alumnos[self.idx]
        fecha  = self.fecha.get()
        regs = [r for r in self.data.get(alumno,[]) if r['fecha'] != fecha]
        regs.append({'fecha':fecha,'nota':nota})
        self.data[alumno] = regs
        with open(CUADERNO_FILE,'w') as f:
            json.dump(self.data,f,indent=4)

    def _load_student(self):
        # Cargar siguiente/alumno actual
        alumno = self.alumnos[self.idx]
        self.lbl.config(text=f"Alumno: {alumno}")
        self.cal.set_date(datetime.now())
        self.ct.set(False)
        self.cp.set(False)
        self.part.set("")
        self.nr.set("")
        self.mat.set("")
        self.trab.set("")
        self._on_change()
        self._update_nav()

# Arranque de la aplicación
if __name__ == "__main__":
    app = App()
    app.mainloop()











