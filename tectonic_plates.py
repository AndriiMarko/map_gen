import numpy as np
from sphere_surface import SphereSurface
from PIL import Image
import time

class Plate:
    def __init__(self, plate_id, latitude, longitude, plate_type, growth_rate):
        self.plate_id = plate_id
        self.latitude = latitude
        self.longitude = longitude
        self.plate_type = plate_type  # 'continental' or 'oceanic'
        self.growth_rate = growth_rate
        self.points = set()   # Holds all points belonging to this plate
        self.borders = set()  # Holds border points for this plate
        self.old_borders = set()  # Holds border points for this plate

class TectonicPlates:
    def __init__(self, equator_length, num_continental, num_oceanic, growth_rate_range=3):
        self.surface = SphereSurface(equator_length)
        self.equator_length = equator_length
        self.plates = []
        self._init_plates(num_continental, num_oceanic, growth_rate_range)

    def _random_point(self):
        # Random latitude and longitude indices on the sphere surface
        longitude = np.random.randint(0, np.round(self.equator_length/2).astype(int)-1)
        latitude = np.random.randint(self.surface.pixel_offsets[longitude], self.surface.pixel_offsets[longitude]+self.surface.pixel_lengths[longitude])
        return longitude, latitude

    def _init_plates(self, num_continental, num_oceanic, growth_rate_range):
        for i in range(num_continental):
            lon, lat = self._random_point()
            growth_rate = np.random.randint(1, growth_rate_range)
            self.plates.append(Plate(i + 1, lat, lon, 'continental', growth_rate))
        for i in range(num_oceanic):
            lon, lat = self._random_point()
            growth_rate = np.random.randint(1, growth_rate_range)
            self.plates.append(Plate(num_continental + i + 1, lat, lon, 'oceanic', growth_rate))

    def draw_plates(self):
        surface = self.surface.surface

        # Initialize plate seeds
        for plate in self.plates:
            if surface[plate.longitude, plate.latitude] == 0:
                surface[plate.longitude, plate.latitude] = plate.plate_id
                plate.points.add((plate.longitude, plate.latitude))
                plate.borders.add((plate.longitude, plate.latitude))

        # Directions: S, N, E, W, 
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        
        step = 0
        total_pixels = self.surface.size()
        free_pixels = total_pixels - self.surface.count_nonzero()
        print(f"Starting plate growth: {free_pixels} free pixels")

        previous_round_free = free_pixels
        while free_pixels > 0:
            step += 1
            for plate in self.plates:
                for g in range(plate.growth_rate):
                    new_borders = set()
                    for point in plate.borders:
                        lon, lat = point
                        taken_bits_encountered = 0
                        for dlon, dlat in directions:
                            nlon = lon + dlon
                            if 0 <= nlon < np.round(self.equator_length/2).astype(int):
                                nlat = (lat + dlat)
                                if nlat < self.surface.pixel_offsets[nlon]:
                                    end_lat = self.surface.pixel_offsets[nlon] + self.surface.pixel_lengths[nlon]
                                    negative_offset = self.surface.pixel_offsets[nlon] - nlat
                                    nlat = end_lat - negative_offset
                                elif nlat >= self.surface.pixel_offsets[nlon] + self.surface.pixel_lengths[nlon]:
                                    nlat = nlat % self.surface.pixel_lengths[nlon] + self.surface.pixel_offsets[nlon]
                                if surface[nlon, nlat] == 0:
                                    surface[nlon, nlat] = plate.plate_id
                                    new_borders.add((nlon, nlat))
                                else:
                                    taken_bits_encountered += 1
                        if taken_bits_encountered > 0:
                            plate.old_borders.add(point)
                    plate.borders = new_borders
                    plate.points.update(new_borders)
            free_pixels = total_pixels - self.surface.count_nonzero()
            print(f"Step {step}: {free_pixels} free pixels remaining ({100 * (total_pixels - free_pixels) // total_pixels}%)")
            # time.sleep(1)  # Slow down for visibility
            if free_pixels == previous_round_free:
                print("No more growth possible, stopping.")
                break
            else: 
                previous_round_free = free_pixels
        print("Plate growth complete.")

    def surface_to_image(self):
        """
        Converts the sphere surface to a rectangle and returns it as an image.
        Each plate ID is assigned a distinguishable color.
        """
        rect = self.surface.to_rectangle()
        # rect = self.surface.surface # For testing without transformation
        h, w = rect.shape

        # Assign colors for each plate (random but fixed for reproducibility)
        np.random.seed(42)
        plate_ids = [plate.plate_id for plate in self.plates]
        colors = {
            pid: tuple(np.random.randint(0, 256, 3)) for pid in plate_ids
        }
        colors[0] = (0, 0, 0)  # background

        # Create RGB image array
        img_array = np.zeros((h, w, 3), dtype=np.uint8)
        for pid, color in colors.items():
            img_array[rect == pid] = color

        img = Image.fromarray(img_array, 'RGB')
        return img
    
    def surface_to_image2(self):
        """
        Converts the sphere surface to a rectangle and returns it as an image.
        Each plate ID is assigned a distinguishable color.
        """
        rect = self.surface.to_rectangle2()
        # rect = self.surface.surface # For testing without transformation
        h, w = rect.shape

        # Assign colors for each plate (random but fixed for reproducibility)
        np.random.seed(42)
        plate_ids = [plate.plate_id for plate in self.plates]
        colors = {
            pid: tuple(np.random.randint(0, 256, 3)) for pid in plate_ids
        }
        colors[0] = (0, 0, 0)  # background

        # Create RGB image array
        img_array = np.zeros((h, w, 3), dtype=np.uint8)
        for pid, color in colors.items():
            img_array[rect == pid] = color

        img = Image.fromarray(img_array, 'RGB')
        return img
