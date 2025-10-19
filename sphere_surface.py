import numpy as np

class SphereSurface:
    def __init__(self, equator_length):
        self.equator_length = equator_length
        # Memory-efficient array: using uint8 for pixel data
        self.surface = np.zeros((np.round(equator_length/2).astype(int), equator_length), dtype=np.uint8)
        self.pixel_lengths = self.latitude_pixel_lengths()
        self.pixel_offsets = self.latitude_pixel_offsets()

    def latitude_pixel_lengths(self):
        """
        Returns a 1D numpy array of pixel lengths for each latitude.
        The pixel length at latitude y is proportional to cos(theta),
        where theta is the latitude angle from the equator.
        """
        latitudes = np.linspace(-np.pi/2, np.pi/2, np.round(self.equator_length/2).astype(int))
        pixel_lengths = np.round(self.equator_length * np.cos(latitudes)).astype(int)
        pixel_lengths[pixel_lengths < 1] = 1  # Ensure minimum length is 1
        return pixel_lengths
    
    def latitude_pixel_offsets(self):
        """
        Returns a 1D numpy array of starting offsets for each latitude.
        The offset is calculated to center the pixels for each latitude.
        """
        offsets = np.zeros(np.round(self.equator_length/2).astype(int), dtype=int)
        for y in range(len(offsets)):
            offsets[y] = (self.equator_length - self.pixel_lengths[y]) // 2
        return offsets

    def push_front(self, arr, value, index, times):
        """
        Pushes a value to the front of the array at the specified index,
        x times.
        """
        for i in range(times):
            arr[index] = value
            index += 1

    def push_back(self, arr, value, index, times):
        """
        Pushes a value to the back of the array at the specified index,
        x times.
        """
        for i in range(times):
            arr[index] = value
            index -= 1

    def stretch_latitude(self, srs_row, target_length):
        """
        Stretches a latitude row to the target length by duplicating pixels.
        """
        current_length = len(srs_row)
        print(f"Stretching from {current_length} to {target_length}")
        stratched_row = np.zeros(target_length, dtype=srs_row.dtype)
        elements_set = 0
        for i in range(current_length):
            mul_factor = np.round((target_length-elements_set)/(current_length-i)).astype(int)
            if mul_factor+elements_set > target_length:
                mul_factor = target_length - elements_set
            self.push_front(stratched_row, srs_row[i], elements_set, mul_factor)
            elements_set += mul_factor
        return stratched_row

    def to_rectangle(self):
        """
        Transforms the sphere surface to a rectangle by stretching each latitude's
        pixels to the full equator_length.
        Returns a new numpy array of shape (equator_length, equator_length).
        """
        rect = np.zeros((np.round(self.equator_length/2).astype(int), self.equator_length), dtype=np.uint8)
        for y in range(np.round(self.equator_length/2).astype(int)):
            src_row = self.surface[y, self.pixel_offsets[y]:self.pixel_offsets[y]+self.pixel_lengths[y]]
            # Stretch src_row to equator_length
            stretched_row = self.stretch_latitude(src_row, self.equator_length)
            rect[y] = stretched_row
        return rect
    
    def to_rectangle2(self):
        """
        Alternative method to transform the sphere surface to a rectangle.
        """
        return self.surface

    def count_nonzero(self):
        """
        Counts the number of pixels equal to 'value' within the valid pixel range for each latitude.
        """
        count = 0
        for y in range(np.round(self.equator_length/2).astype(int)):
            count += np.count_nonzero(self.surface[y][self.pixel_offsets[y]:self.pixel_offsets[y]+self.pixel_lengths[y]])
        return count

    def size(self):
        """
        Returns the total number of valid pixels on the sphere surface.
        """
        return int(np.sum(self.pixel_lengths))
    
    def set_surface_default(self, value):
        """
        Sets the surface to a default pattern for testing.
        """
        for y in range(np.round(self.equator_length/2).astype(int)):
            length = self.pixel_lengths[y]
            self.surface[y, self.pixel_offsets[y]:self.pixel_offsets[y]+length] = value

# Example usage:
# sphere = SphereSurface(512)
# rectangle = sphere.to_rectangle()