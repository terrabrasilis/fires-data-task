#!/usr/bin/python3
from configparser import ConfigParser
import os

class ConfigReadError(BaseException):
    """Exception raised for errors in the configurations reading.
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class ConfigLoader():

    #constructor
    def __init__(self, config_path, filename, section):
        # get env var setted in Dockerfile
        self.is_docker_env = os.getenv("DOCKER_ENV", False)
        self.config_path = config_path
        self.default_path = "/usr/local/data/config/"
        self.filename = filename
        self.section = section

    def get(self):

        config_file = ""
        
        # If the environment is docker then use the absolute path to read config files
        if self.is_docker_env:
            config_file = self.default_path + self.filename
        else:
            config_file = self.config_path + "/" + self.filename

         # Test if .cfg file exists
        if not os.path.exists(config_file):
            # get config params from env vars
            raise ConfigReadError("Configuration file","Configuration file, {0}, was not found.".format(self.filename))

        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(config_file)
    
        # get section
        cfg = {}
        if parser.has_section(self.section):
            params = parser.items(self.section)
            for param in params:
                if '{' in param[1] and '}' in param[1]:
                    cfg[param[0]] = eval(param[1])
                else:
                    cfg[param[0]] = param[1]
        else:
            raise Exception("Section {0} not found in the {1} file".format(self.section, self.filename))
    
        return cfg