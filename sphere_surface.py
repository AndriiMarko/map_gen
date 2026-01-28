import numpy as np

class End_of_aray(Exception):
    pass


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
        #print(f"Stretching from {current_length} to {target_length}")
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

    def get_min_max(self):
        """
        Returns the minimum and maximum pixel values on the surface.
        """
        mn = None
        mx = None
        for y in range(np.round(self.equator_length/2).astype(int)):
            length = self.pixel_lengths[y]
            row = self.surface[y, self.pixel_offsets[y]:self.pixel_offsets[y]+length]
            row_min = row.min()
            row_max = row.max()
            if mn is None or row_min < mn:
                mn = row_min
            if mx is None or row_max > mx:
                mx = row_max
        return mn, mx
    
    def get(self, lon, lat):
        """
        Get the pixel value at the specified longitude and latitude.
        """
        longitude = lon % np.round(self.equator_length/2).astype(int)
        if lat < self.pixel_offsets[longitude]:
            end_lat = self.pixel_offsets[longitude] + self.pixel_lengths[longitude]
            negative_offset = self.pixel_offsets[longitude] - lat
            latitude = end_lat - negative_offset
        elif lat >= self.pixel_offsets[longitude] + self.pixel_lengths[longitude]:
            latitude = ((lat - self.pixel_offsets[longitude]) % self.pixel_lengths[longitude]) + self.pixel_offsets[longitude]
        else:
            latitude = lat
        return self.surface[longitude, latitude]
    
    def set(self, lon, lat, value):
        """
        Get the pixel value at the specified longitude and latitude.
        """
        longitude = lon % np.round(self.equator_length/2).astype(int)
        if lat < self.pixel_offsets[longitude]:
            end_lat = self.pixel_offsets[longitude] + self.pixel_lengths[longitude]
            negative_offset = self.pixel_offsets[longitude] - lat
            latitude = end_lat - negative_offset
        elif lat >= self.pixel_offsets[longitude] + self.pixel_lengths[longitude]:
            latitude = ((lat - self.pixel_offsets[longitude]) % self.pixel_lengths[longitude]) + self.pixel_offsets[longitude]
        else:
            latitude = lat
        self.surface[longitude, latitude] = value

    def square_filter(self, lon, lat, size):
        """
        Applies a square filter of given size centered at (lon, lat).
        Returns the average value within the square.
        """
        half_size = size // 2
        total = 0
        count = 0
        for dlon in range(-half_size, half_size + 1):
            for dlat in range(-half_size, half_size + 1):
                if (lon + dlon) < 0 or (lon + dlon) > self.equator_length/2:
                    continue
                total += int(self.get(lon + dlon, lat + dlat))
                count += 1
        return total // count

    def next(self, lon, lat, direction):
        """
        Move one step from (lon, lat) in direction and return new (lon, lat).

        direction may be:
          - a tuple/list (dlon, dlat) of ints, or
          - one of strings: 'N','S','E','W','NE','NW','SE','SW' (case-insensitive).

        Longitude wraps (cylindrical). Latitude is adjusted to stay within the valid
        pixel range for the target longitude using the same rules as get()/set().
        """
        # normalize inputs
        nlon = int(lon)
        nlat = int(lat)

        dm = {
            'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1),
            'NE': (-1, 1), 'NW': (-1, -1), 'SE': (1, 1), 'SW': (1, -1)
        }
        key = direction.upper()
        if key not in dm:
            raise ValueError(f"unknown direction: {direction}")
        dlon, dlat = dm[key]

        if self.endline_check(nlon, nlat, direction):
            try:
                #print(f"End of line reached at lon={nlon}, lat={nlat}, direction={direction}")
                nlon, nlat = self.next_line(nlon, nlat, direction)
                #print(f"Wrapped to lon={nlon}, lat={nlat} after endline")
                return int(nlon), int(nlat)
            except End_of_aray:
                raise End_of_aray(f"{direction} scan ended")


        num_lon = np.round(self.equator_length / 2).astype(int)

        nlon = nlon + dlon
        # compute tentative latitude and then adjust to valid range for nlon
        tentative = nlat + dlat
        off = int(self.pixel_offsets[nlon])
        length = int(self.pixel_lengths[nlon])

        if tentative < off:
            # went above valid range -> wrap from the end of valid range
            end_lat = off + length
            negative_offset = off - tentative
            nlat = end_lat - negative_offset
        elif tentative >= off + length:
            # went below valid range -> wrap within valid length
            nlat = ((tentative - off) % length) + off
        else:
            nlat = tentative
        #print(f"Moved to lon={nlon}, lat={nlat}, offset={off}, length={length}")
        return int(nlon), int(nlat)

    def next_line(self, lon, lat, direction):
        nlon = 0
        nlat = 0
        num_lon = np.round(self.equator_length / 2).astype(int)
        if direction == 'N':
            nlat = lat + 1
            if nlat == self.equator_length:
                raise End_of_aray("N scan ended")
            else:
                for i in range(num_lon-1, -1, -1):
                    off = int(self.pixel_offsets[i])
                    length = int(self.pixel_lengths[i])
                    if off <= nlat < off + length:
                        nlon = i
                        break

        elif direction == 'S':
            nlat = lat + 1
            if nlat == self.equator_length:
                raise End_of_aray("S scan ended")
            else:
                for i in range(num_lon):
                    off = int(self.pixel_offsets[i])
                    length = int(self.pixel_lengths[i])
                    if off <= nlat < off + length:
                        nlon = i
                        break

        elif direction == 'E':
            nlon = lon + 1
            if nlon >= num_lon:
                raise End_of_aray("E scan ended")
            else:
                nlat = self.pixel_offsets[nlon]

        elif direction == 'W':
            nlon = lon + 1
            if nlon >= num_lon:
                raise End_of_aray("w scan ended")
            else:
                nlat = self.pixel_offsets[nlon] + self.pixel_lengths[nlon] - 1

        elif direction == 'NE':
            nlon = lon
            nlat = lat
            if nlat == self.equator_length - 1:
                raise End_of_aray("NE scan ended")
            nlat += 1
            for i in range(max(num_lon - lon, nlat), -1, -1):
                nlon += 1
                nlat -= 1
                if nlon >= num_lon/2:
                    if nlon >= num_lon:
                        nlon -= 1
                        nlat += 1
                        break
                    off = int(self.pixel_offsets[nlon])
                    length = int(self.pixel_lengths[nlon])
                    if off > nlat or nlat >= off + length:
                        nlon -= 1
                        nlat += 1
                        break

        elif direction == 'SE':
            nlon = lon
            nlat = lat
            if nlat == self.equator_length - 1:
                raise End_of_aray("NE scan ended")
            nlat += 1
            for i in range(max(lon, lat), -1, -1):
                nlon -= 1
                nlat -= 1
                if nlon == 0:
                    break
                if nlon <= num_lon/2:
                    off = int(self.pixel_offsets[nlon])
                    length = int(self.pixel_lengths[nlon])
                    if off > nlat or nlat >= off + length:
                        nlon += 1
                        nlat += 1
                        break

        elif direction == 'NW':
            nlon = lon
            nlat = lat
            if nlat == 0:
                raise End_of_aray("NE scan ended")
            nlat -= 1
            for i in range(max(num_lon - lon, self.equator_length - nlat), -1, -1):
                nlon += 1
                nlat += 1
                if nlon >= num_lon/2:
                    if nlon >= num_lon:
                        nlon -= 1
                        nlat -= 1
                        break
                    off = int(self.pixel_offsets[nlon])
                    length = int(self.pixel_lengths[nlon])
                    if off > nlat or nlat >= off + length:
                        nlon -= 1
                        nlat -= 1
                        break

        elif direction == 'SW':
            nlon = lon
            nlat = lat
            if nlat == 0:
                raise End_of_aray("NE scan ended")
            nlat -= 1
            for i in range(max(lon, self.equator_length - lat), -1, -1):
                nlon -= 1
                nlat += 1
                if nlon == 0:
                    break
                off = int(self.pixel_offsets[nlon])
                length = int(self.pixel_lengths[nlon])
                if off > nlat or nlat >= off + length:
                    nlon += 1
                    nlat -= 1
                    break

        return int(nlon), int(nlat)


    def start(self, direction):
        """
        Return a random valid starting coordinate (lon, lat) on the sphere surface.
        """
        nlat = 0
        nlon = 0
        num_lon = np.round(self.equator_length / 2).astype(int)
        if direction in ('N', 'S', 'NE', 'SE'):
            nlat = 0
            for lon in range(num_lon):
                off = int(self.pixel_offsets[lon])
                if off == nlat:
                    nlon = lon
        elif direction in ('W', 'E'):
            nlon = 0
            nlat = int(self.pixel_offsets[nlon])
        elif direction in ('NW', 'SW'):
            nlat = self.equator_length-1
            for lon in range(num_lon):
                off = int(self.pixel_offsets[lon])
                length = int(self.pixel_lengths[lon])
                if off+length == nlat:
                    nlon = lon
        else:
            raise ValueError(f"unknown direction: {direction}")
        return nlon, nlat
    
    def endline_check(self, lon, lat, direction):
        """
        Check if the next step in the given direction would go out of bounds.
        """
        num_lon = np.round(self.equator_length / 2).astype(int)
        off = int(self.pixel_offsets[lon])
        length = int(self.pixel_lengths[lon])
        #print(f"Checking endline at lon={lon}, lat={lat}, offset={off}, length={length}, num_lon={num_lon}")
        if direction == 'S':
            if lon == num_lon - 1:    
                return True
            if lon >= num_lon/2:
                off = int(self.pixel_offsets[lon+1])
                length = int(self.pixel_lengths[lon+1])
                if lat <= off or lat >= off + length - 1:
                    return True
            else:
                return False
        elif direction == 'N':
            if lon == 0:    
                return True
            if lon <= num_lon/2:
                off = int(self.pixel_offsets[lon-1])
                length = int(self.pixel_lengths[lon-1])
                if lat <= off or lat >= off + length - 1:
                    return True
            else:
                return False
        elif direction == 'E':
            if lat == off+length - 1:
                return True
            else:
                return False
        elif direction == 'W':
            if lat == off:
                return True
            else:
                return False
        elif direction == 'NE':
            if lon == 0 or lat == (self.equator_length - 1):    
                return True
            if lon <= num_lon/2:
                off = int(self.pixel_offsets[lon-1])
                length = int(self.pixel_lengths[lon-1])
                if lat + 1 >= off + length - 1:
                    return True
                if lat + 1 < off:
                    return True
            else:
                return False
        elif direction == 'NW':
            if lon == 0 or lat == 0:    
                return True
            if lon <= num_lon/2:
                off = int(self.pixel_offsets[lon-1])
                length = int(self.pixel_lengths[lon-1])
                if lat - 1 < off:
                    return True
                if lat - 1 >= off + length - 1:
                    return True
            else:
                return False
        elif direction == 'SE':
            if lon == (num_lon - 1) or lat == (self.equator_length - 1):    
                return True
            if lon >= num_lon/2:
                off = int(self.pixel_offsets[lon+1])
                length = int(self.pixel_lengths[lon+1])
                if lat + 1 >= off + length - 1:
                    return True
                if lat + 1 < off:
                    return True
            else:
                return False
        elif direction == 'SW':
            if lon == (num_lon - 1) or lat == 0:    
                return True
            if lon >= num_lon/2:
                off = int(self.pixel_offsets[lon+1])
                length = int(self.pixel_lengths[lon+1])
                if lat - 1 < off:
                    return True
                if lat - 1 >= off + length - 1:
                    return True
            else:
                return False


# Example usage:
# sphere = SphereSurface(512)
# rectangle = sphere.to_rectangle()