import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk
import threading

from tectonic_plates import TectonicPlates

class MapGenUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tectonic Plates MapGen")
        self._build_controls()
        self.img_label_a = None
        self.img_label_b = None
        self.tk_img_a = None
        self.tk_img_b = None

    def _build_controls(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill="x")

        # Equator length
        ttk.Label(frm, text="Equator length:").grid(row=0, column=0, sticky="w")
        self.eq_var = tk.IntVar(value=512)
        self.eq_spin = ttk.Spinbox(frm, from_=4, to=4096, increment=2, textvariable=self.eq_var, width=8)
        self.eq_spin.grid(row=0, column=1, sticky="w", padx=6)

        # Continental plates
        ttk.Label(frm, text="Continental plates:").grid(row=1, column=0, sticky="w")
        self.cont_var = tk.IntVar(value=5)
        self.cont_spin = ttk.Spinbox(frm, from_=1, to=200, textvariable=self.cont_var, width=8)
        self.cont_spin.grid(row=1, column=1, sticky="w", padx=6)

        # Oceanic plates
        ttk.Label(frm, text="Oceanic plates:").grid(row=2, column=0, sticky="w")
        self.ocean_var = tk.IntVar(value=7)
        self.ocean_spin = ttk.Spinbox(frm, from_=0, to=200, textvariable=self.ocean_var, width=8)
        self.ocean_spin.grid(row=2, column=1, sticky="w", padx=6)

        # Generate button
        self.gen_btn = ttk.Button(frm, text="Generate", command=self.on_generate)
        self.gen_btn.grid(row=0, column=2, rowspan=3, padx=12)

        # Canvas/frame for images
        self.images_frame = ttk.Frame(self, padding=8)
        self.images_frame.pack(fill="both", expand=True)

        # Two labels for two images (stacked)
        self.label_a = ttk.Label(self.images_frame)
        self.label_a.pack(side="top", expand=True, pady=4)
        self.label_b = ttk.Label(self.images_frame)
        self.label_b.pack(side="top", expand=True, pady=4)

    def on_generate(self):
        try:
            eq = int(self.eq_var.get())
            cont = int(self.cont_var.get())
            ocean = int(self.ocean_var.get())
            if eq < 4 or cont < 1 or ocean < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid input", "Please enter valid numeric values.")
            return

        # disable button while generating
        self.gen_btn.config(state="disabled")
        threading.Thread(target=self._generate_thread, args=(eq, cont, ocean), daemon=True).start()

    def _generate_thread(self, eq_len, num_cont, num_ocean):
        try:
            plates = TectonicPlates(equator_length=eq_len, num_continental=num_cont, num_oceanic=num_ocean)
            plates.draw_plates()  # may log progress to console
            img1 = plates.surface_to_image()
            img2 = None
            # surface_to_image2 may not always be implemented; try to call if available
            try:
                img2 = plates.surface_to_image2()
            except Exception:
                img2 = img1.copy()
            # schedule UI update on main thread
            self.after(0, self._update_images, img1, img2)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Generation error", str(e)))
            self.after(0, lambda: self.gen_btn.config(state="normal"))
        else:
            self.after(0, lambda: self.gen_btn.config(state="normal"))

    def _update_images(self, pil_img_a, pil_img_b):
        # keep references to PhotoImage to avoid garbage collection
        self.tk_img_a = ImageTk.PhotoImage(pil_img_a)
        self.label_a.configure(image=self.tk_img_a)

        self.tk_img_b = ImageTk.PhotoImage(pil_img_b)
        self.label_b.configure(image=self.tk_img_b)

if __name__ == "__main__":
    app = MapGenUI()
    app.mainloop()