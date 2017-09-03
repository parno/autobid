# Autobid
Scripts to automatically generate submission bids for PC members.

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

2. Analyze the PC publications:

    `./analysis.py --cache pc.dat`

    Extracts and normalizes text from the PC's publications.  By default,
    this script will spawn threads equal to the number of your CPUs.  Use
    `-j` to choose another value.

3. Analyze the submissions:

    `./analysis.py --submissions submission_dir`

    Saves the results in `submission_dir/submissions.dat`

4. Build a topic model that maps word occurences to different topics.  

    `./analysis.py --corpus corpus_dir`

   The `corpus_dir` can be any directory of representative publications.
   You can use PDFs from a previous year, or pool all of the PC PDFs and/or
   submissions into the directory.  The model is saved in
   `corpus_dir/lda_model.*`.  You can change the parameters used to learn
   the model (e.g., how many topics to extract, how many passes to make,
   etc.) by editing the call to `gensim.models.ldamodel.LdaModel`.

5. [Optional] Associate PC reviewers with SQL IDs.

   `./util.py --cache pc.dat --pcids pc-info.csv`

   where the CSV file contains a comma-separated first name, last name, and
   SQL ID.  For HotCRP, try:
   `select firstName, lastName, contactId from ContactInfo`
   This will allow the scripts to create MySQL scripts that can feed bid
   info directly into the database

6. Generate bids for submissions:

    `./bid.py --cache pc.dat --submissions submission_dir --corpus corpus_dir`

    For each PC member, this will generate a bid for each submission in
    `submission_dir`.  The bids will be output in a `bid.csv` file in each
    member's directory, as well as a `bid.mysql` file if you completed step
    5 above. To make use of the SQL commands, try something like:

    ```
    for b in `ls */bid.mysql`; do cat $b >> bids.mysql; done
    mysql db_name -u user_name -p < bids.mysql 
    ```

At any time, you can use the [util.py](util.py) script to check on the status of the
PC and to reset the status of an individual PC member or the entire PC, in
case you want to rerun only a portion of the pipeline above.
