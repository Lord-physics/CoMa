"""Ventana Tk; toda red y clasificación se ejecutan fuera del hilo gráfico."""

import queue
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from .models import Message
from .service import MailService
from .startup import enabled as startup_enabled, set_enabled as set_startup


PROVIDERS = {"Gmail": "gmail", "Outlook / Hotmail": "outlook", "Educacyl": "educacyl"}
ACTIONS = (("Archivar", "archive"), ("Eliminar", "delete"), ("Spam", "spam"), ("Spam y borrar", "spam_delete"))


class App(tk.Tk):
    def __init__(self, service: MailService | None = None):
        super().__init__()
        self.service = service or MailService()
        self.title("CoMa · Bandeja no leída")
        self.geometry("1120x720")
        self.minsize(820, 500)
        self.configure(bg="#f3f5f8")
        self.events = queue.Queue()
        self.busy = False
        self.messages: list[Message] = []
        self.candidates: list[Message] = []
        self.candidate_window = None
        self._style()
        self._layout()
        self.after(100, self._drain_events)
        self.after(300, self.refresh)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=(9, 6))
        style.configure("Accent.TButton", padding=(10, 7), background="#1e5b88", foreground="white")
        style.map("Accent.TButton", background=[("active", "#174a70")])
        style.configure("TCheckbutton", background="#f3f5f8")

    def _layout(self):
        header = tk.Frame(self, bg="#f3f5f8")
        header.pack(fill="x", padx=20, pady=(18, 10))
        tk.Label(header, text="CoMa", font=("Segoe UI", 23, "bold"), bg="#f3f5f8", fg="#17324d").pack(side="left")
        tk.Label(header, text="  Bandeja no leída", font=("Segoe UI", 12), bg="#f3f5f8", fg="#526476").pack(side="left", pady=(10, 0))
        ttk.Button(header, text="Añadir cuenta", command=self._add_dialog).pack(side="right", padx=(7, 0))
        ttk.Button(header, text="Quitar cuenta", command=self._remove_dialog).pack(side="right", padx=(7, 0))
        ttk.Button(header, text="Actualizar", command=self.refresh, style="Accent.TButton").pack(side="right")

        controls = tk.Frame(self, bg="#f3f5f8")
        controls.pack(fill="x", padx=20, pady=(0, 8))
        self.start_var = tk.BooleanVar(value=startup_enabled())
        ttk.Checkbutton(controls, text="Abrir CoMa al iniciar sesión", variable=self.start_var,
                        command=self._toggle_startup).pack(side="left")
        self.count_var = tk.StringVar(value="Sin mensajes cargados")
        tk.Label(controls, textvariable=self.count_var, bg="#f3f5f8", fg="#526476").pack(side="right")

        body = tk.Frame(self, bg="#f3f5f8")
        body.pack(fill="both", expand=True, padx=20)
        self.canvas = tk.Canvas(body, bg="#f3f5f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.cards = tk.Frame(self.canvas, bg="#f3f5f8")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards, anchor="nw")
        self.cards.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-event.delta / 120), "units"))

        footer = tk.Frame(self, bg="#e7ebf0")
        footer.pack(fill="x", side="bottom")
        self.spam_button = ttk.Button(footer, text="Posible spam: 0", command=self._show_candidates)
        self.spam_button.pack(side="left", padx=20, pady=9)
        self.status_var = tk.StringVar(value="Añade una cuenta para empezar.")
        tk.Label(footer, textvariable=self.status_var, bg="#e7ebf0", fg="#3f5365", anchor="w").pack(side="left", fill="x", expand=True, padx=10)

    def _toggle_startup(self):
        try:
            set_startup(self.start_var.get())
        except OSError as exc:
            self.start_var.set(startup_enabled())
            messagebox.showerror("Inicio automático", str(exc), parent=self)

    def _run(self, operation, completed, *, status: str):
        if self.busy:
            self.status_var.set("Espera a que termine la operación actual.")
            return
        self.busy = True
        self.status_var.set(status)

        def worker():
            try:
                value = operation()
                self.events.put(("done", completed, value))
            except Exception as exc:
                self.events.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_events(self):
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "status":
                self.status_var.set(event[1])
            elif event[0] == "error":
                self.busy = False
                self.status_var.set("La operación falló.")
                messagebox.showerror("CoMa", event[1], parent=self)
            else:
                self.busy = False
                event[1](event[2])
        self.after(100, self._drain_events)

    def refresh(self):
        self._run(self.service.sync, self._synced, status="Sincronizando cuentas…")

    def _synced(self, result):
        self.messages, errors = result
        self.candidates = self.service.possible_spam(self.messages)
        self.spam_button.configure(text=f"Posible spam: {len(self.candidates)}")
        self.count_var.set(f"{len(self.messages)} correos no leídos")
        self._render_messages()
        self.status_var.set("Sincronización terminada." if not errors else " | ".join(errors)[:240])
        if self.candidate_window and self.candidate_window.winfo_exists():
            self._fill_candidates()

    def _render_messages(self):
        for widget in self.cards.winfo_children():
            widget.destroy()
        if not self.messages:
            tk.Label(self.cards, text="No hay mensajes no leídos o todavía no has añadido ninguna cuenta.",
                     font=("Segoe UI", 12), bg="#f3f5f8", fg="#526476").pack(pady=40)
            return
        for message in self.messages:
            card = tk.Frame(self.cards, bg="white", highlightbackground="#dce2e9", highlightthickness=1)
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(1, weight=1)
            button = ttk.Button(card, text="Abrir web", command=lambda item=message: self._open(item))
            button.grid(row=0, column=0, rowspan=4, padx=(12, 10), pady=12)
            if not message.web_link:
                button.state(["disabled"])
            tk.Label(card, text=f"{message.account_email}  ·  {message.sender}", bg="white", fg="#526476",
                     font=("Segoe UI", 9), anchor="w").grid(row=0, column=1, sticky="ew", pady=(10, 1))
            tk.Label(card, text=message.subject, bg="white", fg="#17324d", font=("Segoe UI", 11, "bold"),
                     anchor="w").grid(row=1, column=1, sticky="ew")
            tk.Label(card, text=message.summary, bg="white", fg="#3f5365", font=("Segoe UI", 9),
                     anchor="w", justify="left", wraplength=490).grid(row=2, column=1, sticky="ew", pady=(2, 10))
            ttk.Button(card, text="No es spam", command=lambda item=message: self._mark_ham(item)).grid(row=3, column=1, sticky="w", pady=(0, 8))
            buttons = tk.Frame(card, bg="white")
            buttons.grid(row=0, column=2, rowspan=4, padx=8)
            for title, action in ACTIONS:
                ttk.Button(buttons, text=title, command=lambda item=message, kind=action: self._act(item, kind)).pack(side="left", padx=2)

    def _open(self, message: Message):
        if message.web_link and not webbrowser.open(message.web_link):
            messagebox.showerror("Abrir correo", "No se pudo abrir el navegador.", parent=self)

    def _act(self, message: Message, action: str):
        def completed(_):
            self.status_var.set("Acción aplicada en el proveedor.")
            self.refresh()
        self._run(lambda: self.service.action(message, action), completed, status="Aplicando acción…")

    def _mark_ham(self, message: Message):
        self.service.not_spam(message)
        self.candidates = self.service.possible_spam(self.messages)
        self.spam_button.configure(text=f"Posible spam: {len(self.candidates)}")
        if self.candidate_window and self.candidate_window.winfo_exists():
            self._fill_candidates()
        self.status_var.set("Corrección guardada: no es spam.")

    def _add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Añadir cuenta")
        dialog.geometry("530x330")
        dialog.transient(self)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Proveedor").grid(row=0, column=0, sticky="w", pady=5)
        provider = tk.StringVar(value="Gmail")
        ttk.Combobox(frame, textvariable=provider, values=list(PROVIDERS), state="readonly", width=39).grid(row=0, column=1, sticky="ew")
        ttk.Label(frame, text="ID de aplicación OAuth").grid(row=1, column=0, sticky="w", pady=5)
        client_id = ttk.Entry(frame, width=42)
        client_id.grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text="Secreto de Google (si procede)").grid(row=2, column=0, sticky="w", pady=5)
        secret = ttk.Entry(frame, show="•")
        secret.grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="Tenant Microsoft").grid(row=3, column=0, sticky="w", pady=5)
        tenant = ttk.Entry(frame)
        tenant.insert(0, "common")
        tenant.grid(row=3, column=1, sticky="ew")
        def change(*_):
            tenant.delete(0, "end")
            tenant.insert(0, "organizations" if provider.get() == "Educacyl" else "common")
        provider.trace_add("write", change)
        ttk.Label(frame, text="Necesitas registrar una aplicación de escritorio en Google Cloud o Microsoft Entra.\nCoMa abrirá el navegador para que autorices la cuenta. Los tokens se guardan cifrados\npara tu usuario de Windows. Educacyl puede requerir aprobación de su administrador.",
                  justify="left", wraplength=470).grid(row=4, column=0, columnspan=2, sticky="w", pady=14)
        def submit():
            cid = client_id.get().strip()
            if not cid:
                messagebox.showerror("Añadir cuenta", "Introduce el ID de aplicación OAuth.", parent=dialog)
                return
            kind = PROVIDERS[provider.get()]
            secret_value = secret.get()
            tenancy = tenant.get().strip() if kind != "gmail" else "common"
            if kind != "gmail" and (not tenancy or "/" in tenancy):
                messagebox.showerror("Añadir cuenta", "Indica un tenant de Microsoft válido.", parent=dialog)
                return
            dialog.grab_release()
            dialog.destroy()
            self._run(lambda: self.service.add_account(kind, cid, tenancy, secret_value,
                            lambda text: self.events.put(("status", text))),
                      lambda account: self._added(account), status="Iniciando autorización…")
        ttk.Button(frame, text="Conectar cuenta", command=submit, style="Accent.TButton").grid(row=5, column=1, sticky="e")

    def _added(self, account):
        self.status_var.set(f"Cuenta {account.email} añadida.")
        self.refresh()

    def _remove_dialog(self):
        accounts = self.service.accounts.list()
        if not accounts:
            messagebox.showinfo("Cuentas", "No hay cuentas configuradas.", parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title("Quitar cuenta")
        dialog.geometry("440x270")
        dialog.transient(self)
        dialog.grab_set()
        items = tk.Listbox(dialog)
        items.pack(fill="both", expand=True, padx=15, pady=12)
        for account in accounts:
            items.insert("end", f"{account.email} ({account.provider})")
        def remove():
            selection = items.curselection()
            if not selection:
                return
            self.service.accounts.remove(accounts[selection[0]].id)
            dialog.grab_release()
            dialog.destroy()
            self.refresh()
        ttk.Button(dialog, text="Quitar cuenta seleccionada", command=remove).pack(pady=(0, 12))

    def _show_candidates(self):
        if self.candidate_window and self.candidate_window.winfo_exists():
            self.candidate_window.lift()
            return
        self.candidate_window = tk.Toplevel(self)
        self.candidate_window.title("Posible spam")
        self.candidate_window.geometry("680x390")
        self.candidate_list = tk.Listbox(self.candidate_window)
        self.candidate_list.pack(fill="both", expand=True, padx=15, pady=(15, 8))
        self.candidate_list.bind("<<ListboxSelect>>", self._candidate_selected)
        self.candidate_summary = tk.StringVar(value="Selecciona un mensaje para ver su resumen.")
        tk.Label(self.candidate_window, textvariable=self.candidate_summary, wraplength=640,
                 justify="left", anchor="w").pack(fill="x", padx=15, pady=6)
        ttk.Button(self.candidate_window, text="No es spam", command=self._correct_candidate).pack(anchor="e", padx=15, pady=12)
        self._fill_candidates()

    def _fill_candidates(self):
        self.candidate_list.delete(0, "end")
        for message in self.candidates:
            self.candidate_list.insert("end", f"{message.sender} · {message.subject}")
        self.candidate_summary.set("Selecciona un mensaje para ver su resumen.")

    def _candidate_selected(self, _event):
        selection = self.candidate_list.curselection()
        if selection:
            self.candidate_summary.set(self.candidates[selection[0]].summary)

    def _correct_candidate(self):
        selection = self.candidate_list.curselection()
        if not selection:
            return
        message = self.candidates[selection[0]]
        self.service.not_spam(message)
        self.candidates = self.service.possible_spam(self.messages)
        self.spam_button.configure(text=f"Posible spam: {len(self.candidates)}")
        self._fill_candidates()
        self.status_var.set("Corrección guardada: no es spam.")
