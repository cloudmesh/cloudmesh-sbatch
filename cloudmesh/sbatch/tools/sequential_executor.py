"""
Sequential Executor

Usage:
  sequential_executor.py [--yaml=<yaml_file>] [--json=<json_file>]
  sequential_executor.py -h | --help

Options:
  -h --help           Show this help message and exit.
  --yaml=<yaml_file>  Path to the YAML file [default: steps.yaml].
  --json=<json_file>  Path to the JSON file.
"""

import subprocess
import yaml
import json
import logging
from docopt import docopt

class SequentialExecutor:
    def __init__(self, dryrun=False):
        self.info = {}
        self.steps = []
        self.dryrun = dryrun

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("SequentialExecutor initialized")

    def load_yaml(self, yaml_path):
        logging.info("Loading YAML file: %s", yaml_path)
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            self.info = data.get('info', {})
            self.steps = data.get('steps', [])
        logging.info("YAML file loaded successfully")

    def run(self, step, **kwargs):
        logging.info("Executing step: %s on host: %s", step['name'], step['host'])

        if self.dryrun:
            logging.info("Dryrun: Command not executed")
            return

        command = step['command']

        # Replace placeholders in the command with provided parameters
        for key, value in kwargs.items():
            command = command.replace(f'{{{key}}}', value)

        try:
            subprocess.run(command, shell=True, check=True)
            logging.info("Step '%s' completed successfully", step['name'])
        except subprocess.CalledProcessError:
            logging.error("Step '%s' failed", step['name'])

    def prepare(self, step):
        logging.info("Preparing in step: %s", step['name'])
        # Add your preparation logic here

    def fetch(self, step):
        logging.info("Fetching data in step: %s", step['name'])
        # Add your fetching logic here

    def load_json(self, json_path):
        logging.info("Loading JSON file: %s", json_path)
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)
        logging.info("JSON file loaded successfully")
        return json_data

    def execute_with_json(self, json_path):
        json_data = self.load_json(json_path)
        # Process the json_data as needed
        # For example, you can iterate through the data and perform actions

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

        for step in self.steps:
            step_type = step.get('type', '')

            if step_type == 'run':
                parameters = step.get('parameters', '')  # Change to the parameter key you're using
                self.run(step, parameters=parameters)
            elif step_type == 'fetch':
                self.fetch(step)
            elif step_type == 'prepare':
                self.prepare(step)
            else:
                logging.warning("Unknown step type in step: %s", step['name'])

if __name__ == "__main__":
    args = docopt(__doc__)

    yaml_file = args['--yaml']
    json_file = args['--json']
    dryrun = args['--dryrun']

    executor = SequentialExecutor(dryrun)

    if yaml_file:
        executor.execute_with_yaml(yaml_file)

    if json_file:
        executor.execute_with_json(json_file)

    executor.execute()
