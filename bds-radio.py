import os
import ffmpeg
import json
from mpd import MPDClient
from select import select
from transliterate import translit

config = {}

with open('config.json', 'r') as f:
	config = json.load(f)

client = MPDClient()
client.connect(config['mpd_hostname'], int(config['mpd_port']))

if len(config['mpd_password']) > 0:
	client.password(config['mpd_password'])

def _parse_song_name():
	song_data = client.currentsong()

	if 'title' not in song_data or 'artist' not in song_data:
		return os.path.splitext(os.path.basename(song_data['file']))[0]

	title = song_data['title']
	artist = song_data['artist']

	if config['transliterate']:
		title = translit(title, 'ru', reversed=True)
		artist = translit(artist, 'ru', reversed=True)
	
	return '{}\n{}'.format(title, artist)

def _write_song_data():
	with open('song.txt.tmp', 'w') as f:
		f.write(_parse_song_name())

	os.replace('song.txt.tmp', 'song.txt')

youtube_url='{}/{}'.format(config['youtube_url'], config['youtube_key'])

audio = ffmpeg.input(config['audio_url'])
background = ffmpeg.input(config['background'], loop=True, framerate=int(config['framerate']))

text_params = {
	'fontsize': config['font_size'],
	'x': 16,
	'y': 16,
	'reload': True,
	'textfile': 'song.txt',
	'fontcolor': config['font_color']
}

if len(config['font_file']) > 0:
	text_params.update({'fontfile': config['font_file']})

_write_song_data()
client.send_idle()

def _run_ffmpeg():
	process = (
		ffmpeg.concat(background, audio, v=1, a=1)
		.drawtext(**text_params)
		.output(youtube_url, audio_bitrate='320k', video_bitrate='2500k', acodec='aac', format='flv', framerate=int(config['framerate']))
		.run_async()
	)
	return process
	
process = _run_ffmpeg()

while True:
	if select([client], [], [], 0)[0]:
		client.fetch_idle()
		_write_song_data()
		client.send_idle()

	if process.poll():
		process = _run_ffmpeg()