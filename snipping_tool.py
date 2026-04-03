import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image, ImageTk, ImageDraw
import base64
import io
import keyboard
from ocr_tool import run_ocr

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

SUGGESTED_PROMPTS = [
    "What does this say?",
    "Explain this",
    "Translate this to English",
    "Summarize this",
    "What is wrong with this?",
]


class SnippingOverlay:
    """Fullscreen transparent overlay for region selection."""

    def __init__(self, callback):
        self.callback = callback
        self.start_x = self.start_y = 0
        self.rect = None

        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.35)
        self.root.configure(bg="black")
        self.root.attributes("-topmost", True)
        self.root.config(cursor="crosshair")

        self.canvas = tk.Canvas(self.root, bg="black", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_press(self, event):
        self.start_x, self.start_y = event.x_root, event.y_root
        if self.rect:
            self.canvas.delete(self.rect)

    def on_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
        x0 = self.start_x - self.root.winfo_rootx()
        y0 = self.start_y - self.root.winfo_rooty()
        x1 = event.x
        y1 = event.y
        self.rect = self.canvas.create_rectangle(
            x0, y0, x1, y1,
            outline="#00BFFF", width=2, dash=(4, 2)
        )

    def on_release(self, event):
        end_x, end_y = event.x_root, event.y_root
        self.root.destroy()
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        if x2 - x1 > 5 and y2 - y1 > 5:
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.callback(screenshot)


class SnipToolbar(tk.Toplevel):
    """Action toolbar shown after a snip is taken."""

    def __init__(self, parent, image: Image.Image, send_to_chat_callback):
        super().__init__(parent)
        self.image = image
        self.send_to_chat_callback = send_to_chat_callback
        self.ocr_mode = tk.StringVar(value="quick")
        self.selected_lang = tk.StringVar(value="auto")

        self.title("Snip Toolbar")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self._build_ui()

    def _build_ui(self):
        # ── Preview ──────────────────────────────────────────────
        preview = self.image.copy()
        preview.thumbnail((400, 300))
        self.tk_img = ImageTk.PhotoImage(preview)
        tk.Label(self, image=self.tk_img, bd=1, relief="solid").pack(
            padx=10, pady=(10, 4)
        )

        # ── OCR Mode Toggle ───────────────────────────────────────
        mode_frame = tk.Frame(self)
        mode_frame.pack(pady=4)
        tk.Label(mode_frame, text="OCR Mode:", font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Radiobutton(
            mode_frame, text="⚡ Quick (Tesseract)",
            variable=self.ocr_mode, value="quick",
            command=self._toggle_lang_bar
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            mode_frame, text="🤖 AI OCR",
            variable=self.ocr_mode, value="ai",
            command=self._toggle_lang_bar
        ).pack(side=tk.LEFT, padx=(8, 0))

        # ── Language Bar (Quick OCR only) ─────────────────────────
        self.lang_frame = tk.Frame(self)
        self.lang_frame.pack(pady=2)
        tk.Label(self.lang_frame, text="Language:", font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        langs = [
            ("Auto 🔍", "auto"), ("EN", "eng"), ("DE", "deu"), ("FR", "fra"),
            ("ES", "spa"), ("IT", "ita"), ("NL", "nld"), ("PT", "por"),
            ("RU", "rus"), ("PL", "pol"), ("CS", "ces"), ("SV", "swe"),
        ]
        for label, code in langs:
            tk.Radiobutton(
                self.lang_frame, text=label,
                variable=self.selected_lang, value=code,
                indicatoron=False, padx=4, pady=2,
                font=("Segoe UI", 8)
            ).pack(side=tk.LEFT, padx=1)

        # ── Suggested Prompt ──────────────────────────────────────
        prompt_frame = tk.Frame(self)
        prompt_frame.pack(pady=4, padx=10, fill=tk.X)
        tk.Label(prompt_frame, text="Prompt:", font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        self.prompt_var = tk.StringVar(value=SUGGESTED_PROMPTS[0])
        prompt_menu = tk.OptionMenu(prompt_frame, self.prompt_var, *SUGGESTED_PROMPTS)
        prompt_menu.config(font=("Segoe UI", 9))
        prompt_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ── Action Buttons ────────────────────────────────────────
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8, padx=10)

        actions = [
            ("📤 Send to AI", self.send_to_ai),
            ("📝 Extract Text", self.extract_text),
            ("💾 Save", self.save_image),
            ("✏️ Edit", self.open_editor),
            ("📋 Copy", self.copy_to_clipboard),
        ]
        for text, cmd in actions:
            tk.Button(
                btn_frame, text=text, command=cmd,
                font=("Segoe UI", 9), padx=8, pady=4
            ).pack(side=tk.LEFT, padx=3)

        # ── OCR Result Box ────────────────────────────────────────
        self.result_label = tk.Label(
            self, text="", font=("Segoe UI", 9), fg="#555"
        )
        self.result_label.pack()
        self.result_text = tk.Text(
            self, height=6, font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED
        )

    def _toggle_lang_bar(self):
        if self.ocr_mode.get() == "quick":
            self.lang_frame.pack(pady=2)
        else:
            self.lang_frame.pack_forget()

    def _image_to_base64(self) -> str:
        buffer = io.BytesIO()
        self.image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def send_to_ai(self):
        b64 = self._image_to_base64()
        prompt = self.prompt_var.get()
        self.send_to_chat_callback(b64, prompt)
        self.destroy()

    def extract_text(self):
        mode = self.ocr_mode.get()
        lang = self.selected_lang.get() if mode == "quick" else None
        self.result_label.config(text="Extracting text...")
        self.update()

        text = run_ocr(self.image, mode=mode, lang_override=None if lang == "auto" else lang)

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
        self.result_text.pack(padx=10, pady=(0, 8), fill=tk.BOTH)
        self.result_label.config(text="Extracted Text:")

    def save_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")],
            title="Save Snip"
        )
        if path:
            self.image.save(path)
            messagebox.showinfo("Saved", f"Snip saved to:\n{path}")

    def open_editor(self):
        SnipEditor(self, self.image)

    def copy_to_clipboard(self):
        # Copy image to clipboard via temporary file + shell
        import tempfile, subprocess, sys
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            self.image.save(f.name)
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-command",
                     f"Set-Clipboard -Path '{f.name}'"],
                    check=False
                )
        self.result_label.config(text="Image copied to clipboard.")


class SnipEditor(tk.Toplevel):
    """Minimal annotation editor: draw, highlight, add arrows."""

    def __init__(self, parent, image: Image.Image):
        super().__init__(parent)
        self.title("Edit Snip")
        self.orig_image = image.copy()
        self.draw_image = image.copy()
        self.draw_layer = ImageDraw.Draw(self.draw_image)
        self.tool = tk.StringVar(value="pen")
        self.color = "red"
        self.last_x = self.last_y = None
        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=4)

        tools = [("✏️ Pen", "pen"), ("🔲 Rect", "rect"), ("➡️ Arrow", "arrow")]
        for label, val in tools:
            tk.Radiobutton(
                toolbar, text=label, variable=self.tool,
                value=val, indicatoron=False, padx=6
            ).pack(side=tk.LEFT, padx=2)

        colors = [("Red", "red"), ("Yellow", "yellow"), ("Blue", "blue"), ("Green", "green")]
        for label, col in colors:
            tk.Button(
                toolbar, text=label, bg=col, width=6,
                command=lambda c=col: setattr(self, "color", c)
            ).pack(side=tk.LEFT, padx=2)

        tk.Button(toolbar, text="💾 Save", command=self.save).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text="↩ Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)

        self.tk_img = ImageTk.PhotoImage(self.draw_image)
        self.canvas = tk.Canvas(
            self, width=self.draw_image.width, height=self.draw_image.height
        )
        self.canvas.pack()
        self.canvas_img = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.history = []

    def _refresh(self):
        self.tk_img = ImageTk.PhotoImage(self.draw_image)
        self.canvas.itemconfig(self.canvas_img, image=self.tk_img)

    def on_press(self, e):
        self.last_x, self.last_y = e.x, e.y
        self.history.append(self.draw_image.copy())

    def on_drag(self, e):
        if self.tool.get() == "pen" and self.last_x is not None:
            self.draw_layer.line(
                [self.last_x, self.last_y, e.x, e.y],
                fill=self.color, width=3
            )
            self.last_x, self.last_y = e.x, e.y
            self._refresh()

    def on_release(self, e):
        if self.tool.get() == "rect":
            self.draw_layer.rectangle(
                [self.last_x, self.last_y, e.x, e.y],
                outline=self.color, width=3
            )
        elif self.tool.get() == "arrow":
            self.draw_layer.line(
                [self.last_x, self.last_y, e.x, e.y],
                fill=self.color, width=3
            )
            self.draw_layer.polygon(
                [e.x, e.y,
                 e.x - 10, e.y - 6,
                 e.x - 10, e.y + 6],
                fill=self.color
            )
        self._refresh()

    def undo(self):
        if self.history:
            self.draw_image = self.history.pop()
            self.draw_layer = ImageDraw.Draw(self.draw_image)
            self._refresh()

    def save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Save Edited Snip"
        )
        if path:
            self.draw_image.save(path)


def register_snip_hotkey(root, send_to_chat_callback):
    """Register global hotkey Ctrl+Shift+S to trigger the snipping overlay."""

    def trigger():
        root.after(0, lambda: _start_snip(root, send_to_chat_callback))

    keyboard.add_hotkey("ctrl+shift+s", trigger)


def _start_snip(root, send_to_chat_callback):
    def on_snip_done(image):
        SnipToolbar(root, image, send_to_chat_callback)

    SnippingOverlay(on_snip_done)
