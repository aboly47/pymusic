import os
import pygame
import threading
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from mutagen.mp3 import MP3

console = Console()

class MusicPlayer:  
    def __init__(self):  
        pygame.mixer.init()  
        self.playlist = []  
        self.names_list = []  
        self.current_track_index = 0  
        self.is_playing = False  
        self.is_paused = False  
        self.lock = threading.Lock()  # Lock for thread safety  
        self.condition = threading.Condition(self.lock)  # Condition for pausing/resuming  

    def load_music_from_directory(self, directory):  
        with self.lock:  
            self.playlist = [f for f in os.listdir(directory) if f.endswith('.mp3')]  
            self.playlist = [os.path.join(directory, f) for f in self.playlist]  
            for i in self.playlist:  
                audio = MP3(i)  
                track_title = audio.get('TIT2', f'track {len(self.playlist) + 1}')  # Get title  
                self.names_list.append(str(track_title))  # Store the song name  
            console.print(f"[green]Loaded {len(self.playlist)} tracks from {directory}.[/green]")  

    def play_music(self):  
        if len(self.playlist) == 0:  
            console.print("[red]No music loaded![/red]")  
            return  

 
        self.is_playing = True  
        self.is_paused = False  
        threading.Thread(target=self._play_current_track, daemon=True).start()  

    def _play_current_track(self):  
        while self.is_playing:  
            if self.current_track_index >= len(self.playlist):  
                console.print("[yellow]End of playlist.[/yellow]")  
                self.is_playing = False  
                return  

            track = self.playlist[self.current_track_index]  
            track_name = self.names_list[self.current_track_index]  
            console.print(f"[yellow]Playing:[/yellow] {track_name}")  
            pygame.mixer.music.load(track)  
            pygame.mixer.music.play()  

            while self.is_playing:  
                if self.is_paused:  
                    pygame.mixer.music.pause()  
                    console.print("[yellow]Music paused. Waiting for resume...[/yellow]")  
                    with self.condition:  
                        self.condition.wait()  # Wait until notified to resume  
                    pygame.mixer.music.unpause()  # Unpause after being notified  

                if not pygame.mixer.music.get_busy():  
                    break  # Exit the inner loop to play the next track  

                pygame.time.Clock().tick(10)  # Add a delay in case the loop runs too fast  

            if not self.is_paused:  # Increment index only if not paused  
                self.current_track_index += 1  

    def pause_music(self):  
        if self.is_playing and not self.is_paused:  
            self.is_paused = True  
            console.print("[yellow]Music paused.[/yellow]")  

    def resume_music(self):  
        if self.is_playing and self.is_paused:  
            self.is_paused = False  
            console.print("[yellow]Music resumed.[/yellow]")  
            with self.condition:  
                self.condition.notify()  # Notify the waiting thread to resume  

    def next_track(self):  
        with self.lock:  
            console.print("[yellow]Skipping to next track.[/yellow]")  
            if self.current_track_index < len(self.playlist) - 1:  
                self.current_track_index += 1  
            else:  
                self.current_track_index = 0  
                console.print("[yellow]End of playlist. Skipping to the beginning...[/yellow]")  
        
        self.play_music()  # Just call play_music to start the new track  

    def previous_track(self):  
        with self.lock:  
            console.print("[yellow]Going back to previous track.[/yellow]")  
            if self.current_track_index > 0:  
                self.current_track_index -= 1  # Move to previous track  
            else:  
                self.current_track_index = len(self.playlist) - 1  # Loop to the last track  
                console.print("[yellow]At beginning of playlist. Looping to the last track...[/yellow]")  
        
        self.play_music()  # Just call play_music to start the new track  

    def show_playlist(self):  
        table = Table(title="Playlist")  
        table.add_column("Track", justify="center")  
        for track in self.names_list:  
            table.add_row(track)  
        console.print(table)

def controller(player):
    while True:
        console.print("\n[bold cyan]PYMUSIC[/bold cyan]")
        console.print("[blue]1.[/blue] Load Music from Directory")
        console.print("[blue]2.[/blue] Play Music")
        console.print("[blue]3.[/blue] Pause Music")
        console.print("[blue]4.[/blue] Resume Music")
        console.print("[blue]5.[/blue] Next Track")
        console.print("[blue]6.[/blue] Previous Track")  # Added option for previous track
        console.print("[blue]7.[/blue] Show Playlist")
        console.print("[blue]8.[/blue] Exit")
        choice = Prompt.ask("Choose an option")

        if choice == "1":
            directory = Prompt.ask("Enter the directory containing MP3 files")
            player.load_music_from_directory(directory)
        elif choice == "2":
            player.play_music()
        elif choice == "3":
            player.pause_music()
        elif choice == "4":
            player.resume_music()
        elif choice == "5":
            player.next_track()
        elif choice == "6":  # Handle input for previous track
            player.previous_track()
        elif choice == "7":
            player.show_playlist()
        elif choice == "8":  # Updated menu choice for exit
            console.print("[bold red]Exiting...[/bold red]")
            with player.lock:
                player.is_playing = False  # Stop playback before exiting
                player.condition.notify()  # Wake up the thread if it's waiting
            break
        else:
            console.print("[red]Invalid option![/red]")

if __name__ == "__main__":
    player = MusicPlayer()  # Create an instance of MusicPlayer
    controller_thread = threading.Thread(target=controller, args=(player,), daemon=True)

    controller_thread.start()  # Start the controller thread
    controller_thread.join()  # Wait for the controller thread to finish
