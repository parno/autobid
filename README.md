# Autobid
Scripts to automatically generate submission bids for PC members.

This version uses a fairly naive matching algorithm based on the 
[Toronto Paper Matching System](http://www.cs.toronto.edu/~lcharlin/papers/tpms.pdf).
The `prior_bids` branch uses a more sophsticated matching algorithm
based on [StarSpace](https://arxiv.org/abs/1709.03856), and it
also has machinery to incorporate prior bidding information.

# Dependencies

The scripts are writen for Python 2 and rely on a number of Python
packages, as well as a few external tools.  Here's a summary of how I
installed all of the necessary dependencies on Mac OS X.  YMMV on other
platforms.

```
sudo pip install -U subprocess32
sudo pip install -U nltk
sudo pip install -U --ignore-installed gensim

brew install wget
brew cask install pdftotext
```

You'll also need a customized copy of Facebook's StarSpace tool, which you can aquire via
```
git clone git@github.com:parno/Starspace.git
```
Follow the README.md instructions for compiling it.  The current `makefile` assumes you 
clone StarSpace into a sibling directory to this one.  If that's not the case, adjust
the `STARSPACE` variable in the `makefile` appropriately.


## Optional

I experimented with using the Python library `slate` to parse PDFs, but
found it to be annoying slow.  The code is still available in [analysis.py](analysis.py).
If you want to enable it, you'll need to run:

```
pip install pdfminer
pip install git+https://github.com/timClicks/slate.git
```

# Standard Pipeline 

Each script depends on the shared definitions in [common.py](common.py).  Each one
will describe its command-line options when run with `-h`.  Note that the
scripts use the Python library `pickle` to save information, so if you
alter the classes in [common.py](common.py), you will be unlikely to be able to load
previously saved data.

The current pipeline consists of the following steps:

1. Fetch publications for each PC member:

    `./fetch.py --cache pc.dat --csv pc-info.csv`

    This parses the CSV file `pc-info.csv` to find a name, email, and URL
    for each PC member (see `parse_csv` in [common.py](common.py) for formatting
    details; if your CSV has different header names, just change the
    relevant labels used as indices into the `row` variable).  The script
    fetches each URL and parses it for direct links to PDF files.  It then
    retrieves those files (using `wget`) and stores in them in a directory
    for each PC member.  Information about the PC is saved into the `pc.dat` 
    file. If you later update `pc-info.csv` with new members, you can run
    the command above, and it will only do additional work for the new
    members.  If an existing reviewer's email or URL change, then that PC
    member's status will be reset, and the script will attempt to fetch
    publications again.

    Suggestion: Before ingesting `pc-info.csv` purge any weird Unicode characters
    you encounter.  They create annoying issues with various command-line utilities,
    so life is easier without them.  Making `fetch.py` do this automatically is future work.

2. Analyze the PC publications:

    `./analysis.py --cache pc.dat`

    Extracts and normalizes text from the PC's publications.  By default,
    this script will spawn threads equal to the number of your CPUs.  Use
    `-j` to choose another value.

3. Associate PC reviewers with SQL IDs.

   `./util.py --cache pc.dat --pcids pc-info.csv`

   where the CSV file contains a comma-separated first name, last name, and
   SQL ID.  For HotCRP, try running the MySQL query:
   `select firstName, lastName, contactId from ContactInfo`
   This will allow the scripts to create MySQL scripts that can feed bid
   info directly into the database

3. (Optional) Feed in data on papers that PC members have previously bid on.  
    First, analyze the previous submissions:

    `./analysis.py --submissions submission_dir`

    Then ingest the bid info:
    
    `./bid.py --learn -c pc.dat --realprefs prefs/real_prefs.october.csv --submissions submission_dir --top_k 15`

    This expects to find all of the previous bidding data in `prefs/real_prefs.october.csv`, and the corresponding
    submitted PDFs in the `submission_dir` directory.  It will look at the top 15 papers that each PC member bid on.

4. Train a model using StarSpace

    `make train`

    Note that if you subsequently add more prior bid info (following the step above), you'll need to rerun this.

5. Generate bids for new submissions:
    Edit the `MONTH` variable in the `makefile` and then run:

    `make bids`

    This will take the information in `pc.dat`, feed it to StarSpace and 
    use it to generate bids.  It assumes your new submissions are stored
    in a path defined by the `SUBMISSIONS_DIR` in the `makefile`.  If that
    isn't the case, update the `makefile` appropriately.

    Sanity check the bids the end up in `bids.MONTH.mysql`.


6. Load the bids into the MySQL database:
    
    `make load_sql`

For an on-going model, you'll need to repeat steps 5 and 6 each month.  You can
also optionally repeat steps 3 and 4 to incorporate bids from the previous month.

At any time, you can use the [util.py](util.py) script to check on the status of the
PC and to reset the status of an individual PC member or the entire PC, in
case you want to rerun only a portion of the pipeline above.
