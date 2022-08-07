import os
import shutil
import sys
from typing import List


#initialize all the variables we'll need here
curdir: str = os.curdir + "/"
template: str = curdir + "template/"
output: str = curdir + "output/"
config: str = curdir + "config.txt"
dict: dict = {}



# splits a file into tokens based on whitespace and newlines
def tokenize(lines: str) -> str:
    buf: str = ""
    ret: List[List[str]] = []
    line: List[str] = []
    whites: str = " \t\n"
    whitespace: bool = True

    #begin iterating through all characters
    for c in lines:

        #if this char is whitespace
        if c in whites:
            if not whitespace:
                line.append(buf)
                buf = ""
                whitespace = True
            if c == "\n" and len(line) > 0:
                ret.append(line)
                line = []
        else:
            whitespace = False
            buf += c #append character to buffer

    #add the buffer to the return list if no whitespace at end of file
    if len(buf) > 0:
        line.append(buf)
        ret.append(line)

    return ret



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
        tokens: str = tokenize(file.read())
    print(tokens)

    
    


if __name__ == "__main__":
    main()


