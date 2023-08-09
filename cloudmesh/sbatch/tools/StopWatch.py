import threading
import time
from tabulate import tabulate
import logging

class StopWatch:
    def __init__(self):
        self.lock = threading.Lock()
        self.timers = {}

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("StopWatch initialized")

    def start(self, name):
        with self.lock:
            if name not in self.timers:
                self.timers[name] = time.time()
                logging.info("Timer '%s' started", name)

    def end(self, name):
        with self.lock:
            if name in self.timers:
                elapsed_time = time.time() - self.timers[name]
                logging.info("Timer '%s' ended. Elapsed time: %.4f seconds", name, elapsed_time)
                return elapsed_time
            else:
                logging.warning("Timer '%s' was not started", name)
                return None

    def benchmark(self):
        with self.lock:
            if self.timers:
                table_data = []
                for name, start_time in self.timers.items():
                    elapsed_time = time.time() - start_time
                    table_data.append([name, elapsed_time])
                headers = ["Timer Name", "Elapsed Time"]
                logging.info("\nBenchmark Results:\n%s", tabulate(table_data, headers=headers, tablefmt="grid"))
            else:
                logging.info("No timers started.")

if __name__ == "__main__":
    def example_function(stopwatch):
        name = threading.currentThread().getName()
        stopwatch.start(name)
        time.sleep(1)  # Simulate some work
        elapsed_time = stopwatch.end(name)
        if elapsed_time is not None:
            logging.info("Thread '%s': Elapsed time: %.4f seconds", name, elapsed_time)
        else:
            logging.info("Thread '%s': Timer not started", name)

    stopwatch = StopWatch()

    threads = []
    for i in range(5):
        thread = threading.Thread(target=example_function, args=(stopwatch,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    logging.info("\nBenchmark Results:")
    stopwatch.benchmark()
