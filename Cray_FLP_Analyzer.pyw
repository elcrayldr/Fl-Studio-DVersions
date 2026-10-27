import os
import re
import json
import struct
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

APP_NAME = "Cray FLP Analyzer"
APP_VERSION = "0.1.0"

# This first version is intentionally read-only. It does not write to or alter FLP files.
# FLP's binary format is only partially documented; string scanning is heuristic,
# so all findings are labelled as clues rather than definitive plugin/sample inventories.

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def printable_strings(data, min_len=4):
    """Extract likely readable ASCII and UTF-16LE strings; heuristic only."""
    found = set()
    for m in re.finditer(rb"[ -~]{%d,}" % min_len, data):
        try:
            s = m.group().decode("ascii", errors="ignore").strip()
            if s:
                found.add(s)
        except Exception:
            pass
    # UTF-16LE runs: printable ASCII-range chars separated by NUL bytes
    for m in re.finditer(rb"(?:[ -~]\x00){%d,}" % min_len, data):
        try:
            s = m.group().decode("utf-16le", errors="ignore").strip()
            if s:
                found.add(s)
        except Exception:
            pass
    return sorted(found, key=str.casefold)

def analyze_flp(path):
    report = {
        "application": APP_NAME,
        "application_version": APP_VERSION,
        "analyzed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "file": os.path.abspath(path),
        "filename": os.path.basename(path),
        "read_only": True,
        "checks": [],
        "clues": {
            "plugin_or_component_names": [],
            "sample_or_preset_paths": [],
            "other_readable_strings": []
        },
        "warnings": []
    }

    if not os.path.isfile(path):
        raise FileNotFoundError("No se encuentra el archivo.")
    if os.path.splitext(path)[1].lower() != ".flp":
        report["warnings"].append("La extensión no es .flp. El análisis continuará, pero comprueba que sea un proyecto FL Studio.")
    size = os.path.getsize(path)
    report["size_bytes"] = size
    report["size_mib"] = round(size / (1024 * 1024), 3)
    report["sha256"] = sha256_file(path)

    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 8:
        report["checks"].append({"name": "Tamaño mínimo", "status": "FAIL", "detail": "El archivo es demasiado pequeño para un FLP normal."})
        report["warnings"].append("Archivo truncado o formato no reconocido.")
        return report

    # Standard FLP files use FLhd as the leading header signature.
    magic = data[:4]
    report["header_signature_hex"] = magic.hex(" ").upper()
    report["header_signature_text"] = magic.decode("latin1", errors="replace")
    if magic == b"FLhd":
        report["checks"].append({"name": "Firma FLP", "status": "PASS", "detail": "Se ha encontrado la firma FLhd esperada."})
        try:
            header_size = struct.unpack_from("<I", data, 4)[0]
            report["header_size_field"] = header_size
            if len(data) >= 16:
                fmt, channels, ppq = struct.unpack_from("<hHH", data, 8)
                report["internal_format_field"] = fmt
                report["header_channel_count_field"] = channels
                report["ppq_field"] = ppq
                report["checks"].append({"name": "Campos básicos del encabezado", "status": "INFO", "detail": f"Formato interno={fmt}; canales declarados={channels}; PPQ={ppq}. Estos campos no bastan por sí solos para determinar la versión comercial de FL Studio."})
        except struct.error:
            report["warnings"].append("No se pudieron interpretar todos los campos del encabezado.")
    else:
        report["checks"].append({"name": "Firma FLP", "status": "WARN", "detail": "No se ha encontrado FLhd al inicio del archivo."})
        report["warnings"].append("Puede ser un archivo dañado, un formato distinto o un contenedor que requiere tratamiento específico.")

    # Detect likely event/data marker without assuming a complete parse.
    if b"FLdt" in data[:64]:
        report["checks"].append({"name": "Marcador de datos FLdt", "status": "PASS", "detail": "Marcador localizado en los primeros 64 bytes."})
    elif b"FLdt" in data:
        report["checks"].append({"name": "Marcador de datos FLdt", "status": "INFO", "detail": "Marcador localizado fuera de la zona inicial; ubicación inusual o variante de formato."})
    else:
        report["checks"].append({"name": "Marcador de datos FLdt", "status": "WARN", "detail": "No se ha localizado el marcador FLdt mediante una búsqueda simple."})

    strings = printable_strings(data)
    # Candidate paths and names are clues, not a full semantic parse.
    path_clues = []
    plugin_clues = []
    other = []
    path_re = re.compile(r"(?i)(?:[a-z]:\\|\\\\|/).{2,220}")
    ext_re = re.compile(r"(?i)\.(wav|aif|aiff|mp3|ogg|flac|mid|fst|fxp|vst3?|dll|ini|preset)\b")
    plugin_words = re.compile(r"(?i)\b(serum|kontakt|massive|omnisphere|vital|sytrus|harmor|sylenth|fabfilter|waves|izotope|valhalla|gross beat|fruity|kirchhoff|ozone|pro-q|pro-c|pro-l)\b")
    for s in strings:
        if path_re.search(s) or ext_re.search(s):
            path_clues.append(s[:300])
        elif plugin_words.search(s):
            plugin_clues.append(s[:300])
        elif len(s) >= 5 and len(s) <= 160:
            other.append(s[:300])

    report["clues"]["sample_or_preset_paths"] = sorted(set(path_clues), key=str.casefold)[:250]
    report["clues"]["plugin_or_component_names"] = sorted(set(plugin_clues), key=str.casefold)[:250]
    report["clues"]["other_readable_strings"] = sorted(set(other), key=str.casefold)[:150]
    report["readable_string_count"] = len(strings)
    report["warnings"].append("La extracción de nombres y rutas es heurística. Puede omitir datos o mostrar fragmentos que no sean rutas/plugins reales.")
    report["warnings"].append("Esta versión no determina de forma fiable la versión exacta de FL Studio ni convierte o repara el proyecto.")
    report["summary"] = {
        "valid_header_signature": magic == b"FLhd",
        "file_size_bytes": size,
        "readable_strings_found": len(strings),
        "path_clues_found": len(report["clues"]["sample_or_preset_paths"]),
        "plugin_name_clues_found": len(report["clues"]["plugin_or_component_names"])
    }
    return report

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("980x680")
        self.minsize(760, 520)
        self.configure(bg="#15171b")
        self.path = None
        self.report = None
        self._style()
        self._build()

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#15171b")
        style.configure("TLabel", background="#15171b", foreground="#f0f0f0", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#f2c230")
        style.configure("Sub.TLabel", foreground="#b9bec7")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Treeview", background="#202329", fieldbackground="#202329", foreground="#f0f0f0", rowheight=28)
        style.configure("Treeview.Heading", background="#30343c", foreground="#ffffff", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#66551b")])

    def _build(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="CRAY FLP ANALYZER", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Analizador local de proyectos FL Studio · modo de solo lectura", style="Sub.TLabel").pack(anchor="w", pady=(3, 14))

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(0, 12))
        ttk.Button(top, text="Seleccionar archivo FLP…", command=self.choose_file).pack(side="left")
        ttk.Button(top, text="Analizar", command=self.start_analysis).pack(side="left", padx=8)
        ttk.Button(top, text="Guardar informe JSON…", command=self.save_json).pack(side="left")
        self.file_label = ttk.Label(root, text="Ningún archivo seleccionado", style="Sub.TLabel")
        self.file_label.pack(anchor="w", pady=(0, 12))

        columns = ("check", "status", "detail")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=8)
        self.tree.heading("check", text="Comprobación")
        self.tree.heading("status", text="Estado")
        self.tree.heading("detail", text="Detalle")
        self.tree.column("check", width=210, stretch=False)
        self.tree.column("status", width=85, stretch=False)
        self.tree.column("detail", width=590, stretch=True)
        self.tree.pack(fill="both", expand=True)

        ttk.Label(root, text="Pistas detectadas (no equivalen a una lectura completa del proyecto)", style="Sub.TLabel").pack(anchor="w", pady=(14, 5))
        self.details = tk.Text(root, height=8, bg="#202329", fg="#f0f0f0", insertbackground="#ffffff",
                               relief="flat", font=("Consolas", 9), wrap="word")
        self.details.pack(fill="both", expand=True)
        self.details.insert("1.0", "Selecciona un archivo .flp y pulsa Analizar.\n\nEl original no se modifica. La versión 0.1 no convierte ni repara archivos.")
        self.details.configure(state="disabled")

        footer = ttk.Label(root, text="Versión inicial · No sube archivos a Internet · No modifica el proyecto original", style="Sub.TLabel")
        footer.pack(anchor="w", pady=(10, 0))

    def choose_file(self):
        p = filedialog.askopenfilename(title="Seleccionar proyecto FL Studio", filetypes=[("Proyectos FL Studio", "*.flp"), ("Todos los archivos", "*.*")])
        if p:
            self.path = p
            self.file_label.configure(text=p)

    def start_analysis(self):
        if not self.path:
            self.choose_file()
            if not self.path:
                return
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("end", "Analizando en modo de solo lectura…")
        self.details.configure(state="disabled")
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self):
        try:
            report = analyze_flp(self.path)
            self.after(0, lambda: self._show_report(report))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error de análisis", str(e)))

    def _show_report(self, report):
        self.report = report
        for item in self.tree.get_children():
            self.tree.delete(item)
        for check in report.get("checks", []):
            self.tree.insert("", "end", values=(check["name"], check["status"], check["detail"]))
        c = report.get("clues", {})
        lines = [
            f"Archivo: {report.get('filename')}",
            f"Tamaño: {report.get('size_mib', 0)} MiB",
            f"SHA-256: {report.get('sha256', '')}",
            f"Firma inicial: {report.get('header_signature_text', '')!r}",
            f"Cadenas legibles detectadas: {report.get('readable_string_count', 0)}",
            "",
            "POSIBLES RUTAS / SAMPLES / PRESETS:"
        ]
        lines.extend("  • " + s for s in c.get("sample_or_preset_paths", [])[:40])
        lines += ["", "POSIBLES PLUGINS / COMPONENTES:"]
        lines.extend("  • " + s for s in c.get("plugin_or_component_names", [])[:40])
        lines += ["", "ADVERTENCIAS:"]
        lines.extend("  • " + s for s in report.get("warnings", []))
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")

    def save_json(self):
        if not self.report:
            messagebox.showinfo("Sin informe", "Analiza primero un archivo FLP.")
            return
        default = os.path.splitext(os.path.basename(self.path))[0] + "_cray_flp_report.json"
        out = filedialog.asksaveasfilename(title="Guardar informe", defaultextension=".json",
                                           initialfile=default, filetypes=[("Informe JSON", "*.json")])
        if not out:
            return
        try:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(self.report, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Informe guardado", f"Se ha guardado el informe:\n{out}")
        except Exception as e:
            messagebox.showerror("No se pudo guardar", str(e))

if __name__ == "__main__":
    App().mainloop()
