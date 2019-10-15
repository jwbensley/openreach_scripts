# lad_compare.py


### Problem Background
Every quarter Openreach release a new version of a CSV file called the "LAD" file. This file maps each UK postcode to the exchange that *would* be used if an EAD fibre circuit were to be ordered to a given UK postcode (the fibre servicing exchange).

This script will compare the two LAD file versions and produce two new files which have a list of postcode entries that are unique to each input file.


### Problem Scoping 1
The first problem is that file 1 has 1,867,414 rows and file 2 has 1,867,749 rows. File 2 is 335 rows larger but they may not be all additional rows, for example some rows may no longer be present in file 1 which were in file 1. This means that in the worst case scenario every row in file 1 needs to be checked to every row in file 2, in a simple `for` loop to check if each postcode exists in both files. A naïve suggestion then would be that the Number of Checks required is `1,867,414 * 1,867,749 == 3,487,860,631,086` checks.


### Problem Scoping 2
A basic conjecture we can make is that 50% of time when searching for a postcode in file 1, it will be found in the first 50% of file 2 (this is independent of file order). This means the NoC is already cut in half and reduced to `1,867,414 * (1,867,749/2) == 1,743,930,315,543` checks.


### Problem Scoping 3
A simple change can be made to the basic for loop idea which reduces the NoC significantly. As each row in file 1 is looped over, and compared against every row in file 2, once a match is found in file 2, the matching row in file 2 can be deleted so that each subsequent row in file 1 has a reducing file 2 to search through. Now, “only” the nth triangle of 1,867,414 rows needs to be checked, and as above statistically 50% of file 1 rows will be in the first 50% of file 2, the entire of file 2 doesn't need to be walked for each file 1 row. NoC is now `1,867,749 * (1,867,414/2) == 1,743,930,315,543 / 2 == 871,965,157,771.5` checks.


### Problem Scoping 4
There is an exception to the previously mentioned 50% assertion. If the two files were explicitly sorted in reverse order to each other, i.e. file 1 is sorted by postcode in alphabetical order from A to Z and file 2 is sorted from Z to A, then for each row in file 1 we'll need to always search to the end (or near the end) of file 2 to find the matching row (if one exists). This means that the first action which must be made is that both files must be sorted. Sorting takes <1 second and as a result for each row in file 1 the matching row is going to be the first row in 2 (or very near the start) because each matched row is deleted from file 2. The NoC now comes essentially becomes "number of rows in the larger of the two files", `NoC == 1,867,749`. In a theoretical worst case scenario that all the postcodes in file 1 weren't present in file 2, no entries from file 2 would be delete because none would match any entry in file 1, and we'd be back to square 1 with NoC returning to `1,867,414 * 1,867,749 == 3,487,860,631,086` checks (in reality there would be no point compring the two CSV files if we knew they were completely different, but we know this is an updated version of the same file so the NoC will be much closer to `1,867,749`).


### Multi-Threading
To cater for the worst case scenarios the simple solution is "guns, lots of guns"

![lots of guns](guns.gif)

It's less costly to sanitise data up-front rather than during the comparison loop so that any data cleansing actions aren't repeated on any entries parsed more than once. The script sorts both lists alphabetically and normalises the data (it converts all postcodes to the same case and strips white spaces, we can't rely on Openreach to provide consistently formatted data!).

The script then divides both files into the same number of chunks as there are CPU threads on the system, and spins up multiple threads and gives each thread a chunk from each file to compare.


### Results
Below are the results from running the script. After modifying the script to return the number of checks each thread made instead of the unique postcodes, across all thread in total 28,691,090 checks were made and the unmodified version of the script shown below shows that these 28,691,090 checks were made in ~57 seconds which is circa 503,352 checks per second.
```
$python3 ./lad_compare.py -f1 ../LODE_LAD-2019-Q2.csv -f2 ../LODE_LAD-2019-Q3.csv
Loading csv...
Loaded 1867414 CSV rows from ../LODE_LAD-2019-Q2.csv
Loaded in 9.596431866 seconds
Loading csv...
Loaded 1867749 CSV rows from ../LODE_LAD-2019-Q3.csv
Loaded in 9.717176722000001 seconds
Formatting postcodes...
Formatted in 1.6291147059999993 seconds
Sorting postcodes...
Sorted in 0.6528609359999997 seconds
Number of CPUs:  12
Chunk size per CPU: 155618
Chunking and merging LAD and Fibre data...
Chunked data in 0.5032568519999998 seconds
Chunk 0: file 1 entries 155618, file 2 entries 155640
Chunk 1: file 1 entries 155618, file 2 entries 155657
Chunk 2: file 1 entries 155618, file 2 entries 155644
Chunk 3: file 1 entries 155618, file 2 entries 155648
Chunk 4: file 1 entries 155618, file 2 entries 155639
Chunk 5: file 1 entries 155618, file 2 entries 155650
Chunk 6: file 1 entries 155618, file 2 entries 155649
Chunk 7: file 1 entries 155618, file 2 entries 155647
Chunk 8: file 1 entries 155618, file 2 entries 155644
Chunk 9: file 1 entries 155618, file 2 entries 155641
Chunk 10: file 1 entries 155618, file 2 entries 155643
Chunk 11: file 1 entries 155616, file 2 entries 155635
Total number of entries in all file 1 chunks: 1867414
Total number of entries in all file 2 chunks: 1867737
Worst case scenario checks to be made: 3487838222118
Starting the comparison....
Started process: <ForkProcess(ForkPoolWorker-1, started daemon)> (22249)
Started process: <ForkProcess(ForkPoolWorker-2, started daemon)> (22250)
Started process: <ForkProcess(ForkPoolWorker-3, started daemon)> (22251)
Started process: <ForkProcess(ForkPoolWorker-4, started daemon)> (22252)
Started process: <ForkProcess(ForkPoolWorker-5, started daemon)> (22253)
Started process: <ForkProcess(ForkPoolWorker-6, started daemon)> (22254)
Finished process: <ForkProcess(ForkPoolWorker-1, started daemon)> (22249)
Started process: <ForkProcess(ForkPoolWorker-7, started daemon)> (22255)
Finished process: <ForkProcess(ForkPoolWorker-2, started daemon)> (22250)
Started process: <ForkProcess(ForkPoolWorker-8, started daemon)> (22256)
Finished process: <ForkProcess(ForkPoolWorker-3, started daemon)> (22251)
Started process: <ForkProcess(ForkPoolWorker-9, started daemon)> (22257)
Started process: <ForkProcess(ForkPoolWorker-10, started daemon)> (22258)
Finished process: <ForkProcess(ForkPoolWorker-4, started daemon)> (22252)
Started process: <ForkProcess(ForkPoolWorker-11, started daemon)> (22259)
Finished process: <ForkProcess(ForkPoolWorker-5, started daemon)> (22253)
Started process: <ForkProcess(ForkPoolWorker-12, started daemon)> (22260)
Finished process: <ForkProcess(ForkPoolWorker-6, started daemon)> (22254)
Finished process: <ForkProcess(ForkPoolWorker-7, started daemon)> (22255)
Finished process: <ForkProcess(ForkPoolWorker-8, started daemon)> (22256)
Finished process: <ForkProcess(ForkPoolWorker-9, started daemon)> (22257)
Finished process: <ForkProcess(ForkPoolWorker-10, started daemon)> (22258)
Finished process: <ForkProcess(ForkPoolWorker-11, started daemon)> (22259)
Finished process: <ForkProcess(ForkPoolWorker-12, started daemon)> (22260)
Finished comparison in 57.057900914 seconds
Entries in file ../LODE_LAD-2019-Q2.csv not in file ../LODE_LAD-2019-Q3.csv: 12
Entries in file ../LODE_LAD-2019-Q3.csv not in file ../LODE_LAD-2019-Q2.csv: 335
```

# postcode_search.py

### Postcode Search
Search for an exact postcode in the Openreach LAD file or search for similar postcodes.

### Why?
The CSV files from Openreach are so big that applications like Microsoft Excel can't open them :(

```
$python3 ./postcode_search.py -l ../LODE_LAD-2019-Q3.csv -p E16PU
Loaded 1867749 postcodes from LAD file
+---------------+----------+--------+----------+---------------------+---------------------+-----------------+
| exchange_1141 | postcode | mdf_id | site_id  | fibre_upto_exchange | fibre_upto_postcode |  exchange_name  |
+---------------+----------+--------+----------+---------------------+---------------------+-----------------+
|     L/BIS     |  E1 6PU  | CLBIS  | EZ0025A1 |          Y          |          Y          | BISHOPSGATE T E |
+---------------+----------+--------+----------+---------------------+---------------------+-----------------+

$python3 ./postcode_search.py -l ../LODE_LAD-2019-Q3.csv -p E16P -n
Loaded 1867749 postcodes from LAD file
+---------------+----------+---------+----------+---------------------+---------------------+------------------------+
| exchange_1141 | postcode |  mdf_id | site_id  | fibre_upto_exchange | fibre_upto_postcode |     exchange_name      |
+---------------+----------+---------+----------+---------------------+---------------------+------------------------+
|     L/BIS     |  E1 6PA  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PD  |  CLBIS  | EZ0025A1 |          Y          |          Y          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PE  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PG  |  CLBIS  | EZ0025A1 |          Y          |          Y          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PJ  |  CLBIS  | EZ0025A1 |          Y          |          Y          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PL  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PN  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PP  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/SHO     |  E1 6PQ  |  CLSHO  | EZ0028A1 |          Y          |          Y          |     SHOREDITCH T E     |
|     L/BIS     |  E1 6PR  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PS  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PU  |  CLBIS  | EZ0025A1 |          Y          |          Y          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PX  |  CLBIS  | EZ0025A1 |          Y          |          Y          |    BISHOPSGATE T E     |
|     L/BIS     |  E1 6PZ  |  CLBIS  | EZ0025A1 |          Y          |          N          |    BISHOPSGATE T E     |
|      MTF      | LE1 6PA  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PB  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PD  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PL  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PN  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PP  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PS  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PT  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      MTF      | LE1 6PW  | EMMONTF | LE0079A1 |          Y          |          N          | LEICESTER MONTFORT ATE |
|      NT/B     | NE1 6PA  |   NENT  | NE0051A1 |          Y          |          Y          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PB  |   NENT  | NE0051A1 |          Y          |          Y          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PD  |   NENT  | NE0051A1 |          Y          |          Y          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PE  |   NENT  | NE0051A1 |          Y          |          N          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PF  |   NENT  | NE0051A1 |          Y          |          Y          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PN  |   NENT  | NE0051A1 |          Y          |          Y          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PT  |   NENT  | NE0051A1 |          Y          |          N          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PX  |   NENT  | NE0051A1 |          Y          |          N          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PY  |   NENT  | NE0051A1 |          Y          |          N          |    NEWCASTLE C T E     |
|      NT/B     | NE1 6PZ  |   NENT  | NE0051A1 |          Y          |          N          |    NEWCASTLE C T E     |
|     L/BER     | SE1 6PA  |  CLBER  | SE0004A1 |          Y          |          N          |     BERMONDSEY T E     |
|     L/WAT     | SE1 6PB  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PD  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PE  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PF  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PG  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PH  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PJ  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PL  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PN  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PP  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PQ  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PR  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PS  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PT  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PU  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PW  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
|     L/WAT     | SE1 6PX  | WRSTHBK | SE0049A1 |          Y          |          N          |     COLOMBO HOUSE      |
+---------------+----------+---------+----------+---------------------+---------------------+------------------------+
```
