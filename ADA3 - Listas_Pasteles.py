# -*- coding: utf-8 -*-
"""
POSTRES: arreglo ordenado + lista ligada de ingredientes por postre
Python 3 + Tkinter (viene incluido, no hay que instalar nada).
Ejecutar:  python postres.py

ESTRUCTURA (igual al dibujo del ejercicio)
    POSTRES = [ Postre("Brownie") --> Nodo --> Nodo --> NIL,
                Postre("Flan")    --> Nodo --> NIL, ... ]
  - El arreglo se mantiene ORDENADO alfabéticamente (búsqueda binaria).
  - Cada ingrediente es un Nodo(dato, sig). sig = None equivale a NIL.

VALIDACIONES (entrada)
  - Nombres: solo letras (con acentos y ñ), espacios, guion (-) y apóstrofo (').
    NO se aceptan números ni símbolos; se bloquean al teclear/pegar y se
    vuelven a validar al ejecutar la operación.
  - Largo máximo 24 por nombre, mínimo 2 letras, máximo 10 ingredientes por postre.
  - Vacíos, comas de más, guiones mal puestos, repetidos (sin importar
    mayúsculas ni acentos), arreglo lleno/vacío, postre inexistente, etc.
  - Cada operación es "todo o nada": si hay un error, no se modifica nada.
VALIDACIONES (salida)
  - Nada se recorta con "…": los textos largos se ajustan en varias líneas.
  - Errores inesperados se muestran en un mensaje en vez de cerrar el programa.
"""
import re
import unicodedata
import tkinter as tk
from tkinter import messagebox, ttk

CAPACIDAD = 12     # tamaño del arreglo (así existe el caso "arreglo lleno")
MAX_NOMBRE = 24    # largo máximo de un nombre (postre o ingrediente)
MAX_ING = 10       # ingredientes máximos por postre

LETRAS = "A-Za-zÀ-ÖØ-öø-ÿ"            # letras latinas con acentos, ñ, ü...
UNA_LETRA = re.compile(f"[{LETRAS}]")
PATRON = re.compile(f"[{LETRAS}]+(?:[ '-][{LETRAS}]+)*")
SEPARADORES = " '-"


# =====================  LÓGICA (estructuras de datos)  =====================
class ErrorPostre(Exception):
    """Errores controlados: se muestran al usuario como mensaje."""


def clave(texto):
    """Clave de comparación: sin mayúsculas ni acentos (la ñ se conserva)."""
    t = texto.casefold().replace("ñ", "n{")
    t = unicodedata.normalize("NFD", t)
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn")


def validar_nombre(texto, etiqueta):
    """Valida y normaliza un nombre. Lanza ErrorPostre con el motivo exacto."""
    t = " ".join(unicodedata.normalize("NFC", texto).split())
    if not t:
        raise ErrorPostre(f"El {etiqueta} no puede estar vacío.")
    if any(ch.isdigit() for ch in t):
        raise ErrorPostre(f"El {etiqueta} no puede llevar números: «{t}».")
    for ch in t:
        if not (UNA_LETRA.fullmatch(ch) or ch in SEPARADORES):
            raro = ch if ch.isprintable() else "(carácter especial)"
            raise ErrorPostre(f"El {etiqueta} tiene un carácter no permitido: «{raro}». "
                              "Solo letras, espacios, guion (-) y apóstrofo (').")
    if len(UNA_LETRA.findall(t)) < 2:
        raise ErrorPostre(f"El {etiqueta} «{t}» es demasiado corto (mínimo 2 letras).")
    if len(t) > MAX_NOMBRE:
        raise ErrorPostre(f"El {etiqueta} «{t}» es demasiado largo ({len(t)} caracteres; máximo {MAX_NOMBRE}).")
    if not PATRON.fullmatch(t):
        raise ErrorPostre(f"El {etiqueta} «{t}» tiene guiones o apóstrofos mal colocados "
                          "(deben ir entre letras).")
    return t[:1].upper() + t[1:].lower()


def parsear_ingredientes(texto):
    """'leche, huevo' -> ['Leche', 'Huevo']. Vacío -> []."""
    if not texto.strip():
        return []
    partes = texto.split(",")
    if any(not p.strip() for p in partes):
        raise ErrorPostre("Hay comas de más o ingredientes vacíos "
                          "(ej.: «Leche, , Huevo» o una coma al final).")
    ings = [validar_nombre(p, "ingrediente") for p in partes]
    if len(ings) > MAX_ING:
        raise ErrorPostre(f"Escribiste {len(ings)} ingredientes; el máximo por postre es {MAX_ING}.")
    return ings


def razon_rechazo(texto, permitir_coma=False):
    """Filtro mientras se teclea/pega. Devuelve el motivo o None si es válido."""
    for ch in texto:
        if ch.isdigit():
            return "Números no permitidos"
        if not (UNA_LETRA.fullmatch(ch) or ch in SEPARADORES or (permitir_coma and ch == ",")):
            return f"Carácter no permitido: «{ch if ch.isprintable() else 'especial'}»"
    partes = texto.split(",") if permitir_coma else [texto]
    if len(partes) > MAX_ING:
        return f"Máximo {MAX_ING} ingredientes"
    if any(len(p.strip()) > MAX_NOMBRE for p in partes):
        return f"Máximo {MAX_NOMBRE} caracteres por nombre"
    return None


def separar_repetidos(lista):
    """Devuelve (únicos, repetidos) ignorando mayúsculas y acentos."""
    vistos, unicos, repetidos = set(), [], []
    for x in lista:
        (repetidos if clave(x) in vistos else unicos).append(x)
        vistos.add(clave(x))
    return unicos, repetidos


class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.sig = None  # None == NIL


class ListaIngredientes:
    """Lista ligada simple de ingredientes (sin repetidos)."""

    def __init__(self):
        self.cabeza = None

    def __len__(self):
        n, act = 0, self.cabeza
        while act:
            n, act = n + 1, act.sig
        return n

    def buscar(self, dato):
        k, act = clave(dato), self.cabeza
        while act:
            if clave(act.dato) == k:
                return act
            act = act.sig
        return None

    def agregar(self, dato):
        """Inserta al final. Devuelve False si ya existía."""
        if self.buscar(dato):
            return False
        nuevo = Nodo(dato)
        if not self.cabeza:
            self.cabeza = nuevo
        else:
            act = self.cabeza
            while act.sig:
                act = act.sig
            act.sig = nuevo
        return True

    def eliminar(self, dato):
        """Quita el nodo (primero, intermedio o último). False si no estaba."""
        k, ant, act = clave(dato), None, self.cabeza
        while act and clave(act.dato) != k:
            ant, act = act, act.sig
        if not act:
            return False
        if ant:
            ant.sig = act.sig
        else:
            self.cabeza = act.sig
        return True

    def elementos(self):
        out, act = [], self.cabeza
        while act:
            out.append(act.dato)
            act = act.sig
        return out

    def vaciar(self):
        self.cabeza = None  # los nodos quedan sin referencia (huérfanos)


class Postre:
    def __init__(self, nombre):
        self.nombre = nombre
        self.ingredientes = ListaIngredientes()


class Recetario:
    """El arreglo POSTRES, siempre ordenado por nombre."""

    def __init__(self):
        self.postres = []

    def _lower_bound(self, nombre):  # búsqueda binaria
        k, lo, hi = clave(nombre), 0, len(self.postres)
        while lo < hi:
            mid = (lo + hi) // 2
            if clave(self.postres[mid].nombre) < k:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def buscar(self, nombre):
        i = self._lower_bound(nombre)
        if i < len(self.postres) and clave(self.postres[i].nombre) == clave(nombre):
            return self.postres[i]
        return None

    def cuantos(self, nombre):
        k = clave(nombre)
        return sum(1 for p in self.postres if clave(p.nombre) == k)

    def obtener(self, nombre):
        nombre = validar_nombre(nombre, "nombre del postre")
        if not self.postres:
            raise ErrorPostre("El arreglo está vacío: todavía no hay postres.")
        p = self.buscar(nombre)
        if not p:
            raise ErrorPostre(f"El postre «{nombre}» no existe.")
        return p

    # ---- a) consultar ----
    def ingredientes(self, nombre):
        return self.obtener(nombre).ingredientes.elementos()

    # ---- b) insertar ingredientes (todo o nada) ----
    def agregar_ingredientes(self, nombre, ings):
        p = self.obtener(nombre)
        if not ings:
            raise ErrorPostre("Escribe al menos un ingrediente (separados por comas).")
        ings, rep_entrada = separar_repetidos([validar_nombre(i, "ingrediente") for i in ings])
        nuevos = [i for i in ings if not p.ingredientes.buscar(i)]
        repetidos = rep_entrada + [i for i in ings if i not in nuevos]
        if not nuevos:
            raise ErrorPostre(f"Todos esos ingredientes ya están en «{p.nombre}».")
        total = len(p.ingredientes) + len(nuevos)
        if total > MAX_ING:
            raise ErrorPostre(f"«{p.nombre}» quedaría con {total} ingredientes y el máximo es {MAX_ING}. "
                              "Quita alguno primero.")
        for i in nuevos:
            p.ingredientes.agregar(i)
        return p, nuevos, repetidos

    # ---- c) eliminar ingredientes ----
    def quitar_ingredientes(self, nombre, ings):
        p = self.obtener(nombre)
        if not ings:
            raise ErrorPostre("Escribe el ingrediente que quieres quitar.")
        ings, _ = separar_repetidos([validar_nombre(i, "ingrediente") for i in ings])
        if p.ingredientes.cabeza is None:
            raise ErrorPostre(f"«{p.nombre}» no tiene ingredientes (su lista ya es NIL).")
        quitados = [i for i in ings if p.ingredientes.eliminar(i)]
        no_estaban = [i for i in ings if i not in quitados]
        if not quitados:
            raise ErrorPostre(f"Ese ingrediente no está en la lista de «{p.nombre}».")
        return p, quitados, no_estaban

    # ---- d) alta (todo o nada) ----
    def alta(self, nombre, ings, permitir_repetido=False):
        nombre = validar_nombre(nombre, "nombre del postre")
        if not ings:
            raise ErrorPostre("Un postre necesita al menos un ingrediente (sepáralos con comas).")
        ings, ignorados = separar_repetidos([validar_nombre(i, "ingrediente") for i in ings])
        if len(ings) > MAX_ING:
            raise ErrorPostre(f"Máximo {MAX_ING} ingredientes por postre.")
        if len(self.postres) >= CAPACIDAD:
            raise ErrorPostre(f"El arreglo está lleno ({CAPACIDAD} postres). Da de baja alguno primero.")
        i = self._lower_bound(nombre)
        existe = i < len(self.postres) and clave(self.postres[i].nombre) == clave(nombre)
        if existe and not permitir_repetido:
            raise ErrorPostre(f"«{nombre}» ya existe. Usa «Agregar ingrediente(s)» para modificarlo.")
        while i < len(self.postres) and clave(self.postres[i].nombre) == clave(nombre):
            i += 1  # el repetido queda junto al original
        p = Postre(nombre)
        for x in ings:
            p.ingredientes.agregar(x)
        self.postres.insert(i, p)  # se recorren los demás para mantener el orden
        return p, ignorados

    # ---- e) baja ----
    def baja(self, nombre):
        p = self.obtener(nombre)
        self.postres.pop(self._lower_bound(p.nombre))
        lista = p.ingredientes.elementos()
        p.ingredientes.vaciar()
        return p, lista, self.cuantos(p.nombre)

    # ---- ejercicio 2: eliminar repetidos ----
    def hay_repetidos(self):
        return any(clave(a.nombre) == clave(b.nombre)
                   for a, b in zip(self.postres, self.postres[1:]))

    def eliminar_repetidos(self, fusionar):
        """Una sola pasada: al estar ordenado, los repetidos son vecinos."""
        nuevo, reporte = [], []
        for p in self.postres:
            if nuevo and clave(nuevo[-1].nombre) == clave(p.nombre):
                base, ings = nuevo[-1], p.ingredientes.elementos()
                if fusionar:
                    pasan = [x for x in ings if base.ingredientes.agregar(x)]
                    reporte.append(f"«{p.nombre}» repetido: su lista se fusionó con la original "
                                   f"(se sumaron: {', '.join(pasan) or 'nada nuevo'}).")
                else:
                    perdidos = [x for x in ings if not base.ingredientes.buscar(x)]
                    reporte.append(f"«{p.nombre}» repetido: su lista se descartó "
                                   f"(ingredientes perdidos: {', '.join(perdidos) or 'ninguno, ya estaban en la original'}).")
                p.ingredientes.vaciar()
            else:
                nuevo.append(p)
        self.postres = nuevo
        return reporte


# =====================  INTERFAZ GRÁFICA  =====================
BG, ROSA, CAFE, BORDE, GRIS = "#FFF8F3", "#EC6A9C", "#4E342E", "#F3C9D8", "#A1887F"
GLASEADOS = ["#F48FB1", "#CE93D8", "#90CAF9", "#A5D6A7", "#FFCC80", "#FFF59D"]

EJEMPLO = [
    ("Brownie", ["Chocolate", "Harina", "Huevo", "Mantequilla", "Azúcar"]),
    ("Cheesecake", ["Queso crema", "Galletas", "Azúcar", "Huevo"]),
    ("Flan", ["Leche", "Huevo", "Azúcar", "Vainilla"]),
    ("Marquesita", ["Queso de bola", "Cajeta", "Masa de crepa"]),
    ("Tiramisú", ["Café", "Mascarpone", "Cacao", "Soletas"]),
    ("Tres leches", ["Leche evaporada", "Leche condensada", "Crema", "Harina", "Huevo"]),
]


def shade(hex_color, f):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(v * f)) for v in (r, g, b))


def cupcake(c, x, y, s=1.0, color="#F48FB1", tags=()):
    """Dibuja un cupcake (aprox. 40s x 50s px) con figuras del Canvas."""
    P = lambda dx, dy: (x + dx * s, y + (dy + 4) * s)
    c.create_polygon(*P(6, 26), *P(34, 26), *P(30, 46), *P(10, 46),
                     fill="#E8B36B", outline="#A9742F", tags=tags)
    for dx in (15, 20, 25):
        c.create_line(*P(dx, 28), *P(20 + (dx - 20) * 0.7, 45), fill="#C98F45", tags=tags)
    borde = shade(color, 0.8)
    c.create_oval(*P(2, 14), *P(38, 30), fill=color, outline=borde, tags=tags)
    c.create_oval(*P(7, 7), *P(33, 21), fill=color, outline=borde, tags=tags)
    c.create_oval(*P(13, 1), *P(27, 12), fill=color, outline=borde, tags=tags)
    c.create_oval(*P(17, -3), *P(23, 3), fill="#D32F2F", outline="#9B1C1C", tags=tags)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Recetario de Postres · arreglo de listas ligadas")
        self.geometry("1120x730")
        self.minsize(980, 700)
        self.configure(bg=BG)
        self.rec = Recetario()
        self.sel = None
        self.sel_idx = None  # posición exacta elegida (por si hay nombres repetidos)
        self.permitir = tk.BooleanVar(value=False)
        self.v_postre, self.v_ing = tk.StringVar(), tk.StringVar()
        self.v_combo = tk.StringVar()
        self._timers = {}
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._estilo()
        self._header()
        self._panel_izq()
        self._panel_der()
        self.cargar_ejemplo(False, confirmar=False)

    # ---------- construcción de la ventana ----------
    def _header(self):
        h = self.hdr = tk.Canvas(self, height=76, bg=ROSA, highlightthickness=0)
        h.grid(row=0, column=0, columnspan=2, sticky="ew")
        cupcake(h, 20, 8, 1.3, "#FFF59D")
        h.create_text(92, 28, text="Recetario de Postres", anchor="w",
                      font=("Segoe UI", 21, "bold"), fill="white")
        h.create_text(94, 56, text="Arreglo ordenado + lista ligada de ingredientes · Python / Tkinter",
                      anchor="w", font=("Segoe UI", 10), fill="#FFE3EE")
        h.bind("<Configure>", self._deco)

    def _deco(self, e):
        self.hdr.delete("deco")
        for k, col in enumerate(GLASEADOS[:4]):
            cupcake(self.hdr, e.width - 70 - k * 62, 12, 1.0, col, tags=("deco",))

    def _card(self, padre, titulo):
        f = tk.Frame(padre, bg="white", highlightthickness=1, highlightbackground=BORDE)
        tk.Label(f, text=titulo, bg="white", fg=ROSA,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        f.pack(fill="x", pady=(0, 10))
        return f

    def _campo(self, padre, etiqueta, var, coma, ayuda):
        """Entry que rechaza números/símbolos al teclear o pegar y avisa por qué."""
        tk.Label(padre, text=etiqueta, bg="white", fg=CAFE, font=("Segoe UI", 10)).pack(anchor="w", padx=12)
        hint = tk.Label(padre, text=ayuda, bg="white", fg=GRIS, font=("Segoe UI", 8), anchor="w")
        hint.normal = ayuda
        vcmd = (self.register(lambda nuevo, h=hint, c=coma: self._valida(nuevo, c, h)), "%P")
        e = tk.Entry(padre, textvariable=var, validate="key", validatecommand=vcmd,
                     font=("Segoe UI", 11), relief="flat", bg="#FFF3F7", fg=CAFE,
                     highlightthickness=1, highlightbackground=BORDE, highlightcolor=ROSA,
                     insertbackground=CAFE)
        e.pack(fill="x", padx=12, pady=(0, 2), ipady=4)
        hint.pack(fill="x", padx=12, pady=(0, 6))
        return e

    def _valida(self, nuevo, coma, hint):
        razon = razon_rechazo(nuevo, coma)
        if razon is None:
            return True
        self.bell()
        hint.config(text="✖ " + razon, fg="#C62828")
        if hint in self._timers:
            self.after_cancel(self._timers[hint])
        self._timers[hint] = self.after(2500, lambda: hint.config(text=hint.normal, fg=GRIS))
        return False

    def _boton(self, padre, texto, color, cmd, font=("Segoe UI", 11, "bold"), anchor="w"):
        b = tk.Button(padre, text=texto, command=cmd, bg=color, fg=CAFE,
                      activebackground=shade(color, 0.88), relief="flat", bd=0,
                      font=font, cursor="hand2", pady=4, padx=12, anchor=anchor)
        b.bind("<Enter>", lambda e: b.config(bg=shade(color, 0.93)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def _panel_izq(self):
        izq = tk.Frame(self, bg=BG)
        izq.grid(row=1, column=0, sticky="n", padx=(14, 7), pady=12)

        datos = self._card(izq, "DATOS")
        fila_c = tk.Frame(datos, bg="white")
        fila_c.pack(fill="x", padx=12, pady=(0, 8))
        self.lbl_combo = tk.Label(fila_c, text="Elegir postre:", bg="white", fg=CAFE,
                                  font=("Segoe UI", 10, "bold"))
        self.lbl_combo.pack(side="left")
        self.combo = ttk.Combobox(fila_c, textvariable=self.v_combo, state="readonly",
                                  font=("Segoe UI", 11))
        self.combo.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.combo.bind("<<ComboboxSelected>>", self._elegir)
        e1 = self._campo(datos, "Postre", self.v_postre, False,
                         f"Solo letras, espacios, - y '  ·  máx. {MAX_NOMBRE} caracteres")
        e1.bind("<Return>", lambda e: self._run(self.op_ver))
        self._campo(datos, "Ingrediente(s)", self.v_ing, True,
                    f"Separa con comas  ·  sin números  ·  máx. {MAX_ING} ingredientes")

        ops = self._card(izq, "OPERACIONES")
        botones = [
            ("a)  Ver ingredientes", "#90CAF9", self.op_ver),
            ("b)  Agregar ingrediente(s)", "#A5D6A7", self.op_agregar),
            ("c)  Quitar ingrediente", "#FFCC80", self.op_quitar),
            ("d)  Alta de postre", "#80CBC4", self.op_alta),
            ("e)  Baja de postre", "#EF9A9A", self.op_baja),
            ("2)  Eliminar repetidos", "#CE93D8", self.op_dedup),
        ]
        for txt, col, fn in botones:
            self._boton(ops, txt, col, lambda f=fn: self._run(f)).pack(fill="x", padx=12, pady=3)
        tk.Checkbutton(ops, text="Permitir repetidos en el alta (para probar el ej. 2)",
                       variable=self.permitir, bg="white", fg=CAFE, activebackground="white",
                       font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=8, pady=(4, 2))
        fila = tk.Frame(ops, bg="white")
        fila.pack(fill="x", padx=12, pady=(2, 10))
        for k, (txt, fn) in enumerate([("Ejemplo", lambda: self.cargar_ejemplo(False)),
                                       ("Con repetidos", lambda: self.cargar_ejemplo(True)),
                                       ("Vaciar", self.vaciar)]):
            fila.columnconfigure(k, weight=1, uniform="x")
            self._boton(fila, txt, "#FFE3EE", fn, font=("Segoe UI", 9, "bold"),
                        anchor="center").grid(row=0, column=k, sticky="ew", padx=2)

    def _panel_der(self):
        der = tk.Frame(self, bg=BG)
        der.grid(row=1, column=1, sticky="nsew", padx=(7, 14), pady=12)
        der.columnconfigure(0, weight=1)
        der.rowconfigure(1, weight=3)
        der.rowconfigure(3, weight=1)

        top = tk.Frame(der, bg=BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(top, text="Estructura en memoria", bg=BG, fg=CAFE,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        self.lbl_cont = tk.Label(top, bg=BG, fg=ROSA, font=("Segoe UI", 10, "bold"))
        self.lbl_cont.pack(side="right")

        wrap = tk.Frame(der, bg="white", highlightthickness=1, highlightbackground=BORDE)
        wrap.grid(row=1, column=0, sticky="nsew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self.cv = tk.Canvas(wrap, bg="white", highlightthickness=0)
        sy = tk.Scrollbar(wrap, orient="vertical", command=self.cv.yview)
        sx = tk.Scrollbar(wrap, orient="horizontal", command=self.cv.xview)
        self.cv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.cv.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.cv.bind("<Enter>", self._rueda_on)
        self.cv.bind("<Leave>", self._rueda_off)

        tk.Label(der, text="Mensajes", bg=BG, fg=CAFE,
                 font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w", pady=(10, 4))
        lf = tk.Frame(der, bg="white", highlightthickness=1, highlightbackground=BORDE)
        lf.grid(row=3, column=0, sticky="nsew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)
        self.log = tk.Text(lf, height=8, font=("Consolas", 10), bg="#FFFDF9", fg=CAFE,
                           relief="flat", wrap="word", state="disabled", padx=8, pady=6)
        ls = tk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=ls.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        ls.grid(row=0, column=1, sticky="ns")
        self.log.tag_config("ok", foreground="#2E7D32")
        self.log.tag_config("err", foreground="#C62828")
        self.log.tag_config("info", foreground="#1565C0")

    def _rueda_on(self, e):
        self.cv.bind_all("<MouseWheel>", lambda ev: self.cv.yview_scroll(-1 if ev.delta > 0 else 1, "units"))
        self.cv.bind_all("<Shift-MouseWheel>", lambda ev: self.cv.xview_scroll(-1 if ev.delta > 0 else 1, "units"))

    def _rueda_off(self, e):
        self.cv.unbind_all("<MouseWheel>")
        self.cv.unbind_all("<Shift-MouseWheel>")

    # ---------- utilidades ----------
    def msg(self, texto, tipo="info"):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n", tipo)
        if int(self.log.index("end-1c").split(".")[0]) > 300:  # el log no crece sin límite
            self.log.delete("1.0", "100.0")
        self.log.see("end")
        self.log.config(state="disabled")

    def error(self, e):
        self.msg("✖ " + str(e), "err")
        messagebox.showwarning("Aviso", str(e), parent=self)

    def report_callback_exception(self, exc, val, tb):  # cualquier fallo no previsto
        self.msg(f"✖ Error inesperado: {val!r}", "err")

    def _run(self, fn):
        try:
            fn()
        except ErrorPostre as e:
            self.error(e)
        except Exception as e:  # último recurso: avisar y NO cerrar el programa
            self.msg(f"✖ Error inesperado: {e!r}", "err")
            messagebox.showerror("Error inesperado", f"Ocurrió un problema interno:\n{e}", parent=self)
        self.dibujar()

    def seleccionar(self, nombre, idx=None):
        self.v_postre.set(nombre)
        self.sel = clave(nombre)
        self.sel_idx = idx
        self.dibujar()

    # ---------- menú desplegable de postres (se actualiza solo) ----------
    def _estilo(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("TCombobox", fieldbackground="#FFF3F7", background="#F8BBD0", foreground=CAFE,
                     arrowcolor=CAFE, bordercolor=BORDE, lightcolor="#FFF3F7", darkcolor="#FFF3F7",
                     padding=4)
        st.map("TCombobox", fieldbackground=[("readonly", "#FFF3F7"), ("disabled", "#F2F2F2")],
               foreground=[("disabled", GRIS)])
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))
        self.option_add("*TCombobox*Listbox.selectBackground", ROSA)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

    def _sync_combo(self):
        """Reconstruye «1 · Brownie», «2 · Flan»... cada vez que cambia el arreglo."""
        ps = self.rec.postres
        self.combo["values"] = [f"{i + 1} · {p.nombre}" for i, p in enumerate(ps)]
        self.lbl_combo.config(text=f"Elegir postre (1–{len(ps)}):" if ps else "Elegir postre:")
        self.combo.config(state="readonly" if ps else "disabled")
        idx = None
        if ps and self.sel is not None:
            if (self.sel_idx is not None and self.sel_idx < len(ps)
                    and clave(ps[self.sel_idx].nombre) == self.sel):
                idx = self.sel_idx
            else:
                idx = next((i for i, p in enumerate(ps) if clave(p.nombre) == self.sel), None)
        if idx is not None:
            self.combo.current(idx)
        else:
            self.v_combo.set("Elige uno…" if ps else "Sin postres")

    def _elegir(self, _evento=None):
        try:
            i = int(self.v_combo.get().split(" ")[0]) - 1
        except ValueError:
            return
        ps = self.rec.postres
        if 0 <= i < len(ps):
            self.seleccionar(ps[i].nombre, i)
            self.combo.selection_clear()

    def _enfocar(self, p):
        self.v_postre.set(p.nombre)  # muestra el nombre ya normalizado
        self.sel = clave(p.nombre)
        n = self.rec.cuantos(p.nombre)
        if n > 1:
            self.msg(f"ℹ Hay {n} postres llamados «{p.nombre}»; se usó el primero.", "info")

    # ---------- operaciones ----------
    def op_ver(self):  # a)
        p = self.rec.obtener(self.v_postre.get())
        self._enfocar(p)
        ings = p.ingredientes.elementos()
        if ings:
            self.msg(f"✔ {p.nombre} → " + ", ".join(ings), "ok")
        else:
            self.msg(f"ℹ {p.nombre} no tiene ingredientes (su lista apunta a NIL).", "info")

    def op_agregar(self):  # b)
        self.rec.obtener(self.v_postre.get())  # primero el postre, luego los ingredientes
        ings = parsear_ingredientes(self.v_ing.get())
        p, nuevos, rep = self.rec.agregar_ingredientes(self.v_postre.get(), ings)
        self._enfocar(p)
        self.msg(f"✔ Se agregaron a {p.nombre}: {', '.join(nuevos)}", "ok")
        if rep:
            self.msg(f"ℹ Ya estaban (no se duplican): {', '.join(rep)}", "info")
        self.v_ing.set("")

    def op_quitar(self):  # c)
        self.rec.obtener(self.v_postre.get())
        ings = parsear_ingredientes(self.v_ing.get())
        p, quitados, faltan = self.rec.quitar_ingredientes(self.v_postre.get(), ings)
        self._enfocar(p)
        self.msg(f"✔ Se quitaron de {p.nombre}: {', '.join(quitados)}", "ok")
        if faltan:
            self.msg(f"ℹ No estaban en la lista: {', '.join(faltan)}", "info")
        if p.ingredientes.cabeza is None:
            self.msg(f"ℹ La lista de {p.nombre} quedó vacía (apunta a NIL).", "info")
        self.v_ing.set("")

    def op_alta(self):  # d)
        validar_nombre(self.v_postre.get(), "nombre del postre")
        ings = parsear_ingredientes(self.v_ing.get())
        p, ign = self.rec.alta(self.v_postre.get(), ings, self.permitir.get())
        self.v_postre.set(p.nombre)
        self.sel = clave(p.nombre)
        self.msg(f"✔ Alta de {p.nombre} con {len(p.ingredientes)} ingrediente(s).", "ok")
        if ign:
            self.msg(f"ℹ Ingredientes repetidos ignorados: {', '.join(ign)}", "info")
        self.v_ing.set("")

    def op_baja(self):  # e)
        p = self.rec.obtener(self.v_postre.get())
        if not messagebox.askyesno("Baja de postre",
                                   f"¿Eliminar «{p.nombre}» con todos sus ingredientes?", parent=self):
            return
        p, lista, restantes = self.rec.baja(p.nombre)
        self.sel = None
        self.msg(f"✔ Baja de {p.nombre}. Se liberaron {len(lista)} nodo(s): {', '.join(lista) or '—'}", "ok")
        if restantes:
            self.msg(f"ℹ Todavía quedan {restantes} postre(s) con ese nombre (usa «Eliminar repetidos»).", "info")

    def op_dedup(self):  # ejercicio 2
        if not self.rec.postres:
            raise ErrorPostre("El arreglo está vacío: no hay nada que depurar.")
        if not self.rec.hay_repetidos():
            self.msg("ℹ No hay postres repetidos en el arreglo.", "info")
            return
        r = messagebox.askyesnocancel(
            "Eliminar repetidos",
            "Hay postres repetidos.\n\n¿Fusionar los ingredientes de los repetidos con el "
            "postre que se conserva?\n\nSí = fusionar\nNo = borrar sin fusionar (esas listas se pierden)\n"
            "Cancelar = no hacer nada", parent=self)
        if r is None:
            return
        for linea in self.rec.eliminar_repetidos(r):
            self.msg("• " + linea, "ok")
        self.msg("Conclusión: NO marcó error. Al borrar el elemento repetido del arreglo, su lista ligada "
                 "queda sin referencia (huérfana) y Python libera los nodos solo. Si no se fusiona, "
                 "esos ingredientes se pierden.", "info")

    def cargar_ejemplo(self, con_repetidos, confirmar=True):
        if confirmar and self.rec.postres and not messagebox.askyesno(
                "Cargar ejemplo", "Esto reemplaza todo lo que hay en el arreglo.\n¿Continuar?", parent=self):
            return
        self.rec = Recetario()
        datos = EJEMPLO + ([("Flan", ["Leche", "Huevo", "Caramelo"])] if con_repetidos else [])
        for n, ings in datos:
            self.rec.alta(n, ings, True)
        self.sel = None
        self.msg("ℹ Ejemplo cargado" + (" (con un Flan repetido)." if con_repetidos else "."), "info")
        self.dibujar()

    def vaciar(self):
        if not self.rec.postres:
            self.msg("ℹ El arreglo ya está vacío.", "info")
            return
        if not messagebox.askyesno("Vaciar", "¿Borrar TODOS los postres y sus ingredientes?", parent=self):
            return
        self.rec = Recetario()
        self.sel = None
        self.msg("ℹ Arreglo vaciado.", "info")
        self.dibujar()

    # ---------- dibujo de la estructura ----------
    def dibujar(self):
        c, ps = self.cv, self.rec.postres
        c.delete("all")
        self._sync_combo()
        lleno = len(ps) >= CAPACIDAD
        self.lbl_cont.config(text=f"Postres en el arreglo: {len(ps)} / {CAPACIDAD}" + ("  (lleno)" if lleno else ""),
                             fg="#C62828" if lleno else ROSA)
        if not ps:
            cupcake(c, 280, 30, 1.3, "#F8BBD0")
            c.create_text(300, 150, text="El arreglo está vacío\nCarga un ejemplo o da de alta un postre",
                          font=("Segoe UI", 13), fill="#B08A99", justify="center")
            c.configure(scrollregion=(0, 0, 600, 240))
            c.xview_moveto(0)
            c.yview_moveto(0)
            return

        X0, AW, DIV, BH, RH = 18, 230, 196, 48, 66
        NW, ND, GAP = 130, 104, 40
        flecha = dict(arrow="last", fill="#F5A300", width=2)
        maxx = 0
        for i, p in enumerate(ps):
            y, ym, tag = 16 + i * RH, 16 + i * RH + BH / 2, f"fila{i}"
            es_sel = clave(p.nombre) == self.sel
            rep = i > 0 and clave(ps[i - 1].nombre) == clave(p.nombre)
            borde = "#FB8C00" if rep else ("#EC407A" if es_sel else "#8D6E63")
            grosor = 3 if (rep or es_sel) else 2
            xa = X0 + 34

            c.create_text(X0, ym, text=f"[{i + 1}]", anchor="w", font=("Consolas", 9), fill=GRIS)
            c.create_rectangle(xa, y, xa + AW, y + BH, fill="#FFE3EE" if es_sel else "#FFF8F3",
                               outline=borde, width=grosor, tags=tag)
            c.create_rectangle(xa + DIV, y, xa + AW, y + BH, fill="#FCE4EC",
                               outline=borde, width=grosor, tags=tag)
            glaseado = GLASEADOS[sum(map(ord, clave(p.nombre))) % len(GLASEADOS)]
            cupcake(c, xa + 6, y + 9, 0.6, glaseado, tags=(tag,))
            c.create_text(xa + 42, ym, text=p.nombre, anchor="w", width=DIV - 48,
                          font=("Segoe UI", 10, "bold"), fill=CAFE, tags=tag)
            if rep:
                c.create_text(xa + 4, y + BH + 9, text="↑ repetido", anchor="w",
                              font=("Segoe UI", 8, "bold"), fill="#FB8C00")
            c.tag_bind(tag, "<Button-1>", lambda e, n=p.nombre, k=i: self.seleccionar(n, k))
            c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

            px = xa + DIV + (AW - DIV) / 2  # punto de salida del puntero
            c.create_oval(px - 3, ym - 3, px + 3, ym + 3, fill="#E6A100", outline="")
            x, ant = xa + AW + GAP + 10, px
            act = p.ingredientes.cabeza
            while act:
                c.create_line(ant, ym, x, ym, **flecha)
                c.create_rectangle(x, y + 4, x + NW, y + BH - 4, fill="white", outline="#8D6E63", width=2)
                c.create_rectangle(x + ND, y + 4, x + NW, y + BH - 4, fill="#FFF3D6", outline="#8D6E63", width=2)
                c.create_text(x + ND / 2, ym, text=act.dato, width=ND - 8, justify="center",
                              font=("Segoe UI", 9), fill=CAFE)  # se ajusta en líneas, no se recorta
                ant = x + ND + (NW - ND) / 2
                c.create_oval(ant - 3, ym - 3, ant + 3, ym + 3, fill="#E6A100", outline="")
                x += NW + GAP
                act = act.sig
            c.create_line(ant, ym, ant + 34, ym, **flecha)
            c.create_text(ant + 40, ym, text="NIL", anchor="w", font=("Segoe UI", 11, "bold"), fill="#6D4C41")
            maxx = max(maxx, ant + 90)
        alto = 16 + len(ps) * RH + 8
        c.configure(scrollregion=(0, 0, maxx + 20, alto))
        c.xview_moveto(0)  # siempre se ve el arreglo a la izquierda
        if alto <= c.winfo_height():
            c.yview_moveto(0)


if __name__ == "__main__":
    App().mainloop()