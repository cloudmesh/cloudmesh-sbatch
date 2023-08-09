"""
Parallel Executor with Dependencies

Usage:
  parallel_executor.py <yaml_file>
  parallel_executor.py -h | --help

Options:
  -h --help           Show this help message and exit.
"""

import subprocess
import yaml
import concurrent.futures
import logging
from docopt import docopt

class ParallelExecutor:
    def __init__(self):
        self.info = {}
        self.steps = []
        self.dependencies = {}

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("ParallelExecutor initialized")

    def load_yaml(self, yaml_path):
        logging.info("Loading YAML file: %s", yaml_path)
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            self.info = data.get('info', {})
            self.steps = data.get('steps', [])
            self.dependencies = {step['name']: step.get('dependencies', []) for step in self.steps}
        logging.info("YAML file loaded successfully")

    def load_json(self, json_path):
        logging.info("Loading JSON file: %s", json_path)
        with open(json_path, 'r') as file:
            data = json.load(file)
            self.info = data.get('info', {})
            self.steps = data.get('steps', [])
            self.dependencies = {step['name']: step.get('dependencies', []) for step in self.steps}
        logging.info("JSON file loaded successfully")

    def execute_step(self, step):
        logging.info("Executing step: %s on host: %s", step['name'], step['host'])
        command = step['command']

        try:
            subprocess.run(command, shell=True, check=True)
            logging.info("Step '%s' completed successfully", step['name'])
        except subprocess.CalledProcessError:
            logging.error("Step '%s' failed", step['name'])

    def execute_with_yaml(self, yaml_path):
        self.load_yaml(yaml_path)
        self.execute()

    def execute(self):
        self.load_yaml()

        description = self.info.get('description', 'No description')
        author = self.info.get('author', 'Unknown')
        source = self.info.get('source', 'Unknown')

        logging.info("Description: %s", description)
        logging.info("Author: %s", author)
        logging.info("Source: %s", source)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.steps)) as executor:
            future_to_step = {executor.submit(self.execute_step, step): step for step in self.steps}
            concurrent.futures.wait(future_to_step)
            for future in concurrent.futures.as_completed(future_to_step):
                step = future_to_step[future]
                logging.info("Step '%s' completed", step['name'])


if __name__ == "__main__":
    args = docopt(__doc__)

    file_path = args['<file>']
    use_json = args['--json']

    executor = ParallelExecutor()

    if use_json:
        executor.load_json(file_path)
    else:
        executor.execute_with_yaml(file_path)

    executor.execute()