import socket
import json
import os
import random
import sqlite3
from datetime import datetime
import threading

def load_choices():
    if os.path.exists("user_choices.json"):
        with open("user_choices.json", "r") as file:
            return json.load(file)
    return []

def save_choices(choices):
    with open("user_choices.json", "w") as file:
        json.dump(choices, file, indent=4)

def init_db():
    conn = sqlite3.connect("user_choices.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS choices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            day TEXT,
            activity TEXT,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(name, day, activity, score):
    conn = sqlite3.connect("user_choices.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO choices (name, day, activity, score)
        VALUES (?, ?, ?, ?)
    ''', (name, day, activity, score))
    conn.commit()
    conn.close()

def clear_data():
    # Clear JSON data
    with open("user_choices.json", "w") as file:
        json.dump([], file, indent=4)

    # Clear SQLite data
    conn = sqlite3.connect("user_choices.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM choices')
    conn.commit()
    conn.close()

def get_winner_from_json():
    choices = load_choices()
    print("Loaded choices from JSON:", choices)  # Debug statement
    user_scores = {}
    for choice in choices:
        name = choice["name"]
        score = choice["score"]
        if name in user_scores:
            user_scores[name] += score
        else:
            user_scores[name] = score
    print("User scores:", user_scores)  # Debug statement
    if user_scores:
        winner = max(user_scores, key=user_scores.get)
        return winner, user_scores[winner]
    return None, 0

def handle_client(conn, addr):
    print(f"Connected by {addr}")


    try:
        while True:
            try:
                # Ask the client for their name
                conn.sendall(b'Whats your name?\n')
                name = conn.recv(1024).decode('utf-8').strip()
                print(f"Client's name: {name}")

                # Load existing choices
                choices = load_choices()

                # Check if the user already exists
                user_exists = False
                for user in choices:
                    if user["name"] == name:
                        user_data = user
                        conn.sendall(f"Welcome back, {name}!\n".encode('utf-8'))
                        user_exists = True
                        break
                if not user_exists:
                    user_data = {"name": name}
                    conn.sendall(f"Hello, {name}!\n".encode('utf-8'))

                current_day = datetime.now().strftime("%A")
                print(f"Current day: {current_day}")

                # Define activities for each day
                activities_by_day = {
                    "Sunday": ["Clean the room", "Read a book", "Prepare meals for the week"],
                    "Monday": ["Wash the car", "Walk with the dog", "Cook a meal", "Laundry"],
                    "Tuesday": ["Exercise", "Clean the house", "Work on a hobby", "Wash the car"],
                    "Wednesday": ["Walk with the dog", "Clean the house", "Bake a cake", "Wash the dishes"],
                    "Thursday": ["Read a book", "Cook a meal", "Do yoga"],
                    "Friday": ["Read a book", "Exercise", "Clean the house"],
                    "Saturday": ["Prepare meals for the week", "Visit friends", "Play with little brother"]
                }
                activities = activities_by_day[current_day]

                # Send list of activities to the client
                activities_message = f"Today is {current_day}. Please choose an activity:(each activity give you a points)\n" + "\n".join([f"{i+1}. {activity}" for i, activity in enumerate(activities)]) + "\n"
                conn.sendall(activities_message.encode('utf-8'))

                # Receive the chosen activity
                activity_index = int(conn.recv(1024).decode('utf-8').strip()) - 1
                chosen_activity = activities[activity_index]
                print(f"Activity chosen by the client: {chosen_activity}")

                # Generate a random score between 1 and 9
                chosen_score = random.randint(1, 9)

                # Acknowledge the choices
                acknowledgment = f"Great! Enjoy in your {current_day} with the activity that you choose: '{chosen_activity}',\nThis activity give you {chosen_score} points to you weekly score!.\n"
                conn.sendall(acknowledgment.encode('utf-8'))

                # Update the user's choices in the data
                new_user_data = {
                    "name": name,
                    "day": current_day,
                    "activity": chosen_activity,
                    "score": chosen_score
                }
                choices.append(new_user_data)

                # Save updated choices to JSON file
                save_choices(choices)

                # Save to SQLite database
                save_to_db(name, current_day, chosen_activity, chosen_score)

                # Ask if there is another user
                conn.sendall(b'\nIs there another family member who wants to register? (yes/no):')
                another_user = conn.recv(1024).decode('utf-8').strip().lower()
                if another_user != 'yes':
                    break
            except socket.timeout:
                print("Connection timed out.")
                break
            except KeyboardInterrupt:
                conn.close()
                print("Server interrupted and closed.")

        # Check the day of the week
        if current_day == "Saturday":
            conn.sendall(b"It's Saturday today, let's check who is the winner...\n")
            winner, total_score = get_winner_from_json()
            print("Winner:", winner, "Total score:", total_score)  # Debug statement
            if winner:
                winner_message = f"The winner is '{winner}' with a total score of '{total_score}'.\n"
                conn.sendall(winner_message.encode('utf-8'))
                # Clear the data after announcing the winner
                clear_data()
            else:
                conn.sendall(b"No scores recorded.\n")
            conn.sendall(b"Goodbye!\n")
        else:
            conn.sendall(b"\nSee you in the next day, Just to let you know, In Saturday we will know who is the winner of this week!.\n")
            conn.sendall(b"Goodbye!\n")

        conn.close()
    except KeyboardInterrupt:
        conn.close()
        print("Server interrupted and closed.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.close()

def start_server():
    init_db()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65431))
    server_socket.listen(5)  # Allow up to 5 connections in the queue
    print("Server is listening on port 65431")
    server_socket.settimeout(30)
    try:
        while True:
            try:
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.start()
                  # Set the timeout to 15 seconds
            
            except socket.timeout as e:
                print(e,': no connections after 30 seconds...')
                server_socket.close()
                break
    except KeyboardInterrupt:
        server_socket.close()
        print("\n>>> Server interrupted and closed... <<<")
    finally:
        pass

if __name__ == "__main__":
    start_server()
