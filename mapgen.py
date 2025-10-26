import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk
import threading

from tectonic_plates import TectonicPlates
from heigth_map import HeightMap

class MapGenUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tectonic Plates MapGen")
        self._build_controls()
        # keep PhotoImage refs to avoid GC
        self.tk_img_a = None
        self.tk_img_b = None
        self.tk_img_c = None
        self.tk_img_d = None

    def _build_controls(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill="x")

        # Equator length
        ttk.Label(frm, text="Equator length:").grid(row=0, column=0, sticky="w")
        self.eq_var = tk.IntVar(value=128)
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

        # Heightmap parameters
        ttk.Label(frm, text="Base ocean (int):").grid(row=3, column=0, sticky="w")
        self.base_ocean_var = tk.IntVar(value=20)
        self.base_ocean_spin = ttk.Spinbox(frm, from_=0, to=255, textvariable=self.base_ocean_var, width=8)
        self.base_ocean_spin.grid(row=3, column=1, sticky="w", padx=6)

        ttk.Label(frm, text="Base continent (int):").grid(row=4, column=0, sticky="w")
        self.base_cont_var = tk.IntVar(value=60)
        self.base_cont_spin = ttk.Spinbox(frm, from_=0, to=255, textvariable=self.base_cont_var, width=8)
        self.base_cont_spin.grid(row=4, column=1, sticky="w", padx=6)

        ttk.Label(frm, text="Smooth window:").grid(row=5, column=0, sticky="w")
        self.smooth_var = tk.IntVar(value=3)
        self.smooth_spin = ttk.Spinbox(frm, from_=1, to=99, textvariable=self.smooth_var, width=8)
        self.smooth_spin.grid(row=5, column=1, sticky="w", padx=6)

        # Generate button
        self.gen_btn = ttk.Button(frm, text="Generate", command=self.on_generate)
        self.gen_btn.grid(row=0, column=2, rowspan=6, padx=12)

        # Canvas/frame for 2x2 images
        self.images_frame = ttk.Frame(self, padding=8)
        self.images_frame.pack(fill="both", expand=True)

        # create a 2x2 grid of labels
        self.label_a = ttk.Label(self.images_frame)
        self.label_b = ttk.Label(self.images_frame)
        self.label_c = ttk.Label(self.images_frame)
        self.label_d = ttk.Label(self.images_frame)

        self.label_a.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.label_b.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        self.label_c.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")
        self.label_d.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")

        # make grid expand
        self.images_frame.columnconfigure(0, weight=1)
        self.images_frame.columnconfigure(1, weight=1)
        self.images_frame.rowconfigure(0, weight=1)
        self.images_frame.rowconfigure(1, weight=1)

    def on_generate(self):
        try:
            eq = int(self.eq_var.get())
            cont = int(self.cont_var.get())
            ocean = int(self.ocean_var.get())
            base_ocean = int(self.base_ocean_var.get())
            base_cont = int(self.base_cont_var.get())
            smooth = int(self.smooth_var.get())
            if eq < 4 or cont < 1 or ocean < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid input", "Please enter valid numeric values.")
            return

        self.gen_btn.config(state="disabled")
        threading.Thread(
            target=self._generate_thread,
            args=(eq, cont, ocean, base_ocean, base_cont, smooth),
            daemon=True
        ).start()

    def _generate_thread(self, eq_len, num_cont, num_ocean, base_ocean, base_cont, smooth):
        try:
            plates = TectonicPlates(equator_length=eq_len, num_continental=num_cont, num_oceanic=num_ocean)
            plates.draw_plates()  # may log progress to console

            # plate image variants
            img_plate_1 = plates.surface_to_image()
            try:
                img_plate_2 = plates.surface_to_image2()
            except Exception:
                img_plate_2 = img_plate_1.copy()

            # heightmap variants
            hmap = HeightMap(plates, base_ocean=base_ocean, base_continent=base_cont, smooth_window=smooth)
            img_height_1 = hmap.to_image()
            try:
                img_height_2 = hmap.to_image2()
            except Exception:
                img_height_2 = img_height_1.copy()

            self.after(0, self._update_images, img_plate_1, img_plate_2, img_height_1, img_height_2)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Generation error", str(e)))
            self.after(0, lambda: self.gen_btn.config(state="normal"))
        else:
            self.after(0, lambda: self.gen_btn.config(state="normal"))

    def _update_images(self, pil_a, pil_b, pil_c, pil_d):
        # keep references to PhotoImage to avoid garbage collection
        self.tk_img_a = ImageTk.PhotoImage(pil_a)
        self.label_a.configure(image=self.tk_img_a)

        self.tk_img_b = ImageTk.PhotoImage(pil_b)
        self.label_b.configure(image=self.tk_img_b)

        self.tk_img_c = ImageTk.PhotoImage(pil_c)
        self.label_c.configure(image=self.tk_img_c)

        self.tk_img_d = ImageTk.PhotoImage(pil_d)
        self.label_d.configure(image=self.tk_img_d)

if __name__ == "__main__":
    app = MapGenUI()
    app.mainloop()