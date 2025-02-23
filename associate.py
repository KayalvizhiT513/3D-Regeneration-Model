import sys
import os
import numpy


def read_file_list(filename):
    """
    Reads a trajectory from a text file.
    
    File format:
    The file format is "stamp d1 d2 d3 ...", where stamp denotes the time stamp (to be matched)
    and "d1 d2 d3.." is arbitrary data (e.g., a 3D position and 3D orientation) associated with this timestamp. 
    
    Input:
    filename -- File name
    
    Output:
    dict -- dictionary of (stamp,data) tuples
    """
    with open(filename) as file:
        data = file.read()
    lines = data.replace(",", " ").replace("\t", " ").split("\n")
    file_list = [[v.strip() for v in line.split(" ") if v.strip() != ""] for line in lines if len(line) > 0 and line[0] != "#"]
    file_list = [(float(l[0]), l[1:]) for l in file_list if len(l) > 1]
    return dict(file_list)


def associate(first_list, second_list, offset, max_difference):
    """
    Associate two dictionaries of (stamp, data). As the time stamps never match exactly, we aim 
    to find the closest match for every input tuple.
    
    Input:
    first_list -- first dictionary of (stamp, data) tuples
    second_list -- second dictionary of (stamp, data) tuples
    offset -- time offset between both dictionaries (e.g., to model the delay between the sensors)
    max_difference -- search radius for candidate generation

    Output:
    matches -- list of matched tuples ((stamp1, data1), (stamp2, data2))
    """
    first_keys = set(first_list.keys())
    second_keys = set(second_list.keys())

    potential_matches = [(abs(a - (b + offset)), a, b) 
                         for a in first_keys 
                         for b in second_keys 
                         if abs(a - (b + offset)) < max_difference]
    potential_matches.sort()
    matches = []
    for diff, a, b in potential_matches:
        if a in first_keys and b in second_keys:
            first_keys.remove(a)
            second_keys.remove(b)
            matches.append((a, b))
    
    matches.sort()
    return matches


if __name__ == '__main__':
    # Set parameters directly in the code
    depth_file = 'depth.txt'
    rgb_file = 'rgb.txt'
    groundtruth_file = 'groundtruth.txt'
    output_file = 'timestamp_map.txt'

    offset = 0  # Time offset
    max_difference = 0.02  # Maximum time difference for matching

    # Read the files
    depth_list = read_file_list(depth_file)
    rgb_list = read_file_list(rgb_file)
    groundtruth_list = read_file_list(groundtruth_file)

    # Associate the depth, rgb, and groundtruth files
    depth_rgb_matches = associate(depth_list, rgb_list, offset, max_difference)
    depth_gt_matches = associate(depth_list, groundtruth_list, offset, max_difference)
    print(f"Found {len(depth_rgb_matches)} depth-rgb matches and {len(depth_gt_matches)} depth-groundtruth matches")

    # List to store matches for depth, rgb, and groundtruth
    depth_rgb_gt_matches = []

    # Match depth-rgb with groundtruth
    for depth_stamp, rgb_stamp in depth_rgb_matches:
        for _, gt_stamp in depth_gt_matches:
            if abs(rgb_stamp - gt_stamp) < max_difference:  # Ensure the rgb_stamp also matches a groundtruth timestamp
                depth_rgb_gt_matches.append((depth_stamp, rgb_stamp, gt_stamp))
                break  # Found a match, no need to check further for this depth_stamp

    # Prepare the output with data
    output_lines = []
    for depth_stamp, rgb_stamp, gt_stamp in depth_rgb_gt_matches:
        # Retrieve the data for each timestamp
        depth_data = " ".join(depth_list[depth_stamp])
        rgb_data = " ".join(rgb_list[rgb_stamp])
        gt_data = " ".join(groundtruth_list[gt_stamp])
        
        # Create a line with timestamp and data for depth, rgb, and groundtruth
        output_lines.append(f"{depth_stamp} {depth_data} {rgb_stamp} {rgb_data} {gt_stamp} {gt_data}\n")

    print("Output line: ", len(output_lines))
    # Save the output to a file
    with open(output_file, 'w') as f:
        f.writelines(output_lines)

    print(f"Output written to {output_file}")

