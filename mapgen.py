import tkinter as tk
from PIL import ImageTk
from tectonic_plates import TectonicPlates

def main():
    plates = TectonicPlates(equator_length=512, num_continental=5, num_oceanic=7)
    plates.draw_plates()
    #plates.surface.set_surface_default(2)  # For testing
    img = plates.surface_to_image()
    img2 = plates.surface_to_image2()

    root = tk.Tk()
    root.title("Tectonic Plates Map")

    tk_img = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=tk_img)
    label.pack()

    tk_img2 = ImageTk.PhotoImage(img2)
    label2 = tk.Label(root, image=tk_img2)
    label2.pack()

    root.mainloop()

if __name__ == "__main__":
    main()