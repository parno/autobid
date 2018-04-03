
MONTH=september
SUBMISSIONS_DIR=submissions/sp2018-$(MONTH)
NUM_SUBMISSIONS=`ls $(SUBMISSIONS_DIR) | wc -l`
STARSPACE=../Starspace/starspace
TOP_K=25		# Script ensures that TOP_K ranked papers for a PC member have a positive bid; everything else has a negative bid

# StarSpace parameters that seem to work reasonably well.  YMMV
DIM=50
BIDRATIO=0.75
TRAIN_COUNT=10


all: bids 

train:
	./bid.py -c pc.dat --train pc.training --train_count $(TRAIN_COUNT) --bidratio $(BID_RATIO)
	$(STARSPACE) train -trainFile pc.training -model pcmatching -fileFormat labelDoc -trainMode 1 -thread 5 -dim $(DIM)

bids:
	echo Writing out PC members...
	./bid.py -c pc.dat --pcfile pc.test --train_count $(TRAIN_COUNT) --bidratio $(BID_RATIO)
	echo Analyzing submissions
	./analysis.py --submissions $(SUBMISSIONS_DIR)
	echo Preparing submissions for StarSpace
	./bid.py -c pc.dat --subfile $(SUBMISSIONS_DIR)/submissions.starspace.txt --submissions $(SUBMISSIONS_DIR)
	echo Generating predictions
	$(STARSPACE) test -testFile pc.test -model pcmatching -fileFormat labelDoc -basedoc $(SUBMISSIONS_DIR)/submissions.starspace.txt -predictionFile $(SUBMISSIONS_DIR)/prediction.txt -K $(NUM_SUBMISSIONS)
	echo Splitting the predictions into bids 
	./bid.py --predictions $(SUBMISSIONS_DIR)/prediction.txt --submissions $(SUBMISSIONS_DIR) -c pc.dat --bidlabel bidratio$(BID_RATIO)dim$(DIM) --top_k $(TOP_K)
	echo Merging SQL commands for the bids
	for b in `ls pc_data/*/bid.mysql`; do cat $b >> bids.$(MONTH).mysql; done

load_sql:
	mysql sp2018 < bids.$(MONTH).mysql 

