import json
import numpy as np
import cv2
import ast


def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def load_pv_data(csv_path):
    with open(csv_path) as f:
        lines = f.readlines()

    # The first line contains info about the intrinsics.
    # The following lines (one per frame) contain timestamp, focal length and transform PVtoWorld
    n_frames = len(lines) - 1
    frame_timestamps = np.zeros(n_frames, dtype=np.longlong)
    focal_lengths = np.zeros((n_frames, 2))
    pv2world_transforms = np.zeros((n_frames, 4, 4))

    intrinsics_ox, intrinsics_oy, \
        intrinsics_width, intrinsics_height = ast.literal_eval(lines[0])

    for i_frame, frame in enumerate(lines[1:]):
        # Row format is
        # timestamp, focal length (2), transform PVtoWorld (4x4)
        frame = frame.split(',')
        frame_timestamps[i_frame] = int(frame[0])
        focal_lengths[i_frame, 0] = float(frame[1])
        focal_lengths[i_frame, 1] = float(frame[2])
        pv2world_transforms[i_frame] = np.array(
            frame[3:20]).astype(float).reshape((4, 4))

    return (frame_timestamps, focal_lengths, pv2world_transforms,
            intrinsics_ox, intrinsics_oy, intrinsics_width, intrinsics_height)


def load_lut(lut_filename):
    with open(lut_filename, mode='rb') as depth_file:
        lut = np.frombuffer(depth_file.read(), dtype="f")
        lut = np.reshape(lut, (-1, 3))
    return lut


def load_extrinsics(extrinsics_path):
    mtx = np.loadtxt(str(extrinsics_path), delimiter=',').reshape((4, 4))
    return mtx


def load_rig2world_transforms(path):
    transforms = []
    timestamps = []
    with open(path, "r") as f:
        lines = [l.strip() for l in f.readlines()]
    for line in lines:
        value = line.split(",")
        timestamp = int(value[0])
        timestamps.append(timestamp)
        transform_entries = [float(v) for v in value[1:]]
        transform = np.array(transform_entries).reshape((4, 4))
        transforms.append(transform)
    return (timestamps, transforms)


def get_points_in_cam_space(img, lut):
    img = np.tile(img.flatten().reshape((-1, 1)), (1, 3))
    points = img * lut
    remove_ids = np.where(np.sqrt(np.sum(points**2, axis=1)) < 1e-6)[0]
    points = np.delete(points, remove_ids, axis=0)
    points /= 1000.
    return points


def cam2world(points, rig2cam, rig2world):
    homog_points = np.hstack((points, np.ones((points.shape[0], 1))))
    cam2world_transform = rig2world @ np.linalg.inv(rig2cam)
    world_points = cam2world_transform @ homog_points.T
    return world_points.T[:, :3], cam2world_transform


def project_on_pv(points, pv_img, pv2world_transform, focal_length, principal_point):
    height, width, _ = pv_img.shape

    homog_points = np.hstack((points, np.ones(len(points)).reshape((-1, 1))))
    world2pv_transform = np.linalg.inv(pv2world_transform)
    points_pv = (world2pv_transform @ homog_points.T).T[:, :3]

    intrinsic_matrix = np.array([[focal_length[0], 0, width-principal_point[0]], [
        0, focal_length[1], principal_point[1]], [0, 0, 1]])
    rvec = np.zeros(3)
    tvec = np.zeros(3)
    xy, _ = cv2.projectPoints(points_pv, rvec, tvec, intrinsic_matrix, None)
    xy = np.squeeze(xy)
    xy[:, 0] = width - xy[:, 0]
    xy = np.floor(xy).astype(int)

    width_check = np.logical_and(0 <= xy[:, 0], xy[:, 0] < width)
    height_check = np.logical_and(0 <= xy[:, 1], xy[:, 1] < height)
    valid_ids = np.where(np.logical_and(width_check, height_check))[0]

    points = points[valid_ids, :]
    xy = xy[valid_ids, :]

    pos_image = np.zeros((height, width, 3))
    valid_mask = np.zeros((height, width)).astype(bool)
    for i, p in enumerate(xy):
        pos_image[p[1], p[0]] = points[i]
        valid_mask[p[1], p[0]] = True

    return pos_image, valid_mask


rvec = np.zeros(3)
tvec = np.zeros(3)


def project_pos_to_pv(pos, world2pv, intrinsic_matrix, width):
    p = np.hstack((pos, [1]))
    p = world2pv @ p
    xy, _ = cv2.projectPoints(
        p[:3], rvec, tvec, intrinsic_matrix, None)
    xy = np.squeeze(xy)
    xy[0] = width - xy[0]
    xy = np.floor(xy).astype(int)
    return xy