import csv
import configparser

# Returns a dictionary of the config file
def getConfig(configFilePath):
    configRaw = configparser.ConfigParser()
    configRaw.optionxform = lambda option: option # This must be included otherwise the config file will be read in all lowercase
    configRaw.read(configFilePath)

    # Go through all the config files, convert to dictionary
    config = {}
    for section in configRaw.sections():
        for key in configRaw[section]:
            config[key] = configRaw[section][key] # Do not use parseConfigSetting() here or else it will convert all values to lowercase
            
    return config



# Interprets a string as a boolean. Returns True or False
def parseBool(string, silent=False):
    if type(string) == str:
        if string.lower() == 'true':
            return True
        elif string.lower() == 'false':
            return False
        else:
            if not silent:
                raise ValueError(f'Invalid value "{string}". Must be "True" or "False"')
            elif silent:
                return string
    elif type(string) == bool:
        if string == True:
            return True
        elif string == False:
            return False
    else:
        raise ValueError('Not a valid boolean string')


def parseConfigSetting(setting):
    # Remove any quotes user may have added in config file
    setting = setting.strip("\"").strip("\'")

    # Check if it is a boolean
    if type(parseBool(setting, silent=True)) == bool:
        return parseBool(setting, silent=True)

    # Check if it is an integer
    try:
        return int(setting)
    except ValueError:
        pass

    # Otherwise return the string in lower case
    return setting.lower()


# Returns a list of dictionaries from a csv file. Where the key is the column name and the value is the value in that column
# The column names are set by the first row of the csv file
def csv_to_dict(csvFilePath):
    with open(csvFilePath, "r", encoding='utf-8-sig') as data:
        entriesDictsList = []
        for line in csv.DictReader(data):
            entriesDictsList.append(line)
    return entriesDictsList


# Returns a list of strings from a txt file. Ignores empty lines and lines that start with '#'
def txt_to_list(txtFilePath):
    with open(txtFilePath, "r", encoding='utf-8-sig') as data:
        entriesList = []
        for line in data:
            if line.strip() != '' and line.strip()[0] != '#':
                entriesList.append(line.strip())
    return entriesList
