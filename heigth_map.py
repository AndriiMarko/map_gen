import numpy as np
from PIL import Image
from sphere_surface import SphereSurface, get_opposite

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

    def linear_wave_deform(self, lon, lat, direction, magnitude, attenuation, period=10, max_steps=1000):
        """
        Apply a linear wave deformation starting from (lon, lat) in the given direction.
        Moves along the line using SphereSurface.next(), applying a sinusoidal wave
        with given magnitude, attenuation per step, and period (in steps).
        Stops after max_steps, if attenuation makes the effect negligible, or if endline_check indicates end.
        Then does the same in the opposite direction.
        """
        # Get min and max values from surface dtype
        dtype = self.height_surface.surface.dtype
        min_val = np.iinfo(dtype).min
        max_val = np.iinfo(dtype).max

        # First direction
        current_lon, current_lat = int(lon), int(lat)
        distance = 0

        while distance < max_steps and (attenuation ** distance) > 1e-6:
            wave_value = magnitude * np.sin(2 * np.pi * distance / period) * (attenuation ** distance)
            self.height_surface.surface[current_lon, current_lat] = np.clip(
                self.height_surface.surface[current_lon, current_lat] + wave_value, min_val, max_val
            )

            if self.plates.surface.endline_check(current_lon, current_lat, direction):
                break

            try:
                next_lon, next_lat = self.plates.surface.next(current_lon, current_lat, direction)
                current_lon, current_lat = next_lon, next_lat
                distance += 1
            except Exception:
                break

        # Opposite direction
        opp_direction = get_opposite(direction)
        current_lon, current_lat = int(lon), int(lat)
        distance = 0

        while distance < max_steps and (attenuation ** distance) > 1e-6:
            wave_value = magnitude * np.sin(2 * np.pi * distance / period) * (attenuation ** distance)
            self.height_surface.surface[current_lon, current_lat] = np.clip(
                self.height_surface.surface[current_lon, current_lat] + wave_value, min_val, max_val
            )

            if self.plates.surface.endline_check(current_lon, current_lat, opp_direction):
                break

            try:
                next_lon, next_lat = self.plates.surface.next(current_lon, current_lat, opp_direction)
                current_lon, current_lat = next_lon, next_lat
                distance += 1
            except Exception:
                break

        # No rounding needed since we clipped to dtype range

    def calculate_collision_magnitude(self, dir1, dir2):
        """
        Calculate magnitude based on two plate movement directions.
        Higher for head-on collisions, lower for parallel or same direction.
        """
        opposites = {'N':'S', 'S':'N', 'E':'W', 'W':'E', 'NE':'SW', 'SW':'NE', 'NW':'SE', 'SE':'NW'}
        if dir1.upper() == opposites.get(dir2.upper(), ''):
            return 20  # head-on collision
        elif dir1.upper() == dir2.upper():
            return 5   # same direction, low collision
        else:
            return 10  # oblique collision

    def plate_tectonic_apply(self, plate_id, attenuation=0.9, period=5):
        """
        Apply tectonic deformation for the given plate_id.
        Finds the plate's movement direction, then for each border point that touches another plate,
        determines the other plate's direction, calculates magnitude, and applies linear_wave_deform.
        """
        plate = next((p for p in self.plates.plates if p.plate_id == plate_id), None)
        if plate is None:
            return

        direction = getattr(plate, 'movement_direction', 'N')

        for point in plate.borders:
            lon, lat = point
            other_plate_id = None
            for d in [direction, get_opposite(direction)]:
                nlon, nlat = self.plates.surface.next(lon, lat, d)
                pid = self.plates.surface.surface[nlon, nlat]
                if pid != plate_id and pid != 0:
                    other_plate_id = pid
                    break
            if other_plate_id is not None:
                other_plate = next((p for p in self.plates.plates if p.plate_id == other_plate_id), None)
                if other_plate:
                    other_direction = getattr(other_plate, 'movement_direction', 'N')
                    magnitude = self.calculate_collision_magnitude(direction, other_direction)
                    self.linear_wave_deform(lon, lat, direction, magnitude, attenuation, period)

    def tectonic_apply(self, attenuation=0.9, period=5):
        """
        Apply tectonic deformation for all plates by calling plate_tectonic_apply for each plate.
        """
        for plate in self.plates.plates:
            self.plate_tectonic_apply(plate.plate_id, attenuation, period)