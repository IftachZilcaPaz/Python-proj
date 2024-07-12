import socket
import platform
import os

def start_client(port=65431):
    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', port))

        while True:
            try:
                os_type = platform.system()
                if os_type == "Windows":
                    os.system("cls")
                else:
                    os.system("clear")
                # Receive and respond to the server
                response = client_socket.recv(1024).decode('utf-8')
                print(response)
                if 'Goodbye!' in response:
                    break
                if 'Whats your name?' in response:
                    name = input()
                    client_socket.sendall(name.encode('utf-8'))
                #elif 'Please choose a day:' in response:
                 #   day_choice = input("Enter the number of the day of your choice: ")
                  #  client_socket.sendall(day_choice.encode('utf-8'))
                elif 'Please choose an activity:' in response:
                    activity_choice = input("Enter the number of the activity that you want to choose for today: ")
                    client_socket.sendall(activity_choice.encode('utf-8'))
                elif 'Is there another family member who wants to register?' in response:
                    another_user = input()
                    client_socket.sendall(another_user.encode('utf-8'))
                    if another_user.lower() != 'yes':
                        break
            except KeyboardInterrupt:
                print("\n>>> client interrupted and closed... <<<")
                client_socket.close()
        
        # Receive any final messages
        while True:
            try:
                response = client_socket.recv(1024).decode('utf-8')
                if response:
                    print(response)
                else:
                    break
            except:
                break
        break

if __name__ == "__main__":
    start_client()
