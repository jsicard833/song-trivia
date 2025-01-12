import spotify
import random
import server
import sys

class SongTriviaServer:
    def __init__(self):
        # Spotify Developer Credentials
        self.playlist_url = self.get_playlist_url()
        self.spotify = spotify.Spotify(self.playlist_url)
        try:
            self.track_dict = self.spotify.get_playlist_tracks(self.spotify.playlist_id)
        except Exception as e:
            sys.exit(f"Error: {e}")
        self.chosen_songs = []
        self.correct_answer = ''
        self.player_scores = {}

    def get_playlist_url(self) -> str:
        # Input: Spotify playlist URL
        return input("Enter the Spotify playlist URL: ")

    def run(self) -> None:
        my_server = server.Server()
        my_server.start()
        self.send_names_to_clients(my_server)
        for _ in range(15):
            question = self.create_question_list()
            #print(self.correct_answer)
            #print(self.track_dict[self.correct_answer])
            start_time = self.get_random_start_time()
            my_server.send_list_to_clients(question + [self.correct_answer, self.track_dict[self.correct_answer], start_time])
            my_server.get_ready_from_clients()
            my_server.broadcast("START")
            answers = my_server.get_answer_from_clients()
            for client_name, client_answer in answers:
                print(f"{client_name}: {client_answer}")
            player_scores = self.calculate_scores(answers)
            self.send_scores_to_clients(my_server, player_scores)
        my_server.close_connections()

    def send_scores_to_clients(self, my_server: server.Server, player_scores: dict) -> None:
        # Send the scores of the players to the clients
        scores_list = [(name, score) for name, score in player_scores.items()]
        my_server.send_list_to_clients(scores_list)

    def send_names_to_clients(self, my_server: server.Server) -> None:
        # Send the names of the players to the clients
        names = [name for _, _, name in my_server.clients]
        my_server.send_list_to_clients(names)

    def calculate_scores(self, answers: list) -> dict:
        for player, answer in answers:
            if answer == self.correct_answer:
                self.player_scores[player] = self.player_scores.get(player, 0) + 1
            else:
                self.player_scores[player] = self.player_scores.get(player, 0)
        return self.player_scores

    def create_question_list(self) -> list:
        # Choose a random song from the playlist that hasn't been asked yet
        self.correct_answer = random.choice(list(self.track_dict.keys()))
        # Check if there are any songs left to ask
        if len(self.chosen_songs) == len(self.track_dict):
            self.chosen_songs = []
        while self.correct_answer in self.chosen_songs:
            self.correct_answer = random.choice(list(self.track_dict.keys()))
        self.chosen_songs.append(self.correct_answer)
        # Choose 3 other random songs from the playlist
        other_songs = random.sample(list(self.track_dict.keys()), 3)
        # Check that the other songs are not the same as the correct answer
        while self.correct_answer in other_songs:
            other_songs = random.sample(list(self.track_dict.keys()), 3)
        # Create a list of the 4 songs
        songs = [self.correct_answer] + other_songs
        # Shuffle the list
        random.shuffle(songs)
        return songs
    
    def get_random_start_time(self) -> int:
        # Get a random start time for the song
        song_length = self.spotify.get_song_length(self.correct_answer)
        if song_length:
            start_time = random.randint(0, song_length - 30000) # 30 seconds before the end of the song
            return start_time
        else:
            return 0


def main() -> None:
    game_server = SongTriviaServer()
    game_server.run()

if __name__ == "__main__":
    main()