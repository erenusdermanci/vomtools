"""Generate a black/green V icon for VomTools using only stdlib"""
import struct
import os

def create_ico():
    size = 32
    
    # Create RGBA pixel data for 32x32 icon
    pixels = []
    bg = (10, 10, 10, 255)      # Black background
    green = (0, 255, 0, 255)    # Bright green V
    
    for y in range(size):
        row = []
        for x in range(size):
            # Draw V shape
            # Left arm: starts at (4, 4), goes to (16, 28)
            # Right arm: starts at (28, 4), goes to (16, 28)
            
            left_x = 4 + (y - 4) * 12 // 24  # Left arm center
            right_x = 28 - (y - 4) * 12 // 24  # Right arm center
            
            stroke = 3
            
            is_left_arm = y >= 4 and y < 28 and abs(x - left_x) < stroke
            is_right_arm = y >= 4 and y < 28 and abs(x - right_x) < stroke
            
            if is_left_arm or is_right_arm:
                row.append(green)
            else:
                row.append(bg)
        pixels.append(row)
    
    # Convert to BMP format (bottom-up, BGRA)
    bmp_data = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = pixels[y][x]
            bmp_data.extend([b, g, r, a])
    
    # AND mask (all zeros = fully opaque)
    and_mask = bytes((size * size) // 8)
    
    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type=1 (ICO), Count=1
    
    # ICO directory entry
    bmp_size = 40 + len(bmp_data) + len(and_mask)
    ico_entry = struct.pack('<BBBBHHII',
        size,      # Width
        size,      # Height
        0,         # Color palette
        0,         # Reserved
        1,         # Color planes
        32,        # Bits per pixel
        bmp_size,  # Size of image data
        22         # Offset to image data (6 + 16)
    )
    
    # BMP info header (BITMAPINFOHEADER)
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,           # Header size
        size,         # Width
        size * 2,     # Height (doubled for ICO format)
        1,            # Color planes
        32,           # Bits per pixel
        0,            # Compression (BI_RGB)
        len(bmp_data) + len(and_mask),  # Image size
        0, 0,         # Pixels per meter
        0, 0          # Colors
    )
    
    # Write ICO file
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vomtools.ico')
    with open(icon_path, 'wb') as f:
        f.write(ico_header)
        f.write(ico_entry)
        f.write(bmp_header)
        f.write(bmp_data)
        f.write(and_mask)
    
    print(f"Icon saved to: {icon_path}")

if __name__ == "__main__":
    create_ico()
