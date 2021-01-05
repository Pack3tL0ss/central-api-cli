'''
Collection of functions used to clean output from Aruba Central API into a consistent structure.
'''

from typing import List


def get_all_groups(data: List[str, ]) -> list:
    return [g for _ in data for g in _ if g != "unprovisioned"]
