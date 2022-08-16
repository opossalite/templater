# Templater
A python project that allows the user to create one or more templates and produce an output folder according to a config file.

I created this project to make it easier for me to generate my dotfiles for Linux. I have multiple systems, which means each config file will be slightly different on all my machines, but there are many similarities that I want to be parallel between my systems (such as keybinds). Thus, this project was born.

## How To Use
Next to templater.py, you need a templates directory and a config.txt. The templates directory can be laid out in any way that you wish, and by default the entire tree in this directory will be copied to a new directory called output. You will specify variable values in config.txt, and Templater will automatically fill these into the provided template. You can also specify conditionals and exclude files in the config.

### Template
The template directory is very simple. You can specify where to place a variable by using this notation:
    $t{VARIABLE_NAME}
If the variable is defined in the config, then that placeholder will be replaced with the variable's value when the output directory is generated.

### Config
The config file is a little more intricate. First you can define comments by starting a line with '#'. Comments must be defined at the start of the line. You can define a variable in this fashion:
    VARIABLE_NAME {value}
Anything between the two curly braces will become part of the variable's value, including newlines and other whitespace. Thus, a variable definition can cover multiple lines in your config.

Conditionals and if statements also exist. Here's an example
    if (COLOR {blue} or (COLOR {green}))
    [CODE-BLOCK]
    else
    [CODE-BLOCK]
    end
Parentheses take first priority, then 'not', 'and', and finally 'or'. In this case, if the variable COLOR is equal to the value 'blue', or if COLOR is equal to 'green', then we'll run the first block. Otherwise, we will run the second code block. An else statement is not necessary, but an end statement is.

Finally, we have the exclude keyword. This can be used to exclude a file or directory from being copied into the output folder, which is useful in cases where you want to copy a different file depending on a variable value.
    exclude "example.txt"
    exclude "examplefolder/example_config.ini"


