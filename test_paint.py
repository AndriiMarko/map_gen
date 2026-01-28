import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from sphere_surface import SphereSurface, End_of_aray

DIRECTION = 'N'

class PainterApp(tk.Tk):
    def __init__(self, equator_length=128, delay=10, direction=DIRECTION):
        super().__init__()
        self.title("SphereSurface Painter")
        self.eq = equator_length
        self.delay = delay  # ms between painted pixels
        self.direction = direction
        # create sphere surface and clear (black)
        self.sphere = SphereSurface(self.eq)
        self.sphere.set_surface_default(0)

        # rectangle representation parameters
        self.rect = self.sphere.to_rectangle()
        self.h, self.w = self.rect.shape  # h = num_lon rows, w = equator_length

        # tkinter Canvas
        self.canvas = tk.Canvas(self, width=self.w, height=self.h)
        self.canvas.pack(fill="both", expand=True)

        # create initial PhotoImage
        self.photo = None
        self._update_image()

        # build iterator of coordinates to paint using start/next
        self.coord_iter = self._coords_generator()

        # start painting loop
        self.after(self.delay, self._paint_step)

    def _update_image(self):
        """Create RGB image from rectangle (0 = black, >0 = red)."""
        self.rect = self.sphere.to_rectangle2()
        arr = self.rect
        h, w = arr.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        mask = arr == 0
        rgb[~mask] = (255, 0, 0)   # painted pixels -> red
        rgb[mask] = (0, 0, 0)      # background -> black
        img = Image.fromarray(rgb, 'RGB')
        self.photo = ImageTk.PhotoImage(img)
        # draw or update image on canvas
        if getattr(self, "_img_id", None) is None:
            self._img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        else:
            self.canvas.itemconfigure(self._img_id, image=self.photo)
        self.update_idletasks()

    def _coords_generator(self):
        """
        Generate coordinates to paint using start(direction) once and next().
        We'll scan each logical row (latitude value across longitudes):
        for each latitude from 0..eq-1 find a starting longitude and then walk east with next(...,'E').
        This uses SphereSurface.next(...) for stepping.
        """
        lon, lat = self.sphere.start(self.direction)
        #print(f"Starting painting at lon={lon}, lat={lat}, direction={self.direction}")
        while True:
            yield (lon, lat)
            try:
                lon, lat = self.sphere.next(lon, lat, self.direction)
            except End_of_aray:
                break

    def _paint_step(self):
        try:
            lon, lat = next(self.coord_iter)
            #print(f"Painting at lon={lon}, lat={lat}")
        except StopIteration:
            print("Painting complete.")
            return  # done
        # paint if free (0)
        if self.sphere.get(lon, lat) == 0:
            self.sphere.set(lon, lat, 255)
        # update displayed image
        self._update_image()
        # schedule next step
        self.after(self.delay, self._paint_step)

if __name__ == "__main__":
    app = PainterApp(equator_length=64, delay=5, direction=DIRECTION)
    app.mainloop()