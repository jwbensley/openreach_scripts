import argparse
import csv
import math
import multiprocessing
from multiprocessing import Pool
import operator
import os
import pprint
import sys
import timeit


def chunk_data(chunk_size, lad_data_1, lad_data_2, num_proc):

    """
    This function takes two data sets and splits them into chunks
    of chunk_size. It returns one list which is a list of lists;
    chunks = [
        [ set_1_chunk_1, set_2_chunk_1],
        [ set_1_chunk_2, set_2_chunk_2],
        [ set_1_chunk_3, set_2_chunk_3]
    ]
    """

    print("Chunking and merging LAD and Fibre data...")
    start_time = timeit.default_timer()

    # Chunk up the 1st data set
    lad_data_1_chunks = [
        lad_data_1[i : i + chunk_size]
        for i in range(0, len(lad_data_1), chunk_size)
    ]

    # Chunk the 2nd data set.
    # Try to match the chunks from the 1st data set.
    lad_data_2_chunks = []
    for chunk in lad_data_1_chunks:

        start, end = None, None
        # First postcode in this chunk
        first_postcode = chunk[0]["postcode"]
        # Last postcode in this chunk
        last_postcode = chunk[len(chunk) - 1]["postcode"]

        """
        Loop over all the entries in the 2nd data set, find the index in the
        2nd set for the first postcode in the current chunk of data set 1,
        and the index of the last postcode in the currnet chunk of the data
        set 1.

        There may not be an exact match for the first and last postcodes in
        the current data set 1 chunk in the 2nd data set. Try matching the
        full postcode string, then decrement the string length letter by
        letter match a shorter and shorter string until we have a match.
        """
        for i in range(len(first_postcode), 0, -1):
            for chunk_index, chunk_entry in enumerate(lad_data_2):
                if first_postcode[:i] == chunk_entry["postcode"][:i]:
                    start = chunk_index
                    break
            else:
                """
                There was no match for the first postcode in this data set 1
                chunk.
                """
                continue
            break

        for i in range(len(last_postcode), 0, -1):
            for chunk_index, chunk_entry in enumerate(lad_data_2):
                if last_postcode[:i] == chunk_entry["postcode"][:i]:
                    end = chunk_index
                    break
            else:
                """
                There was no match for the last postcode in this data set 1
                chunk.
                """
                print("Couldn't find the last postcode ({})".format(
                    last_postcode
                    )
                )
                end = len(lad_data_2)-1
                continue
            break

        lad_data_2_chunks.append(lad_data_2[start:end])
        del (lad_data_2[start:end])


    chunks = [[lad_data_1_chunks[i], lad_data_2_chunks[i]] for i in range(0, num_proc)]

    end_time = timeit.default_timer()
    print("Chunked data in {} seconds".format(end_time - start_time))


    for index, chunk in enumerate(chunks):
        print(
            "Chunk {}: file 1 entries {}, file 2 entries {}".format(
                index, len(chunk[0]), len(chunk[1])
            )
        )

    lad_1_total = sum([len(chunk[0]) for chunk in chunks])
    print("Total number of entries in all file 1 chunks: {}".format(lad_1_total))
    lad_2_total = sum([len(chunk[1]) for chunk in chunks])
    print("Total number of entries in all file 2 chunks: {}".format(lad_2_total))
    print("Worst case scenario checks to be made: {}".format(lad_1_total * lad_2_total))

    return chunks


def compare_chunks(chunks):

    """
    This function will remove postcodes found in both chunks being compared
    and return a list of two lists, the two sub-lists are the postcodes left
    over (no matches found in both chunks being compared)
    """

    print(
        "Started process: {} ({})".format(
            multiprocessing.current_process(), os.getpid()
        )
    )

    lad_data_2 = chunks[1][:]

    for lad_2_entry in lad_data_2:
        for lad_1_entry in chunks[0]:
            if lad_2_entry["postcode"] == lad_1_entry["postcode"]:
                chunks[0].remove(lad_1_entry)
                chunks[1].remove(lad_2_entry)
                break

    print(
        "Finished process: {} ({})".format(
            multiprocessing.current_process(), os.getpid()
        )
    )

    return chunks


def format_postcodes(lad_data_1, lad_data_2):

    print("Formatting postcodes...")
    start_time = timeit.default_timer()

    for lad_1_entry in lad_data_1:
        lad_1_entry["postcode"] = "".join(lad_1_entry["postcode"].upper().split())

    for lad_2_entry in lad_data_2:
        lad_2_entry["postcode"] = "".join(lad_2_entry["postcode"].upper().split())

    end_time = timeit.default_timer()
    print("Formatted in {} seconds".format(end_time - start_time))


def load_csv_to_dict(filename):

    print("Loading csv...")
    start_time = timeit.default_timer()

    """
    This function returns each CSV row as an OrderedDict (a list of 2-tuples),
    the result is a list of OrderedDict's:
    [
        OrderedDict(
            [   ('exchange_1141', 'AB/WEST'),
                ('postcode', 'AB10 7LX'),
                ('mdf_id', 'NSWES'),
                ('site_id', 'AB0004A1'),
                ('fibre_upto_exchange', 'Y'),
                ('fibre_upto_postcode', 'N'),
                ('exchange_name', 'WEST AUTO EXCHANGE')
            ]
        ),
        OrderedDict(
            [
                ('exchange_1141', 'AB'),
                ('postcode', 'AB10 7LY'),
                ('mdf_id', 'NSLNG'),
                ('site_id', 'AB0006A1'),
                ('fibre_upto_exchange', 'Y'),
                ('fibre_upto_postcode', 'N'),
                ('exchange_name', 'ABERDEEN CENTRAL TE')
            ]
        )
    ]
    """

    if filename == None:
        print("Network CSV filename not provided")
        return False

    try:
        csv_file = open(filename, "r", encoding="ISO-8859-1")
    except Exception:
        print("Couldn't open csv file {}".format(filename))
        return False

    try:
        csv_data = csv.DictReader(csv_file)
    except Exception as e:
        print("Couldn't parse CSV file".format(e))
        return False

    rows = [row for row in csv_data]

    csv_file.close()

    print("Loaded {} CSV rows from {}".format(len(rows), filename))

    end_time = timeit.default_timer()
    print("Loaded in {} seconds".format(end_time - start_time))

    return rows


def load_lad_files(args):

    lad_data_1 = load_csv_to_dict(args["file_1"])
    if not lad_data_1:
        return False

    lad_data_2 = load_csv_to_dict(args["file_2"])
    if not lad_data_2:
        return False

    return lad_data_1, lad_data_2


def parse_cli_args():

    parser = argparse.ArgumentParser(
        description="Openreach LAD file comparison script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-f1", "--file_1", help="LAD file 1", type=str, default="LODE_LAD-2019-Q2.csv"
    )
    parser.add_argument(
        "-f2", "--file_2", help="LAD file 2", type=str, default="LODE_LAD-2019-Q3.csv"
    )

    return vars(parser.parse_args())


def write_to_csv(csv_data, filename):

    try:
        with open(filename, "w") as csvfile:
            fieldnames = [
                "exchange_1141",
                "postcode",
                "mdf_id",
                "site_id",
                "fibre_upto_exchange",
                "fibre_upto_postcode",
                "exchange_name",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in csv_data:
                writer.writerow(row)
    except Exception as e:
        print("Unable to write CSV entries to {}: {}".format(filename, e))
        return False

    return True


def sort_postcodes(lad_data_1, lad_data_2):

    print("Sorting postcodes...")
    start_time = timeit.default_timer()

    lad_data_1.sort(key=operator.itemgetter("postcode"))
    lad_data_2.sort(key=operator.itemgetter("postcode"))

    end_time = timeit.default_timer()
    print("Sorted in {} seconds".format(end_time - start_time))


def main():

    pp = pprint.PrettyPrinter(indent=4)
    # Returns the number of threads the CPU has
    num_proc = multiprocessing.cpu_count()
    Pool = multiprocessing.Pool(num_proc)

    args = parse_cli_args()
    if args == False:
        return False

    lad_data_1, lad_data_2 = load_lad_files(args)
    if not lad_data_1 or not lad_data_2:
        return Fasle

    format_postcodes(lad_data_1, lad_data_2)

    sort_postcodes(lad_data_1, lad_data_2)

    # The chunk size is driven by the smaller file
    if len(lad_data_1) < len(lad_data_2):
        chunk_size = int(math.ceil(len(lad_data_2) / num_proc))
    else:
        chunk_size = int(math.ceil(len(lad_data_1) / num_proc))

    print("Number of CPUs:  {}".format(num_proc))
    print("Chunk size per CPU: {}".format(chunk_size))

    chunks = chunk_data(chunk_size, lad_data_1, lad_data_2, num_proc)


    print("Starting the comparison....")
    start_time = timeit.default_timer()

    # compare_chunks() will return any postcode not in both chunks
    unique_postcodes = Pool.map(compare_chunks, chunks)

    lad_1_only = []
    lad_2_only = []

    for chunk_lists in unique_postcodes:
        for lad_2_entry in chunk_lists[1]:
            lad_2_only.append(lad_2_entry)

    for chunk_lists in unique_postcodes:
        for lad_1_entry in chunk_lists[0]:
            lad_1_only.append(lad_1_entry)

    end_time = timeit.default_timer()
    print("Finished comparison in {} seconds".format(end_time - start_time))

    print(
        "Entries in file {} not in file {}: {}".format(
            args["file_1"], args["file_2"], len(lad_1_only)
        )
    )
    print(
        "Entries in file {} not in file {}: {}".format(
            args["file_2"], args["file_1"], len(lad_2_only)
        )
    )

    if not write_to_csv(lad_1_only, args["file_1"].split('.csv')[0] + "_only.csv"):
        return False
    if not write_to_csv(lad_2_only, args["file_2"].split('.csv')[0] + "_only.csv"):
        return False

    return True


if __name__ == "__main__":
    sys.exit(main())
