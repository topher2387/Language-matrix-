def merge_ranges(ranges):
    # Check for reversed intervals
    for start, end in ranges:
        if start > end:
            raise ValueError('Reversed interval')

    # Sort by start value
    sorted_ranges = sorted(ranges, key=lambda x: x[0])

    # Merge overlapping and adjacent intervals
    merged = []
    for start, end in sorted_ranges:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]
            if start <= last_end + 1:  # Overlapping or adjacent (inclusive)
                merged[-1][1] = max(last_end, end)
            else:
                merged.append([start, end])

    return [tuple(interval) for interval in merged]
