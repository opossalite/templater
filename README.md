# Templater
A python project that allows the user to create one or more templates and produce an output folder according to a config file.

I created this project to make it easier for me to generate my dotfiles for Linux. I have multiple systems, which means each config file will be slightly different on all my machines, but there are many similarities that I want to be parallel between my systems (such as keybinds). Thus, this project was born.

## License
This software is dual-licensed under GPL Version 2 and/or GPL Version 3. You may use this software according to these licenses as is most appropriate for your project on a case-by-case basis. Both licenses can be found in the root directory of the repository.

## Documentation
Please look at the [wiki](../../wiki) for full documentation. If you think it needs expanding, please leave a GitHub issue for me.

## Installation
### Arch AUR:

    yay -S templater-git

### Debian/Ubuntu Repo:
Coming soon

### Other:
Install these dependencies:

    git most python

You can either download the templater.py file to the directory where you wish to use it, or you can download and run the PKGBUILD file to install it to your Linux system.

To run the program, simply use this command if it's installed to your system:

    templater [OPTIONS]
    
or this command if you copied the templater.py to your directory:

    python templater.py [OPTIONS]
    
This program will likely work on Windows and MacOS with little to no tweaking, however this has not been tested.
