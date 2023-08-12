from pynput import keyboard
import click
import scraper

def on_press(key):
	if key == keyboard.Key.esc:
		click.echo(click.style(f'{key} PRESSED. EXITING...', fg='green', bold=True))
		exit()

@click.command()
@click.argument('anime', nargs=-1, type=click.STRING)
@click.option('-q', '--quality', 'quality', nargs=1, default=720, type=click.INT)
@click.option('-s', '--season', 'season', nargs=1, default=0, type=click.INT)
@click.option('-e', '--episode', 'episode', nargs=1, default=0, type=click.INT)
def downloadAnime(anime, quality, season, episode):
    session_id = scraper.start_session()
    nAnime = ' '.join(anime)
    findAnime = scraper.get_anime_id(nAnime)

    if findAnime is None:
    	click.echo(click.style('anime not found. try again', fg='red', bold=True))
    else:
    	if quality == 0 and season == 0 and episode == 0:
    		with keyboard.Listener(on_press=on_press) as listener:
    			listener.join()
    		click.echo(click.style(
	            '[WARNING] quality not chosen. downloading default quality: 720p', fg='yellow', bold=True))
    		click.echo(click.style(
	            '[WARNING] season not chosen. downloading from default season: 1', fg='yellow', bold=True))
    		click.echo(click.style(
	            '[WARNING] episode not chosen. downloading default episode: 1', fg='yellow', bold=True))

downloadAnime()