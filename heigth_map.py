import numpy as np
from PIL import Image
from sphere_surface import SphereSurface

class HeightMap:
    """
    Build a heightmap from a TectonicPlates instance.

    Constructor args:
    - plates: TectonicPlates instance
    - base_ocean: int height value for ocean plates (will be used as integer)
    - base_continent: int height value for continental plates (will be used as integer)
    - smooth_window: odd integer window size for box smoothing (>=1)
    """
    def __init__(self, plates, base_ocean=20, base_continent=60, smooth_window=3):
        self.plates = plates
        # prefer integer heights
        self.base_ocean = int(base_ocean)
        self.base_continent = int(base_continent)
        self.smooth_window = max(1, int(smooth_window))
        if self.smooth_window % 2 == 0:
            self.smooth_window += 1

        # surface
        self.height_surface = SphereSurface(self.plates.surface.equator_length)

        # build raw height map using plate types
        self.set_base_heights()

        # apply smoothing (works on float)
        if self.smooth_window > 1:
            self.height_surface.surface = self._box_smooth(self.smooth_window)

        # final integer height map (rounded)
        #self.map = np.rint(fmap).astype(np.int16)

    def set_base_heights(self):
        surface = self.plates.surface.surface

        plate_types = {p.plate_id: (1 if p.plate_type == 'continental' else 0) for p in self.plates.plates}

        for y in range(np.round(self.height_surface.equator_length/2).astype(int)):
            length = self.height_surface.pixel_lengths[y]
            for x in range(self.height_surface.pixel_offsets[y], self.height_surface.pixel_offsets[y]+length):
                plate_id = surface[y, x]
                if plate_id == 0:
                    value = self.base_ocean
                else:
                    if plate_types[plate_id] == 1:
                        value = self.base_continent
                    else:
                        value = self.base_ocean
                self.height_surface.surface[y, x] = value

    def _box_smooth(self, k):
        """Fast box filter via integral image. k must be odd."""
        equator_length = self.height_surface.equator_length
        surface = np.zeros((np.round(equator_length/2).astype(int), equator_length), dtype=np.uint8)
        for y in range(np.round(equator_length/2).astype(int)):
            length = self.height_surface.pixel_lengths[y]
            for x in range(self.height_surface.pixel_offsets[y], self.height_surface.pixel_offsets[y]+length):
                smoothed_value = self.height_surface.square_filter(y, x, k)
                surface[y, x] = smoothed_value
        return surface   

    def to_image(self, filename=None, mode="L"):
        """
        Convert integer heightmap to PIL Image.
        - mode "L" produces grayscale (0..255). Values will be normalized to 0..255.
        If filename provided, save the image and return the PIL Image.
        """
        rect = self.height_surface.to_rectangle()
        mn, mx = self.height_surface.get_min_max()
        if mx <= mn:
            norm = np.zeros_like(rect, dtype=np.uint8)
        else:
            norm = ((rect - mn) / (mx - mn) * 255.0).astype(np.uint8)
        img = Image.fromarray(norm, mode)
        if filename:
            img.save(filename)
        return img
    
    def to_image2(self, filename=None, mode="L"):
        """
        Convert integer heightmap to PIL Image.
        - mode "L" produces grayscale (0..255). Values will be normalized to 0..255.
        If filename provided, save the image and return the PIL Image.
        """
        rect = self.height_surface.to_rectangle2()
        mn, mx = self.height_surface.get_min_max()
        if mx <= mn:
            norm = np.zeros_like(rect, dtype=np.uint8)
        else:
            norm = ((rect - mn) / (mx - mn) * 255.0).astype(np.uint8)
        img = Image.fromarray(norm, mode)
        if filename:
            img.save(filename)
        return img