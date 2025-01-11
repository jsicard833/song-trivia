import os


def remove():
    # delete the mp3 files in the current directory
    for file in os.listdir():
        if file.endswith('.mp3'):
            os.remove(file)

if __name__ == "__main__":
    remove()