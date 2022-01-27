# required libraries.

import json
import os
import pathlib
import subprocess

# check if ffmpeg is callable.

try:
    subprocess.call(['ffmpeg', '-version'], stdout=open(os.devnull, 'wb'))
except:
    raise Exception('FFmpeg does not appear to be installed or on path.')

# pull input/output directories from config file.

config_path = pathlib.Path.cwd() / 'config.json'
if not config_path.exists():
    raise Exception('Config file could not be found.')

with open(config_path) as config:
    config = json.load(config)
    input_dir = config['input_directory']
    output_dir = config['output_directory']

# create playbook of files to generate.

planner = dict()
accepted_extensions = ['.mp4', '.avi', '.mov']
directories = [x for x in pathlib.Path(input_dir).iterdir() if x.is_dir() == True]
for d in directories:
    video_files = [str(x) for x in d.iterdir() if x.suffix in accepted_extensions]
    planner[str(d.stem)] = video_files
    
# if temp location does not exist, create.

temp_path = pathlib.Path.home() / 'ffmpeg-concat-temp'
if not temp_path.exists():
    temp_path.mkdir()

# process batches sequentially.

'''
to be added: try except to allow for issues to crash script.
also logs need to be added
'''

for a in planner:
    expected_output = pathlib.Path(output_dir) / f'{a}.mp4'
    if not expected_output.exists():

        '''
        clean up any temp files.
        actually clean up can be very targetted, 
        as it can just reference name construction eg ffmpeg-concat-001.mp4
        '''

        text_string = list()

        for n, x in enumerate(planner[a]):
            in_file = x
            out_file = temp_path / f'{str(n).zfill(4)}.mp4'
            print(in_file, out_file)

            '''
            after cleanup function added, delete the -y flag    
            '''

            subprocess.call(['ffmpeg', '-y', '-i', str(in_file), str(out_file)], stdout=open(os.devnull, 'wb'))

            '''
            the filepath modification below should be os dependant.
            '''

            clean_out_file = str(out_file).replace('\\', '/').replace(' ', '\ ')
            text_string.append(f'file {clean_out_file}')

        with open(temp_path / 'concat.txt', 'w') as menu:
            menu.write('\n'.join(text_string))

        '''
        this is the actual ffmpeg call:
        ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(textpath_form), 
        '-vcodec', 'libx264', '-crf', '23', '-pix_fmt', 'yuv420p', 
        '-preset', 'slow', '-filter:v', 'yadif=0:-1:0,scale', 
        '-aspect', '4:3', '-an', str(videoout)]
        '''

        ffmpeg_call = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(temp_path / 'concat.txt'), str(expected_output)]
        subprocess.call(ffmpeg_call)