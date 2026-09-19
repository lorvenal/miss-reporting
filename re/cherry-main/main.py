import requests
import colorama
import ctypes
from colorama import Fore, Style
from threading import Thread

colorama.init(autoreset=True)

PURPLE = Fore.MAGENTA
RED = Fore.RED
GREEN = Fore.GREEN
BRIGHT = Style.BRIGHT

def main():

    ctypes.windll.kernel32.SetConsoleTitleW("cherry | HeartSec")
    os_system = __import__('os').system
    os_system('cls')

    banner_lines = [
        f"{BRIGHT}{PURPLE} $$$$$$\\  $$\\                                               ",
        f"{BRIGHT}{PURPLE}$$  __$$\\ $$ |                                              ",
        f"{BRIGHT}{PURPLE}$$ /  \\__|$$$$$$$\\   $$$$$$\\   $$$$$$\\   $$$$$$\\  $$\\   $$\\ ",
        f"{BRIGHT}{PURPLE}$$ |      $$  __$$\\ $$  __$$\\ $$  __$$\\ $$  __$$\\ $$ |  $$ |",
        f"{BRIGHT}{PURPLE}$$ |      $$ |  $$ |$$$$$$$$ |$$ |  \\__|$$ |  \\__|$$ |  $$ |",
        f"{BRIGHT}{PURPLE}$$ |  $$\\ $$ |  $$ |$$   ____|$$ |      $$ |      $$ |  $$ |",
        f"{BRIGHT}{PURPLE}\\$$$$$$  |$$ |  $$ |\\$$$$$$$\\ $$ |      $$ |      \\$$$$$$$ |",
        f"{BRIGHT}{PURPLE} \\______/ \\__|  \\__| \\_______|\\__|      \\__|       \\____$$ |",
        f"{BRIGHT}{PURPLE}                                                  $$\\   $$ |",
        f"{BRIGHT}{PURPLE}                                                  \\$$$$$$  |",
        f"{BRIGHT}{PURPLE}                                                   \\______/ ",
        f"{BRIGHT}{PURPLE} x > {Fore.RESET}Options\n"
    ]
    for line in banner_lines:
        print(line)

    print(
        f"{BRIGHT}{RED} {{1}} > {Fore.RESET}illegal Content {BRIGHT}{PURPLE}::{Fore.RESET} 1\n"
        f"{BRIGHT}{RED} {{2}} > {Fore.RESET}Harassment {BRIGHT}{PURPLE}::{Fore.RESET} 2\n"
        f"{BRIGHT}{RED} {{3}} > {Fore.RESET}Spam or Phishing Links {BRIGHT}{PURPLE}::{Fore.RESET} 3\n"
        f"{BRIGHT}{RED} {{4}} > {Fore.RESET}Self harm {BRIGHT}{PURPLE}::{Fore.RESET} 4\n"
        f"{BRIGHT}{RED} {{5}} > {Fore.RESET}NSFW Content {BRIGHT}{PURPLE}::{Fore.RESET} 5\n"
    )

    try:
        token = input(f"{BRIGHT}{PURPLE} > Enter your Token{Fore.RESET}: ")
        headers = {'Authorization': token, 'Content-Type': 'application/json'}
        response = requests.get('https://discord.com/api/v6/users/@me', headers=headers)
        if response.status_code != 200:
            print(f"{BRIGHT}{RED} > Invalid Token")
            input(f"{BRIGHT}{RED}Press Enter to restart...")
            main()
            return

        guild_id = input(f"{BRIGHT}{PURPLE} > Server ID{Fore.RESET}: ")
        channel_id = input(f"{BRIGHT}{PURPLE} > Channel ID{Fore.RESET}: ")
        message_id = input(f"{BRIGHT}{PURPLE} > Message ID{Fore.RESET}: ")
        reason = input(f"{BRIGHT}{PURPLE} > Option{Fore.RESET}: ")

        sent_reports = 0

        def report_message():
            nonlocal sent_reports
            report_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36',
                'Authorization': token,
                'Content-Type': 'application/json'
            }
            payload = {
                'channel_id': channel_id,
                'guild_id': guild_id,
                'message_id': message_id,
                'reason': reason
            }
            while True:
                res = requests.post('https://discord.com/api/v9/report', headers=report_headers, json=payload)
                if res.status_code == 201:
                    sent_reports += 1
                    print(f"{PURPLE} > Sent Report {BRIGHT}{GREEN}::{GREEN} ID {message_id}")
                    ctypes.windll.kernel32.SetConsoleTitleW(f"Report | Sent: {sent_reports}")
                elif res.status_code == 401:
                    print(f"{RED} > Invalid token")
                    input(f"{BRIGHT}{RED}Press Enter to restart...")
                    main()
                    return
                else:
                    print(f"{RED} > Error")
                    input(f"{BRIGHT}{RED}Press Enter to restart...")
                    main()
                    return

        print()
        for _ in range(500, 1000):
            Thread(target=report_message, daemon=True).start()
        input(f"{BRIGHT}{PURPLE}Press Enter to exit...")

    except Exception as e:
        print(f"{RED} > Error: {e}")
        input(f"{BRIGHT}{RED}Press Enter to restart...")
        main()

if __name__ == "__main__":
    main()