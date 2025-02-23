import os
from pathlib import Path
import math
from PIL import Image
import numpy as np
from scipy.spatial.transform import Rotation as R

# Camera parameters
focalLength = 525.0
centerX = 319.5
centerY = 239.5
scalingFactor = 5000.0

# Input and output configuration (hardcoded)
file_list = "timestamp_map.txt"  # Path to the input file
output_dir = Path("output_ply")  # Directory where PLY files will be saved

# Define a function to convert quaternion to rotation matrix
def quaternion_to_rotation_matrix(qx, qy, qz, qw):
    """
    Convert quaternion to a rotation matrix.
    """
    r = R.from_quat([qx, qy, qz, qw])
    return r.as_matrix()

# Apply transformation using the quaternion and translation
def apply_transformation(x, y, z, rotation_matrix, translation):
    """
    Apply translation and rotation to a 3D point.
    """
    point = np.array([x, y, z])
    transformed_point = np.dot(rotation_matrix, point) + translation
    return transformed_point  # Return the transformed x, y, z components

# Generate point cloud in PLY format from RGB and Depth images
def generate_pointcloud(rgb_file, depth_file, ply_file, tx, ty, tz, qx, qy, qz, qw):
    """
    Generate a colored point cloud in PLY format from color and depth images
    with transformation applied using quaternion and translation.
    """
    rgb = Image.open(rgb_file)
    depth = Image.open(depth_file)
    
    if rgb.size != depth.size:
        raise Exception(f"Color and depth images do not have the same resolution: {rgb_file}, {depth_file}")
    if rgb.mode != "RGB":
        raise Exception(f"Color image is not in RGB format: {rgb_file}")
    if depth.mode[0] != "I":
        raise Exception(f"Depth image is not in intensity format: {depth_file}")
    
    # Convert quaternion to rotation matrix
    rotation_matrix = quaternion_to_rotation_matrix(qx, qy, qz, qw)
    translation = np.array([tx, ty, tz])

    points = []
    for v in range(rgb.size[1]):
        for u in range(rgb.size[0]):
            color = rgb.getpixel((u, v))
            Z = depth.getpixel((u, v)) / scalingFactor
            if Z == 0: 
                continue
            X = (u - centerX) * Z / focalLength
            Y = (v - centerY) * Z / focalLength

            # Apply the transformation (rotation + translation)
            transformed_point = apply_transformation(X, Y, Z, rotation_matrix, translation)

            points.append(f"{transformed_point[0]} {transformed_point[1]} {transformed_point[2]} {color[0]} {color[1]} {color[2]} 0\n")
    print(len(points), len(points[0]))
    print("---------------------------------------------")
    
    with open(ply_file, "w") as file:
        file.write(f'''ply
format ascii 1.0
element vertex {len(points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
property uchar alpha
end_header
{''.join(points)}
''')

# Process the file list and generate point clouds for each pair
def process_file_list(file_list, output_dir):
    """
    Process each line of the input file and generate PLY files for RGB and depth image pairs.
    """
    with open(file_list, "r") as f:
        lines = f.readlines()
    
    point_cloud_count = 0
    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) != 12:
            raise ValueError(f"Unexpected format in line: {line}")
        
        # Extract data from each line
        depth_file = parts[1]
        rgb_file = parts[3]
        tx, ty, tz = float(parts[5]), float(parts[6]), float(parts[7])
        qx, qy, qz, qw = float(parts[8]), float(parts[9]), float(parts[10]), float(parts[11])

        # Resolve file paths
        depth_file = Path(depth_file)
        rgb_file = Path(rgb_file)
        ply_file = output_dir / f"point_cloud{point_cloud_count}.ply"
        
        print(f"Processing Depth: {depth_file}, RGB: {rgb_file} -> PLY: {ply_file}")
        generate_pointcloud(rgb_file, depth_file, ply_file, tx, ty, tz, qx, qy, qz, qw)
        point_cloud_count += 1

if __name__ == "__main__":
    # Create output directory if it does not exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process the file list and generate point clouds
    process_file_list(file_list, output_dir)
