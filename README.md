## Dictionary scraper

#### Setup
You must have **python 3.6** or higher installed to run this tool. To check whether you have it, open up **Terminal**. Type `python` and hit enter. In the prompt that comes up, you will hopefully see `Python 3.6.x`. If instead you see `Python 2.7.x`, check to see whether `py`, `python3`, or `py3` have the version you want. If none of those work, you will need to install Python 3 yourself from the website of the publisher.

First, download this code from Github.  

Once downloaded, you should make sure that within the `dict_scrape` folder there are two folders labeled `no_vcs` and `results`. If they don't exist, make them using either Finder or the command line in Terminal.

Once all of that is set up, create a file in the `no_vcs` folder called `login_info.txt`. On the first line of this file, put your MW username, and your password on the second.

Additionally, take the zipfile of `words.db`, unzip it, and move the `words.db` file into the `dict_scrape` folder. You can also create this file yourself with `python get_full_words.py`.

#### Commands
All of these commands must be run with `Python 3`. I will write them as starting with `python`, but that should be changed to whatever command links to `Python 3` on your system.

`python dict_queries.py -h` will list all possible command arguments that can be added on the end of the command to actually do something.

`python dict_queries.py --new` will put a list of all words with the new icon in the `results` folder.

`python dict_queries.py --revised` will put a list of all words with the revised icon in the `results` folder.

`python dict_queries.py --word [WORD]` will display all dict entries that match `WORD` exactly. They will come out in the Terminal window.
* If you want to send these results to a text file, you can redirect output: `python dict_queries.py --word bite > results/bite_entries.txt` for example
    
`python dict_queries.py --word [WORD] --part [PART OF SPEECH]` will display all dict entries that match `WORD` exactly and `PART` closely. They will come out in the Terminal window, but can be redirected as shown above.
* `pythong dict_queries.py --word bite --part verb` for example

#### Other functionality
There's a lot of other stuff that could be done with this! But I need some input about what would actually be useful for you.

There are also a couple bugs that I'm still working out, so there are a few words missing from the current database (on the order of 100). I'll let you know when that gets figured out.
