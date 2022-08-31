import os
import shutil
import sys
import filecmp
from time import sleep
from typing import List


#initialize all the variables we'll need here
curdir: str = os.curdir + "/"
template: str = curdir + "template/"
output: str = curdir + "output/"
config: str = curdir + "config.txt"
check_exclude: List[str] = []



# deduces whether the given if statement is true or not (recursive on parentheses)
def deduce_if(line: List[str], vars: dict) -> bool:
    if len(line) < 3:
        raise Exception(f"Not enough arguments found in this if statement")
    
    #handle all recursion here, should have a single nest by the end of this
    while "(" in line:
        rline = line.copy()
        rline.reverse()
        segment = line[line.index("(") + 1:len(line) - rline.index(")") - 1]
        line[line.index("("):len(line) - rline.index(")")] = [deduce_if(segment, vars)]
        
    #replace all value checks with bools
    i: int = 0
    reserved: List[str] = ["or", "and", "not"]
    while i < len(line):
        
        #if not an operator, then check the variable's value
        if type(line[i]) == str and line[i] not in reserved:
            #print(f"Replace before: {line}")
            line[i:i+4] = [vars.get(line[i]) == line[i+2]]
            #print(f"Replace after: {line}")
        i += 1
            
    #not
    i = 0
    while i < len(line):
        if line[i] == "not":
            #print(f"Not before: {line}")
            line[i:i+2] = [not line[i+1]]
            #print(f"Not after: {line}")
        i += 1
        
    #and
    i = 0
    while i < len(line):
        if line[i] == "and":
            #print(f"And before: {line}")
            line[i-1:i+2] = [line[i-1] and line[i+1]]
            #print(f"And after: {line}")
        else:
            i += 1
        
    #or
    i = 0
    while i < len(line):
        if line[i] == "or":
            #print(f"Or before: {line}")
            line[i-1:i+2] = [line[i-1] or line[i+1]]
            #print(f"Or after: {line}")
        else:
            i += 1
        
    #error checking
    if len(line) > 1 or type(line[0]) != bool:
        #print(line)
        raise Exception(f"Invalid syntax found in this if statement")
    
    return line[0]



# splits a file into tokens based on whitespace and newlines (also strips whitespace)
def tokenize(lines: str) -> List[List[str]]:
    buf: str = ""   #holds the current token
    line: List[str] = []    #holds the current line of tokens
    ret: List[List[str]] = []   #holds all lines
    whites: str = " \t\n"
    whitespace: bool = True
    nests: List[int] = [0, 0]   #holds the values of the different nests: bracket, quote (many rules are ignored when in a nest)
    start_nest: List[str] = ["{", "\""]
    end_nest: List[str] = ["}", "\""]

    #begin iterating through all characters
    for c in lines:

        #if ending a nest
        if (index := end_nest.index(c) if c in end_nest else -1) > -1: #if c is in end_nest, then save its index into index
            if nests[index] > 0: #if in a nest
                nests[index] -= 1
                if nests[index] == 0: #if no longer in a nest (c was the end)
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

        #if in a nest, then ignore most rules and just append to buf
        breakage: bool = False #allows for outer loop continue
        for nest in nests:
            if nest > 0:
                buf += c
                breakage = True
                break
        if breakage:
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
def interpret(tokens: List[List[str]], vars: dict, exclude: List[str]):
    global check_exclude
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
            if line[0] == "end" or line[0] == "else":
                nest -= 1
            elif line[0] == "if":
                nest += 1
            
            #notify the program that we have just ended a nesting phase
            if nest == 0:
                if line[0] == "end":
                    nest = -1
                elif line[0] == "else":
                    nest = -3
            else:
                nest_collect.append(line)
                continue

        #if we're looking for an else statement
        if nest == -2:
            if line[0] == "end":
                nest = 0
            elif line[0] == "else":
                nest = 1
            continue
            
        #handle the end of a nest
        if nest == -1 or nest == -3:
            interpret(nest_collect, vars, exclude)
            nest_collect = []
            if nest == -1:
                nest = 0
                continue
            else:
                nest = -2   #technically this is just a workaround, but it works
                continue

        #handle if statements
        if line[0] == "if":
            if deduce_if(line[1:], vars):
                nest = 1    #collect the current if statment
                #print("SET NEST TO 1")
                continue
            else:
                nest = -2   #collect the else statement
                #print("SET NEST TO -2")
                continue

        #
        # INSTRUCTIONS
        #
        
        if len(line) < 4:
            raise Exception(f"Not enough arguments found on line {i}")
        
        #exclude
        if line[0] == "exclude" and line[1] == "\"" and line[3] == "\"":
            if len(line) > 4:
                raise Exception(f"Too many arguments found on line {i}")
            exclude.append(line[2])
            continue

        #exclude_check
        if line[0] == "exclude_check" and line[1] == "\"" and line[3] == "\"":
            if len(line) > 4:
                raise Exception(f"Too many arguments found on line {i}")
            check_exclude.append(line[2])
            continue

        #set variable value
        if line[1] == "{" and line[3] == "}":
            if len(line) > 4:
                raise Exception(f"Too many arguments found on line {i}")
            vars[line[0]] = line[2]



# apply the config to a specific file
def apply_template_file(vars: dict, path: str):
    with open("./template" + path) as file:
        with open("./output" + path, "w") as outfile:
            filestr: str = file.read()
            
            while "$t{" in filestr:
                #sleep(1)
                #print("the thing was found in the thing")
                #print(f"before: {filestr}")
                index = filestr.find("$t{")
                rindex = filestr.find("}", index)
                filestr = filestr[:index] + vars.get(filestr[index+3:rindex], "") + filestr[rindex + 1:]
                #print(f"after: {filestr}")
            
            outfile.write(filestr)
            
    return



# apply the actual config file to the template and generate the output
def apply_template(vars: dict, exclude: List[str]):
    for (path, dirs, files) in os.walk(template[:-1], topdown = True):
        if path[11:] in exclude: #skip directory
            continue
        
        #create each new directory that we don't skip
        outdir = path[10:]
        os.makedirs("./output" + outdir)
        
        #iterate through all the files in this directory
        for file in files:            
            if file in exclude: #skip file
                continue
            
            #apply config to file
            apply_template_file(vars, outdir + "/" + file)

    return



# check local files and compare them to the generated template
def check(target: str):
    #print(f"TO IMPLEMENT, excluding: {check_exclude} at {target}")
    #for (path1, dirs1, files1, path2, dirs2, files2) in zip(os.walk(target, topdown = True, os.walk(output, topdown = True))):
    
    invalid_dirs: List[str] = [] #a list of all the invalid directories, don't exist in the target
    invalid_files: List[str] = [] #a list of all the invalid directories, don't exist in the target
    valid_files: List[str] = [] #all the files that our git command will be applied to
    
    for (path, dirs, files) in os.walk(output, topdown = True): #iterate through the output and see if each element exists in the target
        if path[-1] != "/":
            path += "/"
        check_path = path[9:]
        
        if path[9:] in invalid_dirs or path[9:] in check_exclude:
            continue
        #print(check_path)
        #print(path)
        #print(dirs)
        #print(files)
        for di in dirs:
            if check_path + di in check_exclude:    #if user has specified to skip this directory
                invalid_dirs.append(check_path + di + "/")
                continue
            print(f"Checking1 {target + check_path + di + '/'}")
            if not os.path.isdir(target + check_path + di + "/"):
                invalid_dirs.append(check_path + di + "/")
        for file in files:
            if check_path + file in check_exclude:  #if user has specified to skip this file
                invalid_files.append(check_path + file)
                continue
            print(f"Checking2 {target + check_path + file}")
            if os.path.isfile(target + check_path + file):
                valid_files.append(check_path + file)
            else:
                invalid_files.append(check_path + file)
                
    print("Check result:")
    print(f"There are {len(invalid_dirs)} folder(s) missing, including files within them.")
    print(f"There are {len(invalid_files)} file(s) missing.")
    res = input("Would you like to see the differences? [Y/n] ")
    if res.lower().strip() != "y":
        return
    
    collected: str = ""
    if len(invalid_dirs) > 0:
        collected += "Folders missing:"
        for d in invalid_dirs:
            collected += "\n" + d
        collected += "\n\n"
    if len(invalid_files) > 0:
        collected += "Files missing:"
        for f in invalid_files:
            collected += "\n" + f
        collected += "\n"
    os.system(f"echo \"{collected}\" | less")
    for file in valid_files:
        #print(target + file)
        #print(filecmp.cmp(os.getcwd() + "/output/" + file, target + file))
        #print(os.path.expanduser("."))
        #print(os.getcwd() + "/output/" + file)
        if not filecmp.cmp(os.getcwd() + "/output/" + file, target + file): #if the two files are not the same
            os.system(f"git diff --no-index {os.getcwd() + '/output/' + file} {target + file}")

    #print("_")
    #print(invalid_dirs)
    #print(invalid_files)
  
    #os.system("ls -a --color=auto")
    #os.system(f"cat {valid_files[0]}")
    
    
    
    
    #git diff --no-index test.txt test1.txt
        



# main function, ensure environment is set up correctly
def main():

    #check to make sure all important items exist
    if not os.path.isfile(config):
        print("The config file does not exist!")
        return
    if not os.path.isdir(template):
        print("The template folder does not exist!")
        return

    #delete the output folder if it exists
    if os.path.isdir(output):
        shutil.rmtree(output)
    #os.mkdir(output)

    with open(config) as file:
        tokens: List[List[str]] = tokenize(file.read())

    #begin interpreting the tokens
    vars: dict = {}
    exclude: List[str] = []
    interpret(tokens, vars, exclude)

    #revise the exclude directories to remove trailing slash if exists
    for i in range(len(exclude)):
        if exclude[i][-1] == "/":
            exclude[i] = exclude[i][:-1]
    
    #finally apply the config to the template
    apply_template(vars, exclude)

    #after we've applied the config, check any valid flags the user submitted
    args = sys.argv[1:]
    while len(args) > 0:
        if args[0] == "--check" or args[0] == "-c":
            if len(args) > 1:
                target = args[1]
                if target[-1] != "/":
                    target += "/"
                if not os.path.isdir(target):
                    print("Target directory does not exist!")
                    break
                if target[0] == ".":
                    target = os.getcwd() + target[1:]
                check(target)
                args = args[2:]
                continue
            else:
                print("Missing a target directory in the arguments!")
                break
        
        print("Unknown arguments!")
        break





if __name__ == "__main__":
    main()
