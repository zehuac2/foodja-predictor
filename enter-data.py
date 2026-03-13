import csv
import os
from datetime import date

CSV_FILE = "restaurants.csv"
TODAY = date.today().strftime("%m/%d/%Y")


def prompt_date():
    raw = input(f"Date [{TODAY}]: ").strip()
    if not raw:
        return TODAY
    try:
        return date.fromisoformat(raw).strftime("%m/%d/%Y")
    except ValueError:
        pass
    try:
        return date.strptime(raw, "%m/%d/%Y").strftime("%m/%d/%Y")
    except ValueError:
        pass
    # Try MM/DD without year
    try:
        return date.strptime(f"{raw}/{date.today().year}", "%m/%d/%Y").strftime("%m/%d/%Y")
    except ValueError:
        raise ValueError(f"Unrecognized date format: {raw}")


def get_next_index(target_date):
    if not os.path.exists(CSV_FILE):
        return 0
    with open(CSV_FILE, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["date"] == target_date]
    return len(rows)


def main():
    try:
        target_date = prompt_date()
    except ValueError as e:
        print(e)
        return

    print(f"\nEntering restaurants for {target_date}. Type 'done' or press Ctrl+D to save and exit.\n")

    entries = []
    index = get_next_index(target_date)

    while True:
        try:
            name = input(f"  Restaurant #{index}: ").strip()
        except EOFError:
            print()
            break
        if name.lower() == "done":
            break
        entries.append({"date": target_date, "index": index, "restaurant": name})
        index += 1

    if not entries:
        print("No entries added.")
        return

    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "index", "restaurant"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(entries)

    print(f"\nAdded {len(entries)} restaurant(s) to {CSV_FILE}.")


if __name__ == "__main__":
    main()
