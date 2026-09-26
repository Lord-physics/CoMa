"""Ventana Tk; toda red y clasificación se ejecutan fuera del hilo gráfico."""

import base64
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

from .i18n import HELP_URLS, help_text, language, load_language, set_language, tr
from .models import Message
from .service import MailService
from .startup import enabled as startup_enabled, set_enabled as set_startup


PROVIDERS = {"Gmail": "gmail", "Outlook / Hotmail": "outlook", "Educacyl": "educacyl"}
ACTIONS = ("archive", "delete", "spam", "spam_delete")
COLORS = {
    "background": "#FDFAED",
    "surface": "#FFFEFA",
    "footer": "#E9EAF4",
    "border": "#DDD8CF",
    "accent": "#7F8FB8",
    "accent_active": "#6879A5",
    "text": "#453D47",
    "muted": "#766E7C",
    "body": "#5A5360",
}


def _asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "coma" / "assets" / name
    return Path(__file__).resolve().parent / "assets" / name


class App(tk.Tk):
    def __init__(self, service: MailService | None = None):
        super().__init__()
        load_language()
        self.service = service or MailService()
        self.title(tr("window_title"))
        self.geometry("1120x720")
        self.minsize(820, 500)
        self.configure(bg=COLORS["background"])
        self.events = queue.Queue()
        self.busy = False
        self.messages: list[Message] = []
        self.candidates: list[Message] = []
        self.candidate_window = None
        self.logo_image = tk.PhotoImage(data=base64.b64encode(_asset_path("logo.png").read_bytes())).subsample(24, 24)
        self.iconphoto(True, self.logo_image)
        self._style()
        self._layout()
        self.after(100, self._drain_events)
        self.after(300, self.refresh)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=(9, 6), background=COLORS["surface"], foreground=COLORS["text"])
        style.map("TButton", background=[("active", COLORS["footer"])])
        style.configure("Accent.TButton", padding=(10, 7), background=COLORS["accent"], foreground="white")
        style.map("Accent.TButton", background=[("active", COLORS["accent_active"])])
        style.configure("TCheckbutton", background=COLORS["background"], foreground=COLORS["text"])

    def _layout(self):
        header = tk.Frame(self, bg=COLORS["background"])
        header.pack(fill="x", padx=20, pady=(18, 10))
        tk.Label(header, image=self.logo_image, bg=COLORS["background"]).pack(side="left", padx=(0, 9))
        tk.Label(header, text="CoMa", font=("Segoe UI", 23, "bold"), bg=COLORS["background"], fg=COLORS["text"]).pack(side="left")
        tk.Label(header, text=tr("inbox"), font=("Segoe UI", 12), bg=COLORS["background"], fg=COLORS["muted"]).pack(side="left", pady=(10, 0))
        ttk.Button(header, text=tr("add_account"), command=self._add_dialog).pack(side="right", padx=(7, 0))
        ttk.Button(header, text=tr("remove_account"), command=self._remove_dialog).pack(side="right", padx=(7, 0))
        ttk.Button(header, text=tr("refresh"), command=self.refresh, style="Accent.TButton").pack(side="right")

        controls = tk.Frame(self, bg=COLORS["background"])
        controls.pack(fill="x", padx=20, pady=(0, 8))
        self.start_var = tk.BooleanVar(value=startup_enabled())
        ttk.Checkbutton(controls, text=tr("autostart"), variable=self.start_var,
                        command=self._toggle_startup).pack(side="left")
        self.count_var = tk.StringVar(value=tr("no_messages_loaded"))
        tk.Label(controls, textvariable=self.count_var, bg=COLORS["background"], fg=COLORS["muted"]).pack(side="right")
        self.language_choice = tk.StringVar(value="English" if language() == "en" else "Español")
        picker = ttk.Combobox(controls, textvariable=self.language_choice, values=("Español", "English"),
                              state="readonly", width=10)
        picker.pack(side="right", padx=(8, 18))
        picker.bind("<<ComboboxSelected>>", self._change_language)
        tk.Label(controls, text=tr("language"), bg=COLORS["background"], fg=COLORS["muted"]).pack(side="right")

        body = tk.Frame(self, bg=COLORS["background"])
        body.pack(fill="both", expand=True, padx=20)
        self.canvas = tk.Canvas(body, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.cards = tk.Frame(self.canvas, bg=COLORS["background"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards, anchor="nw")
        self.cards.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-event.delta / 120), "units"))

        footer = tk.Frame(self, bg=COLORS["footer"])
        footer.pack(fill="x", side="bottom")
        self.spam_button = ttk.Button(footer, text=tr("possible_spam", count=0), command=self._show_candidates)
        self.spam_button.pack(side="left", padx=20, pady=9)
        self.status_var = tk.StringVar(value=tr("ready"))
        tk.Label(footer, textvariable=self.status_var, bg=COLORS["footer"], fg=COLORS["body"], anchor="w").pack(side="left", fill="x", expand=True, padx=10)

    def _change_language(self, _event):
        selected = "en" if self.language_choice.get() == "English" else "es"
        try:
            set_language(selected)
        except OSError as exc:
            messagebox.showerror("CoMa", str(exc), parent=self)
            self.language_choice.set("English" if language() == "en" else "Español")
            return
        if self.candidate_window and self.candidate_window.winfo_exists():
            self.candidate_window.destroy()
        self.candidate_window = None
        for widget in self.winfo_children():
            widget.destroy()
        self.title(tr("window_title"))
        self._layout()
        self.spam_button.configure(text=tr("possible_spam", count=len(self.candidates)))
        if self.messages:
            self.count_var.set(tr("unread_count", count=len(self.messages)))
        self._render_messages()
        self.status_var.set(tr("lang_changed"))

    def _toggle_startup(self):
        try:
            set_startup(self.start_var.get())
        except OSError as exc:
            self.start_var.set(startup_enabled())
            messagebox.showerror(tr("autostart_title"), str(exc), parent=self)

    def _run(self, operation, completed, *, status: str, refresh_on_error: bool = False):
        if self.busy:
            self.status_var.set(tr("busy"))
            return
        self.busy = True
        self.status_var.set(status)

        def worker():
            try:
                value = operation()
                self.events.put(("done", completed, value))
            except Exception as exc:
                self.events.put(("error", str(exc), refresh_on_error))

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
                self.status_var.set(tr("operation_failed"))
                messagebox.showerror("CoMa", event[1], parent=self)
                if event[2]:
                    self.refresh()
            else:
                self.busy = False
                event[1](event[2])
        self.after(100, self._drain_events)

    def refresh(self):
        self._run(self.service.sync, self._synced, status=tr("syncing"))

    def _synced(self, result):
        self.messages, errors = result
        self.candidates = self.service.possible_spam(self.messages)
        self.spam_button.configure(text=tr("possible_spam", count=len(self.candidates)))
        self.count_var.set(tr("unread_count", count=len(self.messages)))
        self._render_messages()
        self.status_var.set(tr("sync_done") if not errors else " | ".join(errors)[:240])
        if self.candidate_window and self.candidate_window.winfo_exists():
            self._fill_candidates()

    def _render_messages(self):
        for widget in self.cards.winfo_children():
            widget.destroy()
        if not self.messages:
            tk.Label(self.cards, text=tr("no_unread"),
                     font=("Segoe UI", 12), bg=COLORS["background"], fg=COLORS["muted"]).pack(pady=40)
            return
        for message in self.messages:
            card = tk.Frame(self.cards, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(1, weight=1)
            button = ttk.Button(card, text=tr("open_web"), command=lambda item=message: self._open(item))
            button.grid(row=0, column=0, rowspan=4, padx=(12, 10), pady=12)
            if not message.web_link:
                button.state(["disabled"])
            tk.Label(card, text=f"{message.account_email}  ·  {message.sender}", bg=COLORS["surface"], fg=COLORS["muted"],
                     font=("Segoe UI", 9), anchor="w").grid(row=0, column=1, sticky="ew", pady=(10, 1))
            tk.Label(card, text=message.subject, bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 11, "bold"),
                     anchor="w").grid(row=1, column=1, sticky="ew")
            tk.Label(card, text=message.summary, bg=COLORS["surface"], fg=COLORS["body"], font=("Segoe UI", 9),
                     anchor="w", justify="left", wraplength=490).grid(row=2, column=1, sticky="ew", pady=(2, 10))
            ttk.Button(card, text=tr("not_spam"), command=lambda item=message: self._mark_ham(item)).grid(row=3, column=1, sticky="w", pady=(0, 8))
            buttons = tk.Frame(card, bg=COLORS["surface"])
            buttons.grid(row=0, column=2, rowspan=4, padx=8)
            for action in ACTIONS:
                ttk.Button(buttons, text=tr(action), command=lambda item=message, kind=action: self._act(item, kind)).pack(side="left", padx=2)

    def _open(self, message: Message):
        if message.web_link and not webbrowser.open(message.web_link):
            messagebox.showerror(tr("open_mail"), tr("browser_failed"), parent=self)

    def _act(self, message: Message, action: str):
        def completed(_):
            self.status_var.set(tr("action_done"))
            self.refresh()
        self._run(lambda: self.service.action(message, action), completed,
                  status=tr("applying"), refresh_on_error=True)

    def _mark_ham(self, message: Message):
        self.service.not_spam(message)
        self.candidates = self.service.possible_spam(self.messages)
        self.spam_button.configure(text=tr("possible_spam", count=len(self.candidates)))
        if self.candidate_window and self.candidate_window.winfo_exists():
            self._fill_candidates()
        self.status_var.set(tr("correction_saved"))

    def _add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title(tr("add_account"))
        dialog.geometry("570x315")
        dialog.transient(self)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(1, weight=1)
        ttk.Label(frame, text=tr("provider")).grid(row=0, column=0, sticky="w", pady=5)
        provider = tk.StringVar(value="Gmail")
        ttk.Combobox(frame, textvariable=provider, values=list(PROVIDERS), state="readonly", width=39).grid(row=0, column=1, sticky="ew")
        ttk.Label(frame, text=tr("client_id")).grid(row=1, column=0, sticky="w", pady=5)
        client_id = ttk.Entry(frame, width=42)
        client_id.grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text=tr("google_secret")).grid(row=2, column=0, sticky="w", pady=5)
        secret = ttk.Entry(frame, show="•")
        secret.grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text=tr("microsoft_tenant")).grid(row=3, column=0, sticky="w", pady=5)
        tenant = ttk.Entry(frame)
        tenant.insert(0, "common")
        tenant.grid(row=3, column=1, sticky="ew")
        def change(*_):
            tenant.delete(0, "end")
            tenant.insert(0, "organizations" if provider.get() == "Educacyl" else "common")
        provider.trace_add("write", change)
        ttk.Label(frame, text=tr("account_hint"),
                  justify="left", wraplength=470).grid(row=4, column=0, columnspan=2, sticky="w", pady=14)
        def submit():
            cid = client_id.get().strip()
            if not cid:
                messagebox.showerror(tr("add_account"), tr("missing_client_id"), parent=dialog)
                return
            kind = PROVIDERS[provider.get()]
            secret_value = secret.get()
            tenancy = tenant.get().strip() if kind != "gmail" else "common"
            if kind != "gmail" and (not tenancy or "/" in tenancy):
                messagebox.showerror(tr("add_account"), tr("invalid_tenant"), parent=dialog)
                return
            dialog.grab_release()
            dialog.destroy()
            self._run(lambda: self.service.add_account(kind, cid, tenancy, secret_value,
                            lambda text: self.events.put(("status", text))),
                      lambda account: self._added(account), status=tr("authorizing"))
        ttk.Button(frame, text=tr("help"), command=lambda: self._account_help(dialog, PROVIDERS[provider.get()], provider.get())).grid(row=5, column=0, sticky="w")
        ttk.Button(frame, text=tr("connect"), command=submit, style="Accent.TButton").grid(row=5, column=1, sticky="e")

    def _account_help(self, parent, kind: str, provider_name: str):
        help_window = tk.Toplevel(parent)
        help_window.title(tr("help_title", provider=provider_name))
        help_window.geometry("690x510")
        help_window.minsize(520, 350)
        help_window.transient(parent)
        help_window.grab_set()
        frame = ttk.Frame(help_window, padding=16)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word", font=("Segoe UI", 10), padx=12, pady=12,
                       bg=COLORS["surface"], fg=COLORS["text"])
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", help_text(kind))
        text.configure(state="disabled")
        buttons = ttk.Frame(help_window, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        ttk.Button(buttons, text=tr("open_instructions"),
                   command=lambda: webbrowser.open(HELP_URLS[kind])).pack(side="left")
        def close():
            help_window.grab_release()
            help_window.destroy()
            parent.grab_set()
        ttk.Button(buttons, text=tr("close"), command=close).pack(side="right")
        help_window.protocol("WM_DELETE_WINDOW", close)

    def _added(self, account):
        self.status_var.set(tr("account_added", email=account.email))
        self.refresh()

    def _remove_dialog(self):
        accounts = self.service.accounts.list()
        if not accounts:
            messagebox.showinfo(tr("accounts"), tr("no_accounts"), parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title(tr("remove_account"))
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
        ttk.Button(dialog, text=tr("remove_selected"), command=remove).pack(pady=(0, 12))

    def _show_candidates(self):
        if self.candidate_window and self.candidate_window.winfo_exists():
            self.candidate_window.lift()
            return
        self.candidate_window = tk.Toplevel(self)
        self.candidate_window.title(tr("possible_spam", count=len(self.candidates)))
        self.candidate_window.geometry("680x390")
        self.candidate_list = tk.Listbox(self.candidate_window)
        self.candidate_list.pack(fill="both", expand=True, padx=15, pady=(15, 8))
        self.candidate_list.bind("<<ListboxSelect>>", self._candidate_selected)
        self.candidate_summary = tk.StringVar(value=tr("select_summary"))
        tk.Label(self.candidate_window, textvariable=self.candidate_summary, wraplength=640,
                 justify="left", anchor="w").pack(fill="x", padx=15, pady=6)
        ttk.Button(self.candidate_window, text=tr("not_spam"), command=self._correct_candidate).pack(anchor="e", padx=15, pady=12)
        self._fill_candidates()

    def _fill_candidates(self):
        self.candidate_list.delete(0, "end")
        for message in self.candidates:
            self.candidate_list.insert("end", f"{message.sender} · {message.subject}")
        self.candidate_summary.set(tr("select_summary"))

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
        self.spam_button.configure(text=tr("possible_spam", count=len(self.candidates)))
        self._fill_candidates()
        self.status_var.set(tr("correction_saved"))
