def merge_ranges(ranges):
    result = []
    for start, end in sorted(ranges):
        if start > end:
            raise ValueError('reversed interval')
        if not result:
            result.append((start, end))
            continue
        last_start, last_end = result[-1]
        if start <= last_end + 1:
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
