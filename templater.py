import os
import sys
import shutil
import filecmp
import tempfile
from typing import List


#initialize all the variables we'll need here
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
            line[i:i+4] = [vars.get(line[i]) == line[i+2]]
        i += 1
            
    #not
    i = 0
    while i < len(line):
        if line[i] == "not":
            line[i:i+2] = [not line[i+1]]
        i += 1
        
    #and
    i = 0
    while i < len(line):
        if line[i] == "and":
            line[i-1:i+2] = [line[i-1] and line[i+1]]
        else:
            i += 1
        
    #or
    i = 0
    while i < len(line):
        if line[i] == "or":
            line[i-1:i+2] = [line[i-1] or line[i+1]]
        else:
            i += 1
        
    #error checking
    if len(line) > 1 or type(line[0]) != bool:
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

        ##
        ## CONDITIONALS
        ##

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
                continue
            else:
                nest = -2   #collect the else statement
                continue

        ##
        ## INSTRUCTIONS
        ##
        
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
    global temdir, outdir
    
    #open the same file in the template and the output
    with open(temdir + path) as file:
        with open(outdir + path, "w") as outfile:
            
            #apply the template to the file and write the output
            filestr: str = file.read()
            while "$t{" in filestr:
                index = filestr.find("$t{")
                rindex = filestr.find("}", index)
                filestr = filestr[:index] + vars.get(filestr[index + 3:rindex], "") + filestr[rindex + 1:]
            outfile.write(filestr)
            
    return



# apply the actual config file to the template and generate the output
def apply_template(vars: dict, exclude: List[str]):
    global temdir, outdir
    
    directory_skip: str = None    #the current directory that we have opted to skip
    path_clipped: str = None      #relative directory for a given file/folder
    clip_size: int = len(temdir)  #account for path length and the slash
    
    #iterate through all files in the template
    for (path, dirs, files) in os.walk(temdir, topdown = True):
        
        #print(f"path: {path}")
        path_clipped = path[clip_size:]
        
        #skip directories
        if path_clipped in exclude: #skip if in exclude
            directory_skip = path_clipped
            continue
        elif directory_skip and path_clipped.startswith(directory_skip): #skip if in excluded directory
            continue
        
        #create each new directory that we don't skip
        os.makedirs(outdir + path_clipped)
        
        #iterate through all the files in this directory, TODO ensure that this actually works for files not in the base directory
        for file in files:
            nfile = path_clipped + file if path_clipped == "" else path_clipped + "/" + file
            if nfile in exclude: #skip file
                continue
            
            #apply config to file
            apply_template_file(vars, nfile)

    return



# check local files and compare them to the generated template
def check(target: str):
    global outdir
    
    #setup
    invalid_dirs: List[str] = [] #a list of all the invalid directories, don't exist in the target
    invalid_files: List[str] = [] #a list of all the invalid directories, don't exist in the target
    valid_files: List[str] = [] #all the files that our git command will be applied to
    diff_files: List[str] = [] #all the files that have changed
    
    path_clipped: str = None      #relative directory for a given file/folder
    clip_size: int = len(outdir)  #account for path length and the slash
    
    #revise the check_exclude directories to remove trailing slash if exists, better compatibility with shutil
    for i in range(len(check_exclude)):
        if check_exclude[i][-1] == "/":
            check_exclude[i] = check_exclude[i][:-1]
    
    #iterate through the output and see if each element exists in the target
    for (path, dirs, files) in os.walk(outdir, topdown = True):
        
        path_clipped = path[clip_size:]
        
        if path_clipped in invalid_dirs or path_clipped in check_exclude:
            continue
        
        #load this folder into its correct group
        if path_clipped in check_exclude: #if user has specified to skip this directory, no load
            continue
        if not os.path.isdir(target + path_clipped): #if the directory doesn't exist, invalid_dirs
            invalid_dirs.append(target + path_clipped)
            

        #load files and folders into their respective groups for comparisons
        #for di in dirs:
        #    if path_clipped + "/" + di in check_exclude: #if user has specified to skip this directory, no load
        #        continue
        #    if not os.path.isdir(target + path_clipped): #if the directory doesn't exist, invalid_dirs
        #        invalid_dirs.append(target + "/" + di + "/")
        for file in files:
            nfile = path_clipped + file if path_clipped == "" else path_clipped + "/" + file
            if nfile in check_exclude:  #if user has specified to skip this file, no load
                continue
            if os.path.isfile(target + nfile):  #if the file exists, valid_files 
                valid_files.append(nfile)
            else:                                                   #if the file doesn't exist, invalid_files
                invalid_files.append(nfile)
       
    for file in valid_files:
        if not filecmp.cmp(outdir + file, target + file): #if the two files are not the same
            diff_files.append(file) 
                
    print("Check result:")
    print(f"There are {len(diff_files)} file(s) with changes.")
    print(f"There are {len(invalid_files)} file(s) missing.")
    print(f"There are {len(invalid_dirs)} directories(s) missing.")
    
    if len(diff_files) + len(invalid_files) + len(invalid_dirs) == 0:
        return
    
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
    if len(collected) > 0:
        os.system(f"echo \"{collected}\" | most")
       
    for file in diff_files:
        os.system(f"git diff --no-index \"{outdir + file}\" \"{target + file}\"")



# main function, ensure environment is set up correctly
def main():
    global temdir, outdir, config
    
    ##
    ## ARGUMENT HANDLING
    ##
    
    help_: bool = False
    mode: int = 0           #used to signify that we are searching for something specific
    fail: bool = False      #user failed at providing good parameters
    temdir_base: str = None #base directory of template folder
    outdir_base: str = None #base directory of output folder
    checkdir: str = None    #directory we'll check against, if not None
    
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        
        #help
        if arg == "-h" or arg == "--help":  
            if mode != 0: #if we were looking for something
                print("Error: was expecting a different argument")
                fail = True
                break
            help_ = True
            continue
        
        #directory
        if arg == "-d" or arg == "--directory":
            if mode != 0:
                print("Error: was expecting a different argument")
                fail = True
                break
            if temdir_base != None:
                print("Error: already specified this argument")
                fail = True
                break
            mode = 1
            continue
        
        #check
        if arg == "-c" or arg == "--check" or arg == "--compare":
            if mode != 0:
                print("Error: was expecting a different argument")
                fail = True
                break
            if checkdir != None:
                print("Error: already specified this argument")
                fail = True
                break
            mode = 2
            continue
        
        #temp
        if arg == "-t" or arg == "--temp":
            if mode != 0:
                print("Error: was expecting a different argument")
                fail = True
                break
            if outdir_base != None:
                print("Error: already specified this argument")
                fail = True
                break
            outdir_base = tempfile.mkdtemp()
            continue
        
        #fallback
        if mode == 1:
            if temdir_base != None:
                print("Error: already specified this argument")
                fail = True
                break
            temdir_base = arg
            mode = 0
            continue
        elif mode == 2:
            if checkdir != None:
                print("Error: already specified this argument")
                fail = True
                break
            checkdir = arg
            mode = 0
            continue
        
        print(f"Error: unknown argument {arg}")
        fail = True
        break
    #endfor
            
    if fail:
        print("Invalid arguments, please use '-h' or '--help' for more information")
        return
    
    if help_:
        print(
'''Used to automatically fill in values to a template

USAGE:
\ttemplater [OPTIONS]

OPTIONS:
\t-c [TARGET]\tCompare the output against the target, will show differences
\t-d [TARGET]\tRuns Templater at the specified target instead of in the current working directory
\t-h, --help\tPrint help information (this message) and exit
\t-t, --temp\tWill output to a temporary folder instead of in the current working directory

Full documentation:
<https://github.com/TheTerrior/templater>'''
        )
        return
    
    ##
    ## DIRECTORY PROCESSING
    ##
    
    #set some defaults
    if temdir_base == None:
        temdir_base = os.getcwd() + "/"
    if outdir_base == None:
        outdir_base = temdir_base
        
    #ensure trailing slash
    if temdir_base[-1] != "/":
        temdir_base += "/"
    if outdir_base[-1] != "/":
        outdir_base += "/"
    if checkdir != None and checkdir[-1] != "/":
        checkdir += "/"
        
    #replace dot with current working directory
    if temdir_base[0] == ".":
        temdir_base = os.getcwd() + temdir_base[1:]
    if outdir_base[0] == ".":
        outdir_base = os.getcwd() + outdir_base[1:]
    if checkdir != None and checkdir[0] == ".":
        checkdir = os.getcwd() + checkdir[1:]
    
    #replace tilde with home directory
    if temdir_base[0] == "~":
        temdir_base = os.path.expanduser(temdir_base)
    if outdir_base[0] == "~":
        outdir_base = os.path.expanduser(outdir_base)
    if checkdir != None and checkdir[0] == "~":
        checkdir = os.path.expanduser(checkdir)
        
    #ensure we have complete paths (fill in directory before the relative path)
    if temdir_base[0] != "/":
        temdir_base = os.getcwd() + "/" + temdir_base
    if outdir_base[0] != "/":
        outdir_base = os.getcwd() + "/" + outdir_base
    if checkdir != None and checkdir[0] != "/":
        checkdir = os.getcwd() + "/" + checkdir

    temdir = temdir_base + "template/"  #directory of the template
    config = temdir_base + "config.txt" #directory of the config file
    outdir = outdir_base + "output/"    #directory of the output
    
    ##
    ## Environment Preprocessing
    ##

    #check to make sure all important items exist
    if not os.path.isfile(config):
        print("The config file does not exist!")
        return
    if not os.path.isdir(temdir):
        print("The template folder does not exist!")
        return

    #delete the output folder if it exists
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    
    print("Applying template...")

    ##
    ## CONFIG INTERPRETATION
    ##

    with open(config) as file:
        tokens: List[List[str]] = tokenize(file.read())

    #begin interpreting the tokens
    vars: dict = {}
    exclude: List[str] = []
    interpret(tokens, vars, exclude)

    #revise the exclude directories to remove trailing slash if exists, better compatibility with shutil
    for i in range(len(exclude)):
        if exclude[i][-1] == "/":
            exclude[i] = exclude[i][:-1]
    
    ##
    ## APPLY CONFIG
    ##
    
    #finally apply the config to the template
    apply_template(vars, exclude)
    
    print(f"Completed.") #TODO, maybe output the number of directories and files copied
    
    ##
    ## POSTPROCESS CHECKS
    ##
    
    #perform a check if the user has requested it
    if checkdir != None:
        if not os.path.isdir(checkdir):
            print("Target directory does not exist!")
            return
        check(checkdir)

        

if __name__ == "__main__":
    main()
