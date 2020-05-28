#!/usr/bin/env python3

"""
Requirements:
sudo -H pip3 install PrettyTable
"""

import argparse
import csv
import io
import json
from prettytable import PrettyTable
import re
import sys
import zipfile


def find_exact_postcode(lad_data, postcode, results):

    postcode = postcode.lower().replace(" ", "")

    for row in lad_data:
        if row["postcode"].lower().replace(" ", "") == postcode:
            results.add_row(
                [
                    row["exchange_1141"],
                    row["postcode"],
                    row["mdf_id"],
                    row["site_id"],
                    row["fibre_upto_exchange"],
                    row["fibre_upto_postcode"],
                    row["exchange_name"],
                ]
            )
            return True

    print("Postcode not found in LAD file")
    return False


def find_postcode(lad_data, postcode, results):

    postcode = postcode.lower().replace(" ", "")

    for row in lad_data:
        if postcode in row["postcode"].lower().replace(" ", ""):
            results.add_row(
                [
                    row["exchange_1141"],
                    row["postcode"],
                    row["mdf_id"],
                    row["site_id"],
                    row["fibre_upto_exchange"],
                    row["fibre_upto_postcode"],
                    row["exchange_name"],
                ]
            )

    if len(results._rows) == 0:
        print("Postcode not found in LAD file")
        return False
    else:
        return True


def load_csv(filename):

    """
    This function returns each CSV row as an OrderedDict containing 2-tuples:
    OrderedDict([('exchange_1141', 'AB/WEST'),
                 ('postcode', 'AB10 7LX'),
                 ('mdf_id', 'NSWES'),
                 ('site_id', 'AB0004A1'),
                 ('fibre_upto_exchange', 'Y'),
                 ('fibre_upto_postcode', 'N'),
                 ('exchange_name', 'WEST AUTO EXCHANGE')])
    OrderedDict([('exchange_1141', 'AB'),
                 ('postcode', 'AB10 7LY'),
                 ('mdf_id', 'NSLNG'),
                 ('site_id', 'AB0006A1'),
                 ('fibre_upto_exchange', 'Y'),
                 ('fibre_upto_postcode', 'N'),
                 ('exchange_name', 'ABERDEEN CENTRAL TE')])
    """

    if filename == None:
        print("LAD file filename not provided")
        return False

    try:

        # Check if ZIP archive filename is given
        if filename.split(".")[-1] == "zip":

            try:
                zip_data = zipfile.ZipFile(filename)
            except Exception as e:
                print("Couldn't open zip file {}: {}".format(filename, e))
                return False

            # Look for the LAD file inside ZIp archive
            for fname in zip_data.namelist():
               if re.match(".*LODE_LAD.*", fname):
                  csv_filename = fname
                  break
            else:
                print("Couldn't find LAD CSV file in ZIP archive")
                return False

            # Decompress it
            try:
                csv_file = io.StringIO(
                    zip_data.read(
                        csv_filename
                    ).decode("ISO-8859-1")
                )
            except Exception as e:
                print(
                    "Couldn't decompression CSV file from ZIP archive "
                    "to string: {}".format(e)
                )
                return False


       # Assume CSV file
        else:
            try:
                csv_file = open(filename, "r", encoding="ISO-8859-1")
            except Exception:
                print("Couldn't open file {}".format(filename))
                return False

    except Exception as e:
        print(
            "LAD file name invalid, expected foo.csv or foo.zip: {}".format(e)
        )


    try:
        csv_data = csv.DictReader(csv_file)
    except Exception as e:
        print("Couldn't parse CSV file: {}".format(e))
        return False

    rows = [row for row in csv_data]

    csv_file.close()

    print("Loaded {} postcodes from LAD file".format(len(rows)))
    return rows


def parse_cli_args():

    parser = argparse.ArgumentParser(
        description="Search the OR LAD file for a postcode",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--lad-file",
        help="Openreach LAD file, CSV or ZIP containing CSV",
        type=str,
        default=None
    )
    parser.add_argument(
        "-n",
        "--not-exact",
        help="Disable exact postcode match, return similar postcodes",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--postcode",
        help="Exact postcode to search for",
        type=str,
        default=None
    )

    return vars(parser.parse_args())


def main():

    args = parse_cli_args()
    if args == False:
        return False

    if not args["postcode"]:
        print("Need to specify a postcode to search for")
        return False

    if not args["lad_file"]:
        print("Need to specify LAD filename")
        return False

    lad_data = load_csv(args["lad_file"])
    if not lad_data:
        return False

    results = PrettyTable(
        [
            "exchange_1141",
            "postcode",
            "mdf_id",
            "site_id",
            "fibre_upto_exchange",
            "fibre_upto_postcode",
            "exchange_name",
        ]
    )

    if args["not_exact"]:
        if not find_postcode(lad_data, args["postcode"], results):
            return False
    else:
        if not find_exact_postcode(lad_data, args["postcode"], results):
            return False

    if len(results._rows) > 0:
        results.sortby = "postcode"
        print(results)

    return True


if __name__ == "__main__":
    sys.exit(main())
