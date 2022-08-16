import os
import shutil
import sys
from typing import List


#initialize all the variables we'll need here
curdir: str = os.curdir + "/"
template: str = curdir + "template/"
output: str = curdir + "output/"
config: str = curdir + "config.txt"
reserved: List[str] = ["or", "and", "(", ")", "not", ":"]
exclude: List[str] = []

# deducts whether the given if statement is true or not (recursive on parentheses)
def deduce_if(line: List[str], vars: dict, i: int) -> bool:
    if len(line) < 3:
        raise Exception(f"Not enough arguments found on line {i}")
    
    
    
    #temp
    return True

# splits a file into tokens based on whitespace and newlines (also strips whitespace)
def tokenize(lines: str) -> List[List[str]]:
    buf: str = ""
    line: List[str] = []
    ret: List[List[str]] = []
    whites: str = " \t\n"
    whitespace: bool = True
    nests: List[int] = [0, 0, 0]   #holds the values of the different nests: bracket, quote (many rules are ignored when in a nest)
    start_nest: List[str] = ["{", "\"", "("]
    end_nest: List[str] = ["}", "\"", ")"]

    #begin iterating through all characters
    for c in lines:

        #if ending a nest
        if (index := end_nest.index(c) if c in end_nest else -1) > -1:
            if nests[index] > 0:
                nests[index] -= 1
                if nests[index] == 0:
                    if len(buf) > 0:
                        line.append(buf)
                        buf = ""
                    line.append(c)
                    continue

        #if starting a nest
        if (index := start_nest.index(c) if c in start_nest else -1) > -1:
            nests[index] += 1
            if nests[index] == 1: #newly created nest
                if len(buf) > 0:
                    line.append(buf)
                    buf = ""
                line.append(c)
                continue

        #make certain characters their own token
        if c in ["#", ":", "(", ")"]:
            whitespace = False
            if len(buf) > 0:
                line.append(buf)
            line.append(c)
            buf = ""
            continue

        #if this char is whitespace
        if c in whites:
            if not whitespace: #first whitespace we've seen
                whitespace = True
                if len(buf) > 0:
                    line.append(buf)
                    buf = ""
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



# takes tokens and interprets them line by line (recursive on if statements)
def interpret(tokens: List[List[str]], vars: dict):
    nest: int = 0
    nest_collect: List[List[str]] = []

    #iterate through every token
    for i in range(len(tokens)):
    #for line in tokens:
        line: List[str] = tokens[i]

        #
        # CONDITIONALS
        #

        #skip comments
        if line[0] == "#":
            continue

        #if we're in nesting mode, append each line to nest_collect
        if nest > 0:
            if line[0] == "end":
                nest -= 1
            elif line[0] == "if":
                nest += 1
            
            #notify the program that we have just ended a nesting phase
            if nest == 0:
                nest = -1
            else:
                nest_collect.append(line)
                continue

        #if we're looking for an else statement
        if nest == -2:
            if line[0] == "end":
                nest = 0
                continue
            elif line[0] == "else":
                nest = -1
                continue
            
        #handle the end of a nest
        if nest == -1:
            nest = 0
            interpret(nest_collect, vars)
            continue

        #handle if statements
        if line[0] == "if":
            if deduce_if(line, vars, i):
                nest = 1    #collect the current if statment
                continue
            else:
                nest = -2   #collect the else statement

        #
        # INSTRUCTIONS
        #
        
        if len(line) < 4:
            print(line)
            raise Exception(f"Not enough arguments found on line {i}")
        
        #exclude
        if line[0] == "exclude" and line[1] == "\"" and line[3] == "\"":
            if len(line) > 4:
                raise Exception(f"Too many arguments found on line {i}")
            exclude.append(line[2])
            continue

        #set variable value
        if line[1] == "{" and line[3] == "}":
            if len(line) > 4:
                raise Exception(f"Too many arguments found on line {i}")
            vars[line[0]] = line[2]
            
        









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
        tokens: List[List[str]] = tokenize(file.read())

    #begin interpreting, and provide an empty variable dictionary
    vars: dict = {}
    interpret(tokens, vars)

    print(tokens)
    print(vars)
    print(exclude)




    
    


if __name__ == "__main__":
    main()


