import os
os.environ["PYOPENGL_PLATFORM"] = "osmesa"
import numpy as np
import trimesh
import pyrender
import glob
import tqdm
import tempfile
import cv2
import argparse
from subprocess import call
from psbody.mesh import Mesh
from utils.rendering import render_mesh_helper

def render_sequence_meshes(audio_fname, sequence_vertices, template, out_path):
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    tmp_video_file = tempfile.NamedTemporaryFile('w', suffix='.mp4', dir=out_path)
    if int(cv2.__version__[0]) < 3:
        writer = cv2.VideoWriter(tmp_video_file.name, cv2.cv.CV_FOURCC(*'mp4v'), 60, (800, 800), True)
    else:
        writer = cv2.VideoWriter(tmp_video_file.name, cv2.VideoWriter_fourcc(*'mp4v'), 60, (800, 800), True)

    num_frames = sequence_vertices.shape[0]
    center = np.mean(sequence_vertices[0], axis=0)
    for i_frame in tqdm.tqdm(range(num_frames)):
        img = render_mesh_helper(Mesh(sequence_vertices[i_frame], template.f), center)
        writer.write(img)
    writer.release()

    video_fname = os.path.join(out_path, 'video.mp4')
    cmd = ('ffmpeg' + ' -i {0} -i {1} -vcodec h264 -ac 2 -channel_layout stereo -pix_fmt yuv420p {2}'.format(
        audio_fname, tmp_video_file.name, video_fname)).split()
    call(cmd)
        
def main():
    parser = argparse.ArgumentParser(description='Voice operated character animation')
    parser.add_argument('--objects_path', default='./animation_output/meshes/', help='Path to generated 3D objects')
    parser.add_argument('--audio_fname', default='./audio/test_sentence.wav', help='Path of input speech sequence')
    parser.add_argument('--out_path', default='./animation_output', help='Output path for video')
    
    args = parser.parse_args()
    
    sequence_fnames = sorted(glob.glob(os.path.join(args.objects_path, '*.obj')))
    if len(sequence_fnames) == 0:
        print('No meshes found')

    sequence_vertices = []
    f = None
    for frame_idx, mesh_fname in enumerate(sequence_fnames):
        frame = Mesh(filename=mesh_fname)
        sequence_vertices.append(frame.v)
        if f is None:
            f = frame.f
    template = Mesh(sequence_vertices[0], f)
    sequence_vertices = np.stack(sequence_vertices)
    render_sequence_meshes(args.audio_fname, sequence_vertices, template, args.out_path)
        
if __name__ == "__main__":
    main()
