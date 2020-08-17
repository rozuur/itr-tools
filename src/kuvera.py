import argparse
import datetime
import decimal
import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class Transaction:
    name: str
    isin: str
    family: str
    id: int
    units: decimal.Decimal
    purchase_date: datetime.datetime
    purchase_value: decimal.Decimal
    acquisition_value: decimal.Decimal
    grandfather_value: decimal.Decimal
    redemption_date: datetime.datetime
    redemption_value: decimal.Decimal
    stcg: decimal.Decimal
    ltcg: decimal.Decimal

    @staticmethod
    def dd_mm_yyyy(date: datetime.datetime) -> str:
        date = datetime.datetime.strptime(date, "%b %d, %Y")
        return date.strftime("%d/%m/%Y")

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
            self.dd_mm_yyyy(t.purchase_date),
            t.purchase_value,
            self.dd_mm_yyyy(t.redemption_date),
            perunit_sale,
        )


def parse_transactions(rows):
    # First line is fund with ISIN
    fund = rows[0][0]
    isin = _isin(fund)
    if not isin:
        return
    # Second line is Folio
    _ = rows[1][0]
    name, isin, family = re.match(r"(.+)\[ISIN: ([\w\s]+)\W+(\w+)", fund).groups()
    # Skip last transaction as it's fund total
    for transaction in rows[2:-1]:
        t = Transaction(name.strip(), isin, family, *transaction.to_list())
        if isinstance(t.id, int):
            yield t


def _isin(fund):
    try:
        return "ISIN" in fund
    except TypeError:
        return False


def parse_gains(filename):
    sheet = pd.read_excel(filename, sheet_name="Sheet1")
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
    parser.add_argument("--kuvera", help="Kuvera excel")
    args = parser.parse_args()
    transactions = parse_gains(args.kuvera)

    for t in transactions:
        row = t.cleartax()
        print(",".join([str(c).replace(",", "-") for c in row]))


if __name__ == "__main__":
    main()
