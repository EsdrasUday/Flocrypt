import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import os
import json
import threading
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_DISPONIVEL = True
except ImportError:
    DND_DISPONIVEL = False

# ============================================================
# Paleta — extraída da referência "CipherDrop"
# ============================================================
BG_APP        = "#0d1117"
PANEL_BG      = "#161b27"
PANEL_BORDER  = "#252b36"
CARD_BG       = "#1c2338"
CARD_HOVER    = "#212840"

BADGE_BLUE    = "#3d6ef0"
TEXT_WHITE    = "#dde4f0"
TEXT_GRAY     = "#7a869e"
TEXT_GRAY_DIM = "#647087"
LINK_BLUE     = "#6d96ff"
DANGER        = "#e05a5a"

DASH_COLOR        = "#343c4c"
DASH_COLOR_ACTIVE = "#3d6ef0"
ICON_GRAY         = "#7a869e"

FIELD_BG      = "#0d1117"
FIELD_BORDER  = "#303746"

BTN_ENCRYPT   = "#3d6ef0"
BTN_ENCRYPT_HOVER = "#2a4eb0"
BTN_DECRYPT   = "#1c2338"
BTN_DECRYPT_HOVER = "#212840"

TAB_ACTIVE_BG = "#2a4eb0"
TAB_ACTIVE_FG = "#dde4f0"

PILL_ENC_BG   = "#203a80"
PILL_ENC_FG   = "#8eafff"
PILL_DEC_BG   = "#183b2c"
PILL_DEC_FG   = "#4caf7d"

EXT_COLORS = {
    "pdf": "#e05a5a", "doc": "#e05a5a", "docx": "#e05a5a",
    "zip": "#d49a3a", "rar": "#d49a3a", "7z": "#d49a3a",
    "tar": "#d49a3a", "gz": "#d49a3a",
    "sql": "#4caf7d", "db": "#4caf7d",
    "txt": "#7a869e", "md": "#7a869e", "log": "#7a869e",
    "png": "#3d6ef0", "jpg": "#3d6ef0", "jpeg": "#3d6ef0", "gif": "#3d6ef0",
    "webp": "#3d6ef0", "bmp": "#3d6ef0", "svg": "#3d6ef0",
    "mp3": "#9b72e8", "wav": "#9b72e8", "mp4": "#9b72e8", "mkv": "#9b72e8",
    "csv": "#4caf7d", "json": "#d49a3a", "py": "#d49a3a", "js": "#d49a3a",
}
EXT_COLOR_DEFAULT = "#3d6ef0"

ctk.set_appearance_mode("dark")

MAGIC = b"CPHD1"       
SALT_SIZE = 16
NONCE_SIZE = 12        
KDF_ITERATIONS = 600_000

HISTORICO_PATH = os.path.join(os.path.expanduser("~"), ".cipherdrop_historico.json")
MAX_HISTORICO = 50



def formatar_tamanho(num_bytes: int) -> str:
    tamanho = float(num_bytes)
    for unidade in ("B", "KB", "MB", "GB"):
        if tamanho < 1024 or unidade == "GB":
            return f"{tamanho:.1f} {unidade}" if unidade != "B" else f"{int(tamanho)} B"
        tamanho /= 1024
    return f"{tamanho:.1f} GB"


def formatar_quando(iso_ts: str) -> str:
    dt = datetime.fromisoformat(iso_ts)
    hoje = datetime.now().date()
    if dt.date() == hoje:
        return f"Hoje, {dt.strftime('%H:%M')}"
    if (hoje - dt.date()).days == 1:
        return f"Ontem, {dt.strftime('%H:%M')}"
    return dt.strftime("%d %b, %H:%M")


def cor_extensao(ext: str) -> str:
    return EXT_COLORS.get(ext.lower().lstrip("."), EXT_COLOR_DEFAULT)


if DND_DISPONIVEL:
    class _BaseJanela(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self):
            super().__init__()
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class _BaseJanela(ctk.CTk):
        pass


class CipherDrop(_BaseJanela):
    def __init__(self):
        super().__init__()
        self.title("Floki")
        self.geometry("1060x640")
        self.minsize(920, 560)
        self.configure(fg_color=BG_APP)

        self.arquivo_selecionado = ""
        self.senha_visivel = False
        self.filtro_atual = "todos"
        self.historico = self._carregar_historico()

        raiz = ctk.CTkFrame(self, fg_color="transparent")
        raiz.pack(fill="both", expand=True, padx=16, pady=16)
        raiz.grid_columnconfigure(0, weight=1)
        raiz.grid_columnconfigure(1, weight=0, minsize=290)
        raiz.grid_rowconfigure(0, weight=1)

        self._montar_painel_esquerdo(raiz)
        self._montar_painel_direito(raiz)

    def _mostrar_dialogo(self, titulo, mensagem, tipo="info"):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, lambda: self._mostrar_dialogo(titulo, mensagem, tipo))
            return

        cores = {
            "success": ("#4caf7d", "Concluído"),
            "error": (DANGER, "Não foi possível concluir"),
            "warning": ("#d49a3a", "Atenção"),
            "info": (BADGE_BLUE, titulo),
        }
        cor, subtitulo = cores.get(tipo, cores["info"])

        dialogo = ctk.CTkToplevel(self)
        dialogo.title(titulo)
        dialogo.geometry("430x240")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color=PANEL_BG)
        dialogo.transient(self)
        dialogo.grab_set()

        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 430) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 240) // 2
        dialogo.geometry(f"430x240+{x}+{y}")

        conteudo = ctk.CTkFrame(dialogo, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=28, pady=24)

        icone = ctk.CTkFrame(conteudo, width=44, height=44, corner_radius=14,
                             fg_color=self._cor_com_alpha(cor))
        icone.pack()
        icone.pack_propagate(False)
        simbolos = {"success": "✓", "error": "!", "warning": "!", "info": "i"}
        ctk.CTkLabel(icone, text=simbolos.get(tipo, "i"), font=("Inter", 22, "bold"),
                     text_color=cor).pack(expand=True)

        ctk.CTkLabel(conteudo, text=subtitulo, font=("Inter", 15, "bold"),
                     text_color=TEXT_WHITE).pack(pady=(12, 5))
        ctk.CTkLabel(conteudo, text=mensagem, font=("Inter", 11), text_color=TEXT_GRAY,
                     justify="center", wraplength=360).pack()

        botao = ctk.CTkButton(conteudo, text="Entendi", width=110, height=34,
                              corner_radius=9, fg_color=cor, hover_color=cor,
                              text_color=BG_APP, font=("Inter", 11, "bold"),
                              command=dialogo.destroy)
        botao.pack(pady=(18, 0))
        dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)
        dialogo.bind("<Return>", lambda _event: dialogo.destroy())
        dialogo.bind("<Escape>", lambda _event: dialogo.destroy())
        botao.focus_set()

    def _montar_painel_esquerdo(self, raiz):
        painel = ctk.CTkFrame(raiz, fg_color=PANEL_BG, corner_radius=18,
                               border_width=1, border_color=PANEL_BORDER)
        painel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        header = ctk.CTkFrame(painel, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(22, 18))

        badge = ctk.CTkFrame(header, width=40, height=40, corner_radius=11, fg_color=BADGE_BLUE)
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="🛡", font=("Arial", 17), text_color="white").pack(expand=True)

        textos = ctk.CTkFrame(header, fg_color="transparent")
        textos.pack(side="left", padx=12)
        ctk.CTkLabel(textos, text="Flocrypt", font=("Inter", 17, "bold"),
                     text_color=TEXT_WHITE, anchor="w").pack(anchor="w")
        ctk.CTkLabel(textos, text="Criptografia de arquivos AES-256", font=("Inter", 11),
                     text_color=TEXT_GRAY, anchor="w").pack(anchor="w")
        ctk.CTkFrame(painel, fg_color=PANEL_BORDER, height=1).pack(fill="x", padx=0)

        # Zona de drop (Canvas com borda tracejada
        self.dropzone = Canvas(painel, bg=PANEL_BG, highlightthickness=0, height=192)
        self.dropzone.pack(fill="x", padx=24, pady=(0, 18))
        self.dropzone.pack_propagate(False)
        self.dropzone.bind("<Configure>", lambda e: self._redesenhar_dropzone())
        self.dropzone.bind("<Button-1>", lambda e: self.selecionar_arquivo())
        self.dropzone.configure(cursor="hand2")

        if DND_DISPONIVEL:
            self.dropzone.drop_target_register(DND_FILES)
            self.dropzone.dnd_bind('<<Drop>>', self.on_drop)
            self.dropzone.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.dropzone.dnd_bind('<<DragLeave>>', self.on_drag_leave)

        # Senha
        ctk.CTkLabel(painel, text="Senha de criptografia", font=("Inter", 11),
                     text_color=TEXT_GRAY, anchor="w").pack(fill="x", padx=24)

        campo_senha = ctk.CTkFrame(painel, fg_color=FIELD_BG, corner_radius=10,
                                    border_width=1, border_color=FIELD_BORDER, height=42)
        campo_senha.pack(fill="x", padx=24, pady=(6, 16))
        campo_senha.pack_propagate(False)

        ctk.CTkLabel(campo_senha, text="🔒", width=18, font=("Noto Sans Symbols 2", 14),
                 text_color=TEXT_GRAY).pack(side="left", padx=(12, 4))

        self.entry_pass = ctk.CTkEntry(campo_senha, placeholder_text="Digite uma senha segura...",
                                        show="*", fg_color="transparent", border_width=0,
                                        text_color=TEXT_WHITE)
        self.entry_pass.pack(side="left", fill="both", expand=True)

        self.btn_olho = ctk.CTkButton(campo_senha, text="⊘", width=28, height=28,
                         corner_radius=6, fg_color="transparent",
                         hover_color=FIELD_BORDER, text_color=TEXT_GRAY,
                         font=("Noto Sans Symbols 2", 16),
                         command=self.alternar_senha_visivel)
        self.btn_olho.pack(side="right", padx=6)

        
        linha_botoes = ctk.CTkFrame(painel, fg_color="transparent")
        linha_botoes.pack(fill="x", padx=24, pady=(0, 10))
        linha_botoes.grid_columnconfigure((0, 1), weight=1)

        self.btn_criptografar = ctk.CTkButton(
            linha_botoes, text="🔒  Criptografar", height=42, corner_radius=10,
            fg_color=BTN_ENCRYPT, hover_color=BTN_ENCRYPT_HOVER, text_color="white",
            font=("Inter", 13, "bold"),
            command=lambda: self.iniciar_thread('c')
        )
        self.btn_criptografar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_descriptografar = ctk.CTkButton(
            linha_botoes, text="🔓  Descriptografar", height=42, corner_radius=10,
            fg_color=BTN_DECRYPT, hover_color=BTN_DECRYPT_HOVER, text_color=TEXT_WHITE,
            font=("Inter", 13, "bold"), border_width=1, border_color=FIELD_BORDER,
            command=lambda: self.iniciar_thread('d')
        )
        self.btn_descriptografar.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self._atualizar_estado_botoes()
        self.entry_pass.bind("<Return>", self._processar_com_enter)

        rodape = ctk.CTkFrame(painel, fg_color="transparent")
        rodape.pack(fill="x", padx=24, pady=(4, 22))

        self.progress_bar = ctk.CTkProgressBar(rodape, progress_color=BADGE_BLUE, fg_color=FIELD_BG)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(2, 6))

        self.status_label = ctk.CTkLabel(rodape, text="", font=("Inter", 10), text_color=TEXT_GRAY)
        self.status_label.pack(anchor="w")

        ctk.CTkLabel(rodape, text="© 2026 Esdras Uday. All rights reserved.",
                 font=("Inter", 9), text_color=TEXT_GRAY_DIM).pack(pady=(14, 0))
        ctk.CTkLabel(rodape, text="v4.2", font=("JetBrains Mono", 9),
                 text_color=TEXT_GRAY_DIM).pack(pady=(3, 0))

        self._redesenhar_dropzone()

    def _redesenhar_dropzone(self):
        c = self.dropzone
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        cor_borda = DASH_COLOR_ACTIVE if self.arquivo_selecionado else DASH_COLOR
        cor_icone = BADGE_BLUE if self.arquivo_selecionado else ICON_GRAY

        margem, raio = 2, 14
        x1, y1, x2, y2 = margem, margem, w - margem, h - margem
        dash = (6, 5)

        c.create_line(x1 + raio, y1, x2 - raio, y1, fill=cor_borda, dash=dash, width=1.6)
        c.create_line(x1 + raio, y2, x2 - raio, y2, fill=cor_borda, dash=dash, width=1.6)
        c.create_line(x1, y1 + raio, x1, y2 - raio, fill=cor_borda, dash=dash, width=1.6)
        c.create_line(x2, y1 + raio, x2, y2 - raio, fill=cor_borda, dash=dash, width=1.6)
        c.create_arc(x1, y1, x1 + 2 * raio, y1 + 2 * raio, start=90, extent=90,
                     style="arc", outline=cor_borda, dash=dash, width=1.6)
        c.create_arc(x2 - 2 * raio, y1, x2, y1 + 2 * raio, start=0, extent=90,
                     style="arc", outline=cor_borda, dash=dash, width=1.6)
        c.create_arc(x1, y2 - 2 * raio, x1 + 2 * raio, y2, start=180, extent=90,
                     style="arc", outline=cor_borda, dash=dash, width=1.6)
        c.create_arc(x2 - 2 * raio, y2 - 2 * raio, x2, y2, start=270, extent=90,
                     style="arc", outline=cor_borda, dash=dash, width=1.6)

        cx, cy = w / 2, h / 2

        if self.arquivo_selecionado:
            nome = os.path.basename(self.arquivo_selecionado)
            if len(nome) > 34:
                nome = nome[:31] + "..."
            ext = os.path.splitext(self.arquivo_selecionado)[1].lstrip(".").upper()[:4] or "FILE"
            cor_ext = cor_extensao(ext)
            c.create_rectangle(cx - 31, cy - 53, cx + 31, cy - 17,
                               fill=self._cor_com_alpha(cor_ext), outline=cor_ext,
                               width=1)
            c.create_text(cx, cy - 35, text=ext, font=("JetBrains Mono", 13, "bold"),
                          fill=cor_ext)
            c.create_text(cx, cy + 8, text=nome, font=("Inter", 13, "bold"), fill=TEXT_WHITE)
            c.create_text(cx, cy + 30, text="arquivo pronto · clique para trocar",
                          font=("Inter", 10), fill=TEXT_GRAY_DIM)
        else:
            # ícone de upload desenhado manualmente (seta + bandeja)
            ax, atopo, abase = cx, cy - 48, cy - 20
            c.create_line(ax, abase, ax, atopo, fill=cor_icone, width=2.2, arrow="last", arrowshape=(9, 11, 4))
            c.create_line(ax - 13, abase + 3, ax - 13, abase + 12, fill=cor_icone, width=2.2)
            c.create_line(ax + 13, abase + 3, ax + 13, abase + 12, fill=cor_icone, width=2.2)
            c.create_line(ax - 13, abase + 12, ax + 13, abase + 12, fill=cor_icone, width=2.2)

            c.create_text(cx, cy + 8, text="Arraste e solte seu arquivo",
                          font=("Inter", 14, "bold"), fill=TEXT_WHITE)
            c.create_text(cx, cy + 30, text="ou clique para selecionar · Qualquer formato",
                          font=("Inter", 10), fill=TEXT_GRAY_DIM)

    def _montar_painel_direito(self, raiz):
        painel = ctk.CTkFrame(raiz, fg_color=PANEL_BG, corner_radius=18,
                               border_width=1, border_color=PANEL_BORDER, width=290)
        painel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        painel.grid_propagate(False)

        header = ctk.CTkFrame(painel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 12))

        esquerda = ctk.CTkFrame(header, fg_color="transparent")
        esquerda.pack(side="left")
        ctk.CTkLabel(esquerda, text="🕐", font=("Arial", 13), text_color=TEXT_GRAY).pack(side="left")
        ctk.CTkLabel(esquerda, text=" Arquivos Recentes", font=("Inter", 14, "bold"),
                     text_color=TEXT_WHITE).pack(side="left")

        self.badge_contagem = ctk.CTkFrame(header, fg_color=PILL_ENC_BG, corner_radius=10)
        self.badge_contagem.pack(side="right")
        self.label_contagem = ctk.CTkLabel(self.badge_contagem, text="0", font=("Inter", 11, "bold"),
                                            text_color=PILL_ENC_FG)
        self.label_contagem.pack(padx=9, pady=1)
        ctk.CTkFrame(painel, fg_color=PANEL_BORDER, height=1).pack(fill="x")

        # ---------------- Abas ----------------
        abas = ctk.CTkFrame(painel, fg_color="transparent")
        abas.pack(fill="x", padx=20, pady=(0, 8))

        self.botoes_aba = {}
        for chave, rotulo in (("todos", "Todos"), ("enc", "Criptog."), ("dec", "Descri.")):
            btn = ctk.CTkButton(abas, text=rotulo, width=66, height=26, corner_radius=8,
                                 font=("Inter", 11),
                                 command=lambda k=chave: self._selecionar_aba(k))
            btn.pack(side="left", padx=(0, 6))
            self.botoes_aba[chave] = btn
        ctk.CTkFrame(painel, fg_color=PANEL_BORDER, height=1).pack(fill="x")

       
        self.lista_scroll = ctk.CTkScrollableFrame(
            painel,
            fg_color="transparent",
            scrollbar_fg_color=PANEL_BG,
            scrollbar_button_color=PANEL_BG,
            scrollbar_button_hover_color=PANEL_BG,
        )
        self.lista_scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self.bind_all("<Button-4>", self._rolar_historico_cima, add="+")
        self.bind_all("<Button-5>", self._rolar_historico_baixo, add="+")

        ctk.CTkFrame(painel, fg_color=PANEL_BORDER, height=1).pack(fill="x")
        rodape = ctk.CTkFrame(painel, fg_color="transparent")
        rodape.pack(fill="x", padx=20, pady=14)

        linha1 = ctk.CTkFrame(rodape, fg_color="transparent")
        linha1.pack(fill="x")
        ctk.CTkLabel(linha1, text="Algoritmo", font=("Inter", 11), text_color=TEXT_GRAY).pack(side="left")
        ctk.CTkLabel(linha1, text="AES-256-GCM", font=("JetBrains Mono", 11, "bold"),
                     text_color=LINK_BLUE).pack(side="right")

        linha2 = ctk.CTkFrame(rodape, fg_color="transparent")
        linha2.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(linha2, text="Derivação", font=("Inter", 11), text_color=TEXT_GRAY).pack(side="left")
        ctk.CTkLabel(linha2, text="PBKDF2-SHA512", font=("JetBrains Mono", 11, "bold"),
                     text_color=LINK_BLUE).pack(side="right")

        self._selecionar_aba("todos")

    def _selecionar_aba(self, chave):
        self.filtro_atual = chave
        for k, btn in self.botoes_aba.items():
            if k == chave:
                btn.configure(fg_color=TAB_ACTIVE_BG, text_color=TAB_ACTIVE_FG)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_GRAY)
        self._renderizar_lista()

    def _renderizar_lista(self):
        for filho in self.lista_scroll.winfo_children():
            filho.destroy()

        if self.filtro_atual == "enc":
            itens = [h for h in self.historico if h["tipo"] == "ENC"]
        elif self.filtro_atual == "dec":
            itens = [h for h in self.historico if h["tipo"] == "DEC"]
        else:
            itens = self.historico

        self.label_contagem.configure(text=str(len(self.historico)))

        if not itens:
            ctk.CTkLabel(self.lista_scroll, text="Nenhum arquivo ainda",
                         font=("Inter", 11), text_color=TEXT_GRAY_DIM).pack(pady=20)
            return

        for item in itens:
            self._linha_arquivo(item)

    def _linha_arquivo(self, item):
        ext = os.path.splitext(item["nome"])[1].lstrip(".").upper()[:4] or "?"
        cor = cor_extensao(ext)

        linha = ctk.CTkFrame(self.lista_scroll, fg_color="transparent", corner_radius=10,
                     height=62)
        linha.pack(fill="x", padx=8, pady=4)
        linha.pack_propagate(False)

        badge = ctk.CTkFrame(linha, width=34, height=34, corner_radius=8,
                              fg_color=self._cor_com_alpha(cor), border_width=1, border_color=cor)
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=ext, font=("JetBrains Mono", 8, "bold"), text_color=cor).pack(expand=True)

        meio = ctk.CTkFrame(linha, fg_color="transparent")
        meio.pack(side="left", fill="x", expand=True, padx=8)

        nome_exibido = item["nome"] if len(item["nome"]) <= 16 else item["nome"][:13] + "..."
        ctk.CTkLabel(meio, text=nome_exibido, font=("JetBrains Mono", 9, "bold"),
                     text_color=TEXT_WHITE, anchor="w").pack(anchor="w")
        subt = f'{formatar_tamanho(item["tamanho"])} · {formatar_quando(item["timestamp"])}'
        ctk.CTkLabel(meio, text=subt, font=("Inter", 9), text_color=TEXT_GRAY_DIM,
                     anchor="w").pack(anchor="w")

        pill_bg, pill_fg = (PILL_ENC_BG, PILL_ENC_FG) if item["tipo"] == "ENC" else (PILL_DEC_BG, PILL_DEC_FG)
        pill = ctk.CTkFrame(linha, width=34, height=20, fg_color=pill_bg, corner_radius=6)
        pill.pack(side="right", padx=(2, 2))
        pill.pack_propagate(False)
        ctk.CTkLabel(pill, text=item["tipo"], font=("JetBrains Mono", 8, "bold"),
                 text_color=pill_fg).pack(expand=True)

        remover = ctk.CTkButton(linha, text="🗑", width=26, height=26, corner_radius=6,
                    fg_color="transparent", hover_color="#3a2028",
                    text_color=DANGER, font=("Noto Sans Symbols 2", 14),
                    cursor="hand2",
                    command=lambda registro=item: self._remover_historico(registro))
        remover.pack(side="right", padx=(4, 8))

        def selecionar(_event=None):
            caminho = item.get("caminho", "")
            if caminho and os.path.isfile(caminho):
                self.definir_arquivo(caminho)
            else:
                self._mostrar_dialogo("Arquivo indisponível",
                                      "O arquivo deste registro não está mais disponível.", "warning")

        def entrar(_event=None):
            linha.configure(fg_color=CARD_HOVER)

        def sair(_event=None):
            linha.configure(fg_color="transparent")

        for widget in (linha, badge, meio, pill):
            widget.bind("<Button-1>", selecionar)
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", sair)
        for widget in meio.winfo_children():
            widget.bind("<Button-1>", selecionar)
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", sair)

    def _rolar_historico_cima(self, event):
        if self.lista_scroll.check_if_master_is_canvas(event.widget):
            self.lista_scroll._parent_canvas.yview_scroll(-3, "units")

    def _rolar_historico_baixo(self, event):
        if self.lista_scroll.check_if_master_is_canvas(event.widget):
            self.lista_scroll._parent_canvas.yview_scroll(3, "units")

    def _remover_historico(self, item):
        self.historico = [registro for registro in self.historico if registro is not item]
        self._salvar_historico()
        self._renderizar_lista()

    @staticmethod
    def _cor_com_alpha(hexcolor):
        hexcolor = hexcolor.lstrip("#")
        r, g, b = (int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = int(r * 0.22), int(g * 0.22), int(b * 0.22)
        return f"#{r:02x}{g:02x}{b:02x}"

  
    def _carregar_historico(self):
        try:
            with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _salvar_historico(self):
        try:
            with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
                json.dump(self.historico[:MAX_HISTORICO], f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # histórico é conveniência, não deve travar o fluxo principal

    def _registrar_historico(self, nome, tamanho, tipo, caminho):
        self.historico.insert(0, {
            "nome": nome,
            "tamanho": tamanho,
            "tipo": tipo,
            "caminho": caminho,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        self.historico = self.historico[:MAX_HISTORICO]
        self._salvar_historico()
        self.after(0, self._renderizar_lista)


    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename()
        if caminho:
            self.definir_arquivo(caminho)

    def _atualizar_estado_botoes(self):
        arquivo_selecionado = bool(self.arquivo_selecionado)
        eh_criptografado = arquivo_selecionado and os.path.splitext(
            self.arquivo_selecionado
        )[1].lower() == ".floki"
        self.btn_criptografar.configure(
            state="disabled" if eh_criptografado or not arquivo_selecionado else "normal"
        )
        self.btn_descriptografar.configure(
            state="normal" if eh_criptografado else "disabled"
        )

    def _processar_com_enter(self, _event=None):
        if not self.arquivo_selecionado:
            self._mostrar_dialogo("Atenção", "Selecione um arquivo primeiro.", "warning")
            return "break"
        modo = "d" if os.path.splitext(self.arquivo_selecionado)[1].lower() == ".floki" else "c"
        self.iniciar_thread(modo)
        return "break"

    def definir_arquivo(self, caminho: str):
        if not os.path.isfile(caminho):
            self._mostrar_dialogo("Atenção", "Isso não parece ser um arquivo válido.", "warning")
            return
        self.arquivo_selecionado = caminho
        self._atualizar_estado_botoes()
        self._redesenhar_dropzone()

    def on_drag_enter(self, event):
        return event.action

    def on_drag_leave(self, event):
        return event.action

    def on_drop(self, event):
        caminhos = self.tk.splitlist(event.data)
        if not caminhos:
            return
        if len(caminhos) > 1:
            self._mostrar_dialogo("Aviso", "Solte apenas um arquivo por vez. Usando o primeiro.", "info")
        self.definir_arquivo(caminhos[0])

    def alternar_senha_visivel(self):
        self.senha_visivel = not self.senha_visivel
        self.entry_pass.configure(show="" if self.senha_visivel else "*")
        self.btn_olho.configure(text="◉" if self.senha_visivel else "⊘")


    def derivar_chave(self, senha: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=salt,
                          iterations=KDF_ITERATIONS)
        return kdf.derive(senha.encode())

    def iniciar_thread(self, modo):
        threading.Thread(target=self.processar, args=(modo,), daemon=True).start()

    def set_status(self, texto):
        self.after(0, lambda: self.status_label.configure(text=texto))

    def wipe_seguro(self, caminho: str, passadas: int = 3):
        try:
            tamanho = os.path.getsize(caminho)
            with open(caminho, "r+b") as f:
                for _ in range(passadas):
                    f.seek(0)
                    f.write(os.urandom(tamanho))
                    f.flush()
                    os.fsync(f.fileno())
            os.remove(caminho)
        except Exception:
            if os.path.exists(caminho):
                os.remove(caminho)

    def processar(self, modo):
        senha = self.entry_pass.get()
        if not self.arquivo_selecionado:
            self._mostrar_dialogo("Atenção", "Selecione um arquivo primeiro.", "warning")
            return
        if modo == 'c' and not senha:
            self._mostrar_dialogo("Atenção", "Digite uma senha para criptografar o arquivo.", "warning")
            return

        caminho_original = self.arquivo_selecionado
        diretorio = os.path.dirname(caminho_original)

        try:
            self.progress_bar.set(0.1)
            self.set_status("Lendo arquivo...")

            with open(caminho_original, 'rb') as f:
                dados_originais = f.read()

            if modo == 'c':
                self.set_status("Gerando salt/nonce e derivando chave...")
                self.progress_bar.set(0.25)

                salt = os.urandom(SALT_SIZE)
                nonce = os.urandom(NONCE_SIZE)
                chave = self.derivar_chave(senha, salt)
                aesgcm = AESGCM(chave)

                nome_original = os.path.basename(caminho_original).encode()
                metadata = len(nome_original).to_bytes(2, 'big') + nome_original
                conteudo_total = metadata + dados_originais

                self.set_status("Criptografando (AES-256-GCM)...")
                self.progress_bar.set(0.5)
                ciphertext = aesgcm.encrypt(nonce, conteudo_total, None)

                pacote_final = MAGIC + salt + nonce + ciphertext
                nome_saida = os.path.basename(caminho_original) + ".floki"
                novo_caminho = os.path.join(diretorio, nome_saida)
                with open(novo_caminho, 'wb') as f:
                    f.write(pacote_final)

                tipo_hist = "ENC"
                nome_hist = os.path.basename(caminho_original)
                tamanho_hist = len(dados_originais)

            else:
                self.set_status("Validando arquivo...")
                self.progress_bar.set(0.2)

                cabecalho_min = len(MAGIC) + SALT_SIZE + NONCE_SIZE
                if len(dados_originais) < cabecalho_min:
                    raise ValueError("Arquivo muito pequeno ou inválido.")
                if dados_originais[:len(MAGIC)] != MAGIC:
                    raise ValueError("Este arquivo não é um .floki válido.")

                cursor = len(MAGIC)
                salt = dados_originais[cursor:cursor + SALT_SIZE]
                cursor += SALT_SIZE
                nonce = dados_originais[cursor:cursor + NONCE_SIZE]
                cursor += NONCE_SIZE
                ciphertext = dados_originais[cursor:]

                self.set_status("Derivando chave e descriptografando...")
                self.progress_bar.set(0.5)
                chave = self.derivar_chave(senha, salt)
                aesgcm = AESGCM(chave)

                try:
                    pacote_decifrado = aesgcm.decrypt(nonce, ciphertext, None)
                except InvalidTag:
                    raise ValueError("Senha incorreta ou arquivo corrompido.")

                tam_nome = int.from_bytes(pacote_decifrado[:2], 'big')
                nome_original = os.path.basename(
                    pacote_decifrado[2:2 + tam_nome].decode()
                )
                resultado = pacote_decifrado[2 + tam_nome:]

                novo_caminho = os.path.join(diretorio, nome_original)
                with open(novo_caminho, 'wb') as f:
                    f.write(resultado)

                tipo_hist = "DEC"
                nome_hist = nome_original
                tamanho_hist = len(resultado)

            self.progress_bar.set(0.8)
            self.set_status("Removendo arquivo original com segurança...")

            if os.path.exists(caminho_original) and caminho_original != novo_caminho:
                self.wipe_seguro(caminho_original)

            self._registrar_historico(nome_hist, tamanho_hist, tipo_hist, novo_caminho)

            self.progress_bar.set(1.0)
            self.set_status("Concluído.")
            self._mostrar_dialogo("Sucesso", "Arquivo transformado com sucesso!", "success")
            self.arquivo_selecionado = ""
            self.entry_pass.delete(0, "end")
            self._atualizar_estado_botoes()
            self.after(0, self._redesenhar_dropzone)
            self.progress_bar.set(0)

        except ValueError as ve:
            self.progress_bar.set(0)
            self.set_status("")
            self._mostrar_dialogo("Erro", f"Falha! {ve}\nO arquivo original não foi alterado.", "error")
        except Exception:
            self.progress_bar.set(0)
            self.set_status("")
            self._mostrar_dialogo("Erro", "Falha inesperada.\nO arquivo original não foi alterado.", "error")


if __name__ == "__main__":
    app = CipherDrop()
    app.mainloop()