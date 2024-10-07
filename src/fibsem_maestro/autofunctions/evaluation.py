import numpy as np


def max_mean(criterion_values):
    """ Change criterion_values (calculate mean for each value). Best value is max """
    # convert list of criteria to mean values for each sweeping variable value
    for key, value_list in list(criterion_values.items()):
        criterion_values[key] = np.mean(value_list)      # find the maximal value
    best_value = max(criterion_values, key=criterion_values.get)
    return best_value


def best_diff(criterion_values):
    """
    Assumption: the middle item is a base value and all remaining value lists have the same length
    Take difference of each wd with base wd
    """
    # get the first values (base wd)
    first_key = next(iter(criterion_values))
    base = criterion_values[first_key]
    for key, value_list in list(criterion_values.items()):
        criterion_values[key] -= base
    del criterion_values[first_key]  # del base value
    best_value = max(criterion_values, key=criterion_values.get)
    return best_value