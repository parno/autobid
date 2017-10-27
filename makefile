# Experimental commands for training and testing StarSpace-based bidding

#LABEL=old_only
#BIDARGS=--train_count 10 --old_work_only

#LABEL=work_and_bids_30
#BIDARGS=--train_count 30 --work_and_bids


#LABEL=dupe10
#BIDARGS=--train_count 10 --dupe_bids

#LABEL=bidratio0.5
#BIDARGS=--train_count 10 --bidratio 0.5

#LABEL=bidratio0.25
#BIDARGS=--train_count 10 --bidratio 0.25

#LABEL=bidratio0.75
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75ngrams3
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75ngrams7
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75dim50
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75dim100
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75dim100epoch10
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75dim50epoch10
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.75dim75
#BIDARGS=--train_count 10 --bidratio 0.75 

#LABEL=bidratio0.62dim50
#BIDARGS=--train_count 10 --bidratio 0.62

LABEL=bidratio0.25dim50
BIDARGS=--train_count 10 --bidratio 0.25

all: experiment
#all: starspace 

starspace:
	echo Training...
	../Starspace/starspace train -trainFile pc.training -model pcmatching -fileFormat labelDoc -trainMode 1 -thread 5 -dim 50 
	echo Predicting...
	../Starspace/starspace test -testFile pc.test -model pcmatching -fileFormat labelDoc -basedoc submissions/sp2018-september/submissions.starspace.txt -predictionFile submissions/sp2018-september/prediction.txt -K 50
	echo Splitting predictions...
	./bid.py --predictions submissions/sp2018-september/prediction.txt --submissions submissions/sp2018-september -c pc.dat --bidlabel $(LABEL)
	echo Analyzing bids...
	./analyze-bids.py --calc predicted_bids.starspace.$(LABEL).txt --changed september --month september --top_k 10 | tee experiments/mode1.$(LABEL).txt

experiment:
	echo Writing out training data...
	./bid.py -c pc.dat --train pc.training $(BIDARGS)
	echo Writing out PC members...
	./bid.py -c pc.dat --pcfile pc.test  $(BIDARGS)
	echo Training...
	../Starspace/starspace train -trainFile pc.training -model pcmatching -fileFormat labelDoc -trainMode 1 -thread 5 
	echo Predicting...
	../Starspace/starspace test -testFile pc.test -model pcmatching -fileFormat labelDoc -basedoc submissions/sp2018-september/submissions.starspace.txt -predictionFile submissions/sp2018-september/prediction.txt -K 50
	echo Splitting predictions...
	./bid.py --predictions submissions/sp2018-september/prediction.txt --submissions submissions/sp2018-september -c pc.dat --bidlabel $(LABEL)
	echo Analyzing bids...
	./analyze-bids.py --calc predicted_bids.starspace.$(LABEL).txt --changed september --month september --top_k 10 | tee experiments/mode1.$(LABEL).txt
