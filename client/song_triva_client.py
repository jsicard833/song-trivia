import subprocess
import sys
import os

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        if package == "yt_dlp":
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        elif package == "vlc":
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-vlc"])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(package)


# List of required packages
required_packages = ["pygame", "yt_dlp", "pydub", "vlc"]

for package in required_packages:
    install_and_import(package)


import socket
import json
import pygame
import yt_dlp as youtube_dl
import time
from pydub import AudioSegment
import queue
import threading
import vlc


SERVER_IP = '3.135.101.123' 
PORT = 54320   

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT_SIZE = 24


class SongTriviaClient:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Song Trivia")
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.buttons = []
        self.clicked_button = None
        self.players = []
        self.answer = None
        self.answered = False
        self.volume = 50  # Initial volume (50%)
        self.slider_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 50, 200, 20)
        self.slider_handle_rect = pygame.Rect(WIDTH // 2 - 10, HEIGHT - 55, 20, 30)
        self.slider_dragging = False
        self.client_socket = None
        self.message_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()
        self.vlc_player.audio_set_volume(self.volume)
        self.run()

    def __del__(self):
        pygame.quit()
        if self.client_socket:
            self.client_socket.close()

    def run(self):
        name = self.get_name()
        self.confirm_name_screen()
        self.connect_to_server(name)
        self.game_loop()

    def get_name(self):
        input_box = pygame.Rect(0, 0, 300, 32)  # Set a fixed width of 300
        input_box.center = (WIDTH // 2, HEIGHT // 2)
        color_active = pygame.Color('dodgerblue2')
        color = color_active
        text = ''
        done = False
        backspace_held = False
        backspace_timer = 0

        # Create a label
        label_font = pygame.font.Font(None, FONT_SIZE)
        label_text = label_font.render("Enter your name:", True, BLACK)
        label_rect = label_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        done = True
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                        backspace_held = True
                        backspace_timer = pygame.time.get_ticks()
                    else:
                        text += event.unicode
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_BACKSPACE:
                        backspace_held = False

            if backspace_held:
                if pygame.time.get_ticks() - backspace_timer > 200:  # Initial delay
                    text = text[:-1]
                    backspace_timer = pygame.time.get_ticks() - 200  # Faster repeat rate

            self.screen.fill(WHITE)
            self.screen.blit(label_text, label_rect)  # Draw the label
            txt_surface = self.font.render(text, True, BLACK)
            self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(self.screen, color, input_box, 2)
            pygame.display.flip()
            self.clock.tick(30)

    def confirm_name_screen(self):
        # show on screen 'waiting for other player'
        self.screen.fill(WHITE)
        waiting_text = self.font.render('Waiting for other player...', True, BLACK)
        waiting_rect = waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(waiting_text, waiting_rect)
        pygame.display.flip()

    def connect_to_server(self, name: str):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_IP, PORT))
        self.client_socket.sendall(name.encode("utf-8"))
        # Start the socket thread
        threading.Thread(target=self.socket_thread, daemon=True).start()
        # Recieve list of names from the server
        message = self.message_queue.get()
        self.players = json.loads(message)

    def socket_thread(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                self.message_queue.put(data)
            except ConnectionResetError:
                break

    def game_loop(self):
        for i in range(15):
            self.answered = False
            question = self.get_question()
            self.answer = question[4]
            artist = question[5]
            music_start_time = question[6]
            self.buttons = self.create_buttons(question)

            # Start the audio streaming in a separate thread
            threading.Thread(target=self.stream_audio_thread, args=(self.answer + " " + artist + " lyrics", music_start_time), daemon=True).start()

            audio_file = None
            while audio_file is None:
                if not self.audio_queue.empty():
                    audio_file = self.audio_queue.get()
                    self.client_socket.sendall('Ready'.encode("utf-8"))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                if i == 0:
                    self.sound_loading_screen()
                else:
                    self.show_score_screen(player1, player1points, player2, player2points)
                self.clock.tick(30)

            # Wait for a response from the server before starting to play the song
            while True:
                if not self.message_queue.empty():
                    self.message_queue.get()
                    self.play_song(audio_file, music_start_time)
                    break
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()   
                self.clock.tick(30)

            start_time = time.time()

            while True:
                elapsed_time = time.time() - start_time
                remaining_time = 10 - elapsed_time
                if elapsed_time >= 10:
                    if not self.answered:
                        self.client_socket.sendall('None'.encode("utf-8"))
                    else:
                        self.client_socket.sendall(self.clicked_button["label"].encode("utf-8"))
                    data = self.message_queue.get()
                    points = json.loads(data) # formatted as [[player1name, player1points], [player2name, player2points]]
                    player1 = points[0][0]
                    player1points = points[0][1]
                    player2 = points[1][0]
                    player2points = points[1][1]
                    #player3 = points[2][0]
                    #player3points = points[2][1]
                    self.show_score_screen(player1, player1points, player2, player2points)
                    break
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        # Check if any button is clicked
                        for button in self.buttons:
                            if button["rect"].collidepoint(mouse_pos) and not self.answered:
                                # Send the answer to the server
                                self.clicked_button = button
                                self.answered = True
                    self.handle_slider_event(event)

                self.screen.fill(WHITE)
                self.draw_buttons()
                self.draw_slider()
                self.draw_countdown(remaining_time)
                pygame.display.flip()
                self.clock.tick(60)

    def sound_loading_screen(self):
        self.screen.fill(WHITE)
        loading_text = self.font.render('Loading sound...', True, BLACK)
        loading_rect = loading_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(loading_text, loading_rect)
        pygame.display.flip()

    def get_question(self) -> list:
        # Recieve list of questions from the server
        message = self.message_queue.get()
        return json.loads(message)

    def draw_buttons(self):
        button_color = pygame.Color('dodgerblue2')
        button_text_color = WHITE
        button_font = pygame.font.Font(None, FONT_SIZE)

        for button in self.buttons:
            if button == self.clicked_button and self.answered:
                if button['label'] == self.answer:
                    pygame.draw.rect(self.screen, pygame.Color('darkgreen'), button["rect"])
                else:
                    pygame.draw.rect(self.screen, pygame.Color('darkred'), button["rect"])
            elif button['label'] == self.answer and self.answered:
                pygame.draw.rect(self.screen, pygame.Color('darkgreen'), button["rect"])
            else:
                pygame.draw.rect(self.screen, button_color, button["rect"])
            text_surface = button_font.render(button["label"], True, button_text_color)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

    def draw_countdown(self, remaining_time):
        countdown_text = self.font.render(f"Time left: {remaining_time:.1f} seconds", True, BLACK)
        countdown_rect = countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        self.screen.blit(countdown_text, countdown_rect)

    def show_score_screen(self, player1, player1points, player2, player2points):
        self.screen.fill(WHITE)
        score_font = pygame.font.Font(None, 36)
        player1_text = score_font.render(f"{player1}: {player1points} points", True, BLACK)
        player2_text = score_font.render(f"{player2}: {player2points} points", True, BLACK)
        #player3_text = score_font.render(f"{player3}: {player3points} points", True, BLACK)
        player1_rect = player1_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        player2_rect = player2_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        #player3_rect = player3_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        self.screen.blit(player1_text, player1_rect)
        self.screen.blit(player2_text, player2_rect)
        #self.screen.blit(player3_text, player3_rect)
        pygame.display.flip()

    def draw_slider(self):
        pygame.draw.rect(self.screen, BLACK, self.slider_rect)
        pygame.draw.rect(self.screen, pygame.Color('gray'), self.slider_handle_rect)

    def handle_slider_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.slider_handle_rect.collidepoint(event.pos):
                self.slider_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.slider_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.slider_dragging:
                self.slider_handle_rect.x = max(self.slider_rect.x, min(event.pos[0] - self.slider_handle_rect.width // 2, self.slider_rect.x + self.slider_rect.width - self.slider_handle_rect.width))
                self.volume = (self.slider_handle_rect.x - self.slider_rect.x) / (self.slider_rect.width - self.slider_handle_rect.width)
                self.vlc_player.audio_set_volume(int(self.volume * 100))

    def create_buttons(self, question: list) -> list:
        button_width = 500
        button_height = 50
        buttons = [
            {"label": question[0], "rect": pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 100), (button_width, button_height))},
            {"label": question[1], "rect": pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 - 40), (button_width, button_height))},
            {"label": question[2], "rect": pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 + 20), (button_width, button_height))},
            {"label": question[3], "rect": pygame.Rect((WIDTH // 2 - button_width // 2, HEIGHT // 2 + 80), (button_width, button_height))}
        ]
        return buttons
        
    def stream_audio_from_youtube(self, query: str):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in results:
                for entry in results['entries']:
                    try:
                        stream_url = entry['url']
                        return stream_url
                    except Exception as e:
                        print(f"Failed to get stream URL for {entry['title']}: {e}")
        return None
    
    def stream_audio_thread(self, query: str, start_time: int):
        stream_url = self.stream_audio_from_youtube(query)
        self.audio_queue.put(stream_url)
            
    '''def play_song(self, audio_file, start_time):
        # Stop any currently playing music
        pygame.mixer.music.stop()

        #unload any previous audio
        pygame.mixer.music.unload()

        audio = AudioSegment.from_file(audio_file)
        duration_ms = len(audio)
        start_ms = start_time
        if start_ms + 30000 > duration_ms:
            start_ms = 0
        audio_segment = audio[start_ms:start_ms + 15000]  # Extract a 15-second segment
        temp_file = "temp.mp3"
        audio_segment.export(temp_file, format="mp3")

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()'''
    
    def play_song(self, stream_url, start_time):
        # Stop any currently playing music
        self.vlc_player.stop()

        media = self.vlc_instance.media_new(stream_url)
        self.vlc_player.set_media(media)
        self.vlc_player.play()
        self.vlc_player.set_time(start_time)


def main():
    SongTriviaClient()

if __name__ == "__main__":
    main()