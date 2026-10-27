"""Interfaz gráfica (tkinter/ttk). Tema oscuro. Las operaciones corren en hilos; la UI solo muestra datos reales.

Nota de estado: esta GUI no se ha podido ejecutar en el entorno de desarrollo (sin tkinter ni pantalla);
solo se ha comprobado que compila. Requiere prueba manual en Windows.
"""
from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .. import service
from ..config import Settings, logs_dir
from ..fl_locator import find_installs, open_in_fl
from ..i18n import t
from ..repair import SampleRemap, plan_repairs
from ..report import save_report, to_markdown
from ..validate import validate_pair
from ..version import APP_STAGE, APP_VERSION, BRAND

try:  # arrastrar y soltar es opcional (paquete tkinterdnd2)
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _Base = TkinterDnD.Tk
    HAS_DND = True
except Exception:  # noqa: BLE001
    _Base = tk.Tk
    HAS_DND = False

BG, PANEL, FG, MUTED, ACCENT = "#101318", "#181c23", "#e8ecf2", "#9aa4b2", "#00c2ff"
SEV_COLOR = {"critical": "#ff4d6d", "error": "#ff7b54", "warning": "#f2c230", "info": "#7aa2ff"}


class App(_Base):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.load()
        self.files: list[Path] = []
        self.analyses: dict[Path, service.Analysis] = {}
        self.last_output: Path | None = None
        self.last_report: dict | None = None
        self.q: queue.Queue = queue.Queue()
        self.title(f"{t('gui.title')} v{APP_VERSION} ({APP_STAGE})")
        self.geometry("1100x720")
        self.minsize(820, 560)
        self.configure(bg=BG)
        self._style()
        self._build()
        self.after(100, self._poll)

    # ---- estilo y construcción
    def _style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, font=("Segoe UI", 10))
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("Title.TLabel", font=("Segoe UI Semibold", 20), foreground=ACCENT)
        s.configure("TButton", padding=(12, 7), background="#232a35", foreground=FG, borderwidth=0)
        s.map("TButton", background=[("active", "#2d3744"), ("disabled", "#171b22")],
              foreground=[("disabled", "#5b6573")])
        s.configure("Accent.TButton", background=ACCENT, foreground="#001018")
        s.map("Accent.TButton", background=[("active", "#35d0ff")])
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG, rowheight=26, borderwidth=0)
        s.configure("Treeview.Heading", background="#232a35", foreground=FG, font=("Segoe UI Semibold", 9))
        s.map("Treeview", background=[("selected", "#1f4a63")])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background="#1b212b", foreground=MUTED, padding=(14, 7))
        s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", FG)])

    def _build(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)
        head = ttk.Frame(root)
        head.pack(fill="x")
        ttk.Label(head, text=t("gui.title"), style="Title.TLabel").pack(side="left")
        ttk.Label(head, text=f"   {t('gui.subtitle')} · {BRAND}", style="Muted.TLabel").pack(side="left", pady=(8, 0))
        ttk.Button(head, text=t("gui.settings"), command=self.open_settings).pack(side="right")
        ttk.Button(head, text=t("gui.logs"), command=self.show_logs).pack(side="right", padx=6)

        self.drop = tk.Label(root, text=t("gui.drop"), bg=PANEL, fg=MUTED, height=3, relief="flat",
                             font=("Segoe UI", 11), cursor="hand2")
        self.drop.pack(fill="x", pady=10)
        self.drop.bind("<Button-1>", lambda _e: self.choose_files())
        if HAS_DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        self.btns: dict[str, ttk.Button] = {}
        for key, cmd, accent in (("select", self.choose_files, False), ("analyze", self.do_analyze, True),
                                 ("repair", self.do_repair, False), ("convert", self.do_convert, False),
                                 ("compare", self.do_compare, False), ("open_fl", self.do_open, False),
                                 ("save_report", self.save_current_report, False)):
            b = ttk.Button(bar, text=t("gui." + key), command=cmd, style="Accent.TButton" if accent else "TButton")
            b.pack(side="left", padx=(0, 6))
            self.btns[key] = b
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", pady=(10, 2))
        self.status = ttk.Label(root, text=t("gui.no_file"), style="Muted.TLabel")
        self.status.pack(anchor="w")

        pw = ttk.PanedWindow(root, orient="vertical")
        pw.pack(fill="both", expand=True, pady=(8, 0))
        top = ttk.Frame(pw)
        pw.add(top, weight=1)
        self.files_tree = ttk.Treeview(top, columns=("file", "diag", "conf"), show="headings", height=4,
                                       selectmode="browse")
        for c, txt, w in (("file", "Proyecto", 360), ("diag", "Diagnóstico principal", 520), ("conf", "Confianza", 100)):
            self.files_tree.heading(c, text=txt)
            self.files_tree.column(c, width=w, stretch=(c == "diag"))
        self.files_tree.pack(fill="both", expand=True)
        self.files_tree.bind("<<TreeviewSelect>>", lambda _e: self._show_selected())

        self.nb = ttk.Notebook(pw)
        pw.add(self.nb, weight=3)
        self.issues = ttk.Treeview(self.nb, columns=("sev", "conf", "cat", "msg"), show="headings")
        for c, txt, w in (("sev", "Severidad", 90), ("conf", "Confianza", 100), ("cat", "Categoría", 100), ("msg", "Incidencia", 700)):
            self.issues.heading(c, text=txt)
            self.issues.column(c, width=w, stretch=(c == "msg"))
        for sev, col in SEV_COLOR.items():
            self.issues.tag_configure(sev, foreground=col)
        self.nb.add(self.issues, text="Incidencias")
        self.diff = ttk.Treeview(self.nb, columns=("cat", "key", "before", "after", "status"), show="headings")
        for c, txt, w in (("cat", "Categoría", 90), ("key", "Elemento", 380), ("before", "Antes", 90), ("after", "Después", 90), ("status", "Estado", 200)):
            self.diff.heading(c, text=txt)
            self.diff.column(c, width=w, stretch=(c == "key"))
        self.nb.add(self.diff, text="Antes / después")
        self.report_txt = self._text()
        self.nb.add(self.report_txt, text="Informe")
        self._set_text(self.report_txt, "Selecciona un proyecto y pulsa Analizar. No se muestra nada que no se haya leído realmente.")

    def _text(self) -> tk.Text:
        return tk.Text(self.nb, bg=PANEL, fg=FG, insertbackground=FG, relief="flat", wrap="word",
                       font=("Consolas", 10), padx=10, pady=8)

    @staticmethod
    def _set_text(w: tk.Text, s: str) -> None:
        w.configure(state="normal"); w.delete("1.0", "end"); w.insert("1.0", s); w.configure(state="disabled")

    # ---- hilos
    def _busy(self, on: bool, msg: str = "") -> None:
        if on:
            self.progress.start(12)
        else:
            self.progress.stop()
        for b in self.btns.values():
            b.state(["disabled"] if on else ["!disabled"])
        self.status.configure(text=msg or t("gui.ready"))

    def _run(self, fn, done, msg: str) -> None:
        self._busy(True, msg)

        def worker() -> None:
            try:
                self.q.put((done, fn(), None))
            except Exception as e:  # noqa: BLE001
                self.q.put((done, None, e))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                done, res, err = self.q.get_nowait()
                self._busy(False)
                if err:
                    messagebox.showerror("No se pudo completar la operación", str(err))
                else:
                    done(res)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    # ---- acciones
    def _on_drop(self, ev) -> None:
        self._add_files([Path(p) for p in self.tk.splitlist(ev.data)])

    def choose_files(self) -> None:
        sel = filedialog.askopenfilenames(title="Seleccionar proyectos FL Studio",
                                          filetypes=[("Proyectos FL Studio", "*.flp"), ("Todos", "*.*")])
        if sel:
            self._add_files([Path(p) for p in sel])

    def _add_files(self, paths: list[Path]) -> None:
        self.files = [p for p in paths if p.is_file()]
        self.status.configure(text=f"{len(self.files)} archivo(s) seleccionado(s).")
        self.files_tree.delete(*self.files_tree.get_children())
        for p in self.files:
            self.files_tree.insert("", "end", iid=str(p), values=(str(p), "—", "—"))

    def _current(self) -> Path | None:
        sel = self.files_tree.selection()
        if sel:
            return Path(sel[0])
        return self.files[0] if self.files else None

    def do_analyze(self) -> None:
        if not self.files:
            return self.choose_files()
        files = list(self.files)
        self._run(lambda: [service.analyze_file(p, self.settings) for p in files], self._analysis_done,
                  "Analizando (solo lectura)…")

    def _analysis_done(self, results: list[service.Analysis]) -> None:
        for a in results:
            self.analyses[a.path] = a
            self.files_tree.item(str(a.path), values=(str(a.path), a.diag.primary_text,
                                                       t("conf." + a.diag.primary_confidence)))
        if results:
            self.files_tree.selection_set(str(results[0].path))
            self._show_selected()

    def _show_selected(self) -> None:
        p = self._current()
        a = self.analyses.get(p) if p else None
        if not a:
            return
        self.issues.delete(*self.issues.get_children())
        for i in a.diag.issues:
            self.issues.insert("", "end", values=(t("sev." + i.severity), t("conf." + i.confidence), i.category, i.message),
                               tags=(i.severity,))
        self.last_report = a.report()
        self._set_text(self.report_txt, to_markdown(self.last_report))

    def _need_analysis(self) -> service.Analysis | None:
        p = self._current()
        a = self.analyses.get(p) if p else None
        if not a:
            messagebox.showinfo("Analiza primero", "Pulsa «Analizar» para este proyecto antes de continuar.")
        return a

    def do_repair(self) -> None:
        a = self._need_analysis()
        if not a:
            return
        actions = plan_repairs(a.doc, a.diag)
        if not actions:
            return messagebox.showinfo("Reparar", t("RP.nothing"))
        trim = any(x.code == "trim_tail" for x in actions)
        remaps: list[SampleRemap] = []
        lines = []
        for x in actions:
            lines.append(f"• {x.description}\n   Riesgo: {x.risk}")
            if x.code == "remap_sample":
                if messagebox.askyesno("Confirmar ruta de sample",
                                       f"¿Usar esta coincidencia?\n\nAntigua:\n{x.old}\n\nPropuesta:\n{x.new}"):
                    remaps.append(SampleRemap(x.event_index, x.old, x.new))
        if trim and not messagebox.askyesno("Confirmar reparación", "Se creará una COPIA reparada (el original no se toca):\n\n"
                                            + "\n".join(lines) + "\n\n¿Continuar?"):
            trim = False
        if not trim and not remaps:
            return
        out = self.settings.resolved_output_dir()
        self._run(lambda: service.repair_file(a, out, trim, remaps),
                  lambda r: self._repair_done(a, r), "Reparando copia…")

    def _repair_done(self, a: service.Analysis, r) -> None:
        res, val = r
        self.last_output = Path(res.output)
        rep = a.report(operation=res, validation=val)
        self.last_report = rep
        save_report(rep, self.last_output.parent, self.last_output.stem)
        self._set_text(self.report_txt, to_markdown(rep))
        self._fill_diff(val)
        self.nb.select(self.diff)
        messagebox.showinfo("Copia creada", f"{res.output}\n\nValidación A: {val.A.status} · B: {val.B.status}\n"
                            "C (apertura en FL Studio): PENDIENTE — ábrelo manualmente.")

    def _fill_diff(self, val) -> None:
        self.diff.delete(*self.diff.get_children())
        for d in val.diff:
            st = d.status + (" (previsto)" if d.explained else "")
            self.diff.insert("", "end", values=(d.category, d.key, d.before, d.after, st))

    def do_convert(self) -> None:
        a = self._need_analysis()
        if a:
            c = a.conversion
            messagebox.showinfo("Evaluación de conversión", f"Destino: FL Studio {a.target_major} ({a.target_source})\n\n{c.explanation}"
                                + ("" if c.can_generate_file else "\n\nNo se ha generado ningún archivo."))

    def do_compare(self) -> None:
        a = filedialog.askopenfilename(title="Original", filetypes=[("FLP", "*.flp")])
        b = filedialog.askopenfilename(title="Resultado", filetypes=[("FLP", "*.flp")]) if a else ""
        if a and b:
            self._run(lambda: validate_pair(Path(a).read_bytes(), Path(b).read_bytes()),
                      lambda v: (self._fill_diff(v), self.nb.select(self.diff)), "Comparando…")

    def do_open(self) -> None:
        target = self.last_output or self._current()
        if not target:
            return
        try:
            open_in_fl(str(target), self.settings.fl_exe or (find_installs()[0].exe if find_installs() else None))
            messagebox.showinfo("Apertura manual", "Se ha lanzado FL Studio. La validación en FL Studio (nivel C) sigue "
                                "PENDIENTE hasta que compruebes tú que el proyecto abre y suena bien.")
        except OSError as e:
            messagebox.showerror("No se pudo abrir", str(e))

    def save_current_report(self) -> None:
        if not self.last_report:
            return messagebox.showinfo("Informe", "Aún no hay informe.")
        out = filedialog.asksaveasfilename(defaultextension=".json", initialfile="informe_cray.json",
                                           filetypes=[("JSON", "*.json"), ("Markdown", "*.md")])
        if out:
            Path(out).write_text(json.dumps(self.last_report, ensure_ascii=False, indent=2, default=str)
                                 if out.endswith(".json") else to_markdown(self.last_report), encoding="utf-8")

    def show_logs(self) -> None:
        import os
        d = logs_dir()
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(d))  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            messagebox.showinfo("Registros", str(d))

    def open_settings(self) -> None:
        w = tk.Toplevel(self)
        w.title(t("gui.settings")); w.configure(bg=BG); w.geometry("560x300")
        mode = tk.StringVar(value=self.settings.target_mode)
        major = tk.StringVar(value=str(self.settings.target_major))
        outd = tk.StringVar(value=self.settings.output_dir)
        samples = tk.StringVar(value=";".join(self.settings.sample_search_dirs))
        for r, (lbl, var) in enumerate((("Destino (auto / manual)", mode), ("Versión mayor de destino", major),
                                        ("Carpeta de salida", outd), ("Carpetas de samples (;)", samples))):
            ttk.Label(w, text=lbl).grid(row=r, column=0, sticky="w", padx=12, pady=8)
            ttk.Entry(w, textvariable=var, width=48).grid(row=r, column=1, padx=6)

        def save() -> None:
            try:
                self.settings.target_major = int(major.get())
            except ValueError:
                return messagebox.showerror("Ajustes", "La versión debe ser un número (p. ej. 26).")
            self.settings.target_mode = mode.get() if mode.get() in ("auto", "manual") else "auto"
            self.settings.output_dir = outd.get().strip()
            self.settings.sample_search_dirs = [p for p in samples.get().split(";") if p.strip()]
            self.settings.save(); w.destroy()
        ttk.Button(w, text="Guardar", style="Accent.TButton", command=save).grid(row=5, column=1, sticky="e", pady=16)


def run() -> int:
    App().mainloop()
    return 0
