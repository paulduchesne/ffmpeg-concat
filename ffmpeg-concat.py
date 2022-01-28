# required libraries.

import json
import os
import pathlib
import subprocess
import tqdm

# define functions.

def check_ffmpeg():

    ''' Determine if FFmpeg is available. '''

    try:
        subprocess.call(['ffmpeg', '-version'], stdout=open(os.devnull, 'wb'))
    except:
        raise Exception('FFmpeg does not appear to be installed or on path.')

def location_config(config_path):

    ''' Define and verify input and output locations. '''

    if not config_path.exists():
        raise Exception('Config file could not be found.')

    with open(config_path) as config:
        config = json.load(config)

    input_dir = pathlib.Path(config['input_directory'])
    output_dir = pathlib.Path(config['output_directory'])

    for directory in [input_dir, output_dir]:
        if not directory.exists():
            raise Exception(directory, 'does not exist.')

    return input_dir, output_dir

def prepare_temp(txt, temp):

    ''' Create temp directory and/or remove existing files. '''

    temp.mkdir(exist_ok=True)
    for d in [txt]+[pathlib.Path(temp) / f'{str(x).zfill(4)}.mp4' for x in range(0,99)]:
        if d.exists():
            os.remove(d)

def define_agenda(source):

    ''' Assemble agenda for transcoding. '''

    p = dict()
    accepted_extensions = ['.mp4', '.avi', '.mov']
    directories = [x for x in pathlib.Path(source).iterdir() if x.is_dir() == True]
    for d in directories:
        v = [str(x) for x in d.iterdir() if x.suffix in accepted_extensions]
        p[str(d.stem)] = v

    return p

def normalise_files(txt, temp, agenda):
 
    ''' Normalise source files prior to concatenation. '''

    text_string = list()

    for n, x in enumerate(agenda):
        in_file, out_file = x, temp / f'{str(n).zfill(4)}.mp4'
        ffmpeg_call = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(in_file), str(out_file)]
        subprocess.call(ffmpeg_call, stdout=open(os.devnull, 'wb'))
        formatted_path = str(out_file).replace('\\', '/').replace(' ', '\ ')
        text_string.append(f'file {formatted_path}')

    with open(txt, 'w') as menu:
        menu.write('\n'.join(text_string))

def concat_files(txt, output):

    ''' Concatenate files based on agenda. '''
    
    with open(txt) as validate:
        validate = validate.read()

    if len(validate):
        ffmpeg_call = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(txt), 
                        '-c:v', 'libx264', '-crf', '23', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-filter:v', 
                        'yadif=0:-1:0,scale', '-aspect', '4:3', str(output)]
        subprocess.call(ffmpeg_call, stdout=open(os.devnull, 'wb'))

def process_files(txt, temp, agenda):

    ''' Process agenda, render temp files and then concat. '''

    t = tqdm.tqdm(total=len(agenda))
    
    for a in agenda:
        expected_output = pathlib.Path(out_dir) / f'{a}.mp4'
        if not expected_output.exists():
            prepare_temp(txt, temp)
            normalise_files(txt, temp, agenda[a])
            concat_files(txt, expected_output)

        t.update(1)

    t.close()

if __name__ == "__main__":

    # check FFmpeg is available.
    check_ffmpeg()

    # define input, output paths.
    in_dir, out_dir = location_config(pathlib.Path.cwd() / 'config.json')

    # generate agenda of files to process. 
    agenda = define_agenda(in_dir)

    # process agenda.
    temp_path = pathlib.Path.home() / 'ffmpeg-concat-temp'
    process_files(temp_path / 'concat.txt', temp_path, agenda)

    print('all done.')