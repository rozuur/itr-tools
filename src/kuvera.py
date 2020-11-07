import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import xlrd

CLEARTAX_DATE_FORMAT = "%d/%m/%Y"
KUVERA_ISIN_PATTERN = re.compile(r"(.+)\[ISIN: ([\w\s]+)\W+(\w+)")


@dataclass
class Transaction:

    name: str
    isin: str
    folio: str
    family: str
    _id: int
    units: float
    purchase_date: datetime
    purchase_value: float
    purchase_nav: float
    acquisition_value: float
    grandfather_value: float
    grandfather_nav: float
    redemption_date: datetime
    redemption_value: float
    redemption_nav: float
    stcg: float
    ltcg: float

    def __parse_date(self, date):
        if isinstance(date, str):
            return datetime.strptime(date, "%b %d, %Y")
        return date

    def __post_init__(self):
        self.purchase_date = self.__parse_date(self.purchase_date)
        self.redemption_date = self.__parse_date(self.redemption_date)

    def cleartax(self):
        t = self
        perunit_sale = t.redemption_value / t.units if t.units > 0 else 0
        # Family will be auto detected in cleartax based on ISIN
        family = ""
        return (
            family,
            t.isin,
            t.name,
            t.units,
            t.purchase_date.strftime(CLEARTAX_DATE_FORMAT),
            t.purchase_value,
            t.redemption_date.strftime(CLEARTAX_DATE_FORMAT),
            perunit_sale,
        )


def parse_transactions(rows):
    # First line is fund with ISIN
    fund = rows[0][0]
    isin = _isin(fund)
    if not isin:
        return
    # Second line is Folio
    folio = rows[1][0]
    name, isin, family = KUVERA_ISIN_PATTERN.match(fund).groups()
    for transaction in rows[2:]:
        t = Transaction(name.strip(), isin, family, folio, *transaction.to_list())
        # Ignore all other rows which doesn't have valid index
        if isinstance(t._id, int):
            yield t


def _isin(fund):
    try:
        return "ISIN" in fund
    except TypeError:
        return False


def parse_gains(filename):
    try:
        sheet = pd.read_excel(filename, sheet_name="Sheet1")
    except xlrd.biffh.XLRDError:
        print(
            "Kuvera capital gains sheet is corrupted, try again after manually opening and saving the sheet.",
            file=sys.stderr,
        )
        exit(1)

    transactions = []
    rows = []
    for pd_row in sheet.iterrows():
        row = pd_row[1]
        # if row contains [ISIN: *] then it's a start
        isin = _isin(row[0])
        if isin:
            transactions.extend(parse_transactions(rows))
            rows = []
        rows.append(row)
    return transactions


def main():
    parser = argparse.ArgumentParser("Capital Gains")
    parser.add_argument("filename", nargs=1)
    args = parser.parse_args()
    transactions = parse_gains(args.filename[0])

    for t in transactions:
        row = t.cleartax()
        print(",".join([str(c).replace(",", "-") for c in row]))


if __name__ == "__main__":
    main()
