import os
import shutil
import sys


#initialize all the variables we'll need here
curdir: str = os.curdir + "/"
template: str = curdir + "template/"
output: str = curdir + "output/"
config: str = curdir + "config.txt"
dict: dict = {}



# splits a file into tokens based on whitespace
def tokenize(lines: str) -> str:
    return lines



# main function, ensure environment is set up correctly
def main():

    #check to make sure all important items exist
    if not os.path.isfile(config):
        print("The config file does not exist!")
        return
    if not os.path.isdir(template):
        print("The template folder does not exist!")
        return

    #delete the output folder if it exists, then create a blank new one
    if os.path.isdir(output):
        shutil.rmtree(output)
    os.mkdir(output)

    with open(config) as file:
        lines: str = tokenize(file.read())
    print(lines)

    
    


if __name__ == "__main__":
    main()


