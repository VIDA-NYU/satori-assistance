import sys
import time
import signal
import asyncio
import requests
import multiprocessing
from datetime import datetime


class ProcessManager:
    """
    Manages a background process that sends repeated POST requests.

    Attributes:
        headers (dict): Authorization or content headers to include in requests.
        processes (list): List of active multiprocessing.Process instances.
    """

    def __init__(self, headers):
        self.headers = headers
        self.processes = []

    def send_post_requests(self, url: str, interval: int = 5):
        """
        Sends a POST request to the given URL at regular intervals.

        Args:
            url (str): The endpoint to which requests are sent.
            interval (int): Number of seconds to wait between requests.
        """
        while True:
            try:
                content = "Trigger"
                response = requests.post(url, files={'entries': content}, headers=self.headers)
                # print(f"[Request] Response: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[Request Error] {e}")
            time.sleep(interval)
            # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {url} Stop sleeping, preparing to send next request")
            # print("Stop sleeping")

    def start_process(self, url: str, interval: int):
        """
        Launches a new process to begin sending repeated POST requests.

        Args:
            url (str): Endpoint to post to.
            interval (int): Frequency in seconds.
        """
        process = multiprocessing.Process(target=self.send_post_requests, args=(url, interval))
        self.processes.append(process)
        process.start()

    def signal_handler(self, sig, frame):
        """
        Gracefully terminates all background processes on interrupt.
        """
        print("[Signal] Ctrl+C detected! Terminating background processes...")
        for process in self.processes:
            process.terminate()
        sys.exit(0)
