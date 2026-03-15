#!/usr/bin/awk -f

# bincount.awk - Bin counting for sequence data histograms
# Usage: bincount.awk -v type=[len|gc|qual] input_file
#        ... | bincount.awk -v type=[len|gc|qual]

BEGIN {
    if (!type) type = "len"
    FS = " "
    OFS = "\t"
}

{
    if (type == "len") {
        # 100bp bins
        bin = int($1 / 100) * 100
        bases[bin] += $1
    } else if (type == "gc") {
        # 1% bins (input is 0-1)
        bin = int($1 * 100)
    } else if (type == "qual") {
        # 0.1 step bins
        bin = int($1 * 10) / 10
    }
    count[bin]++
}

END {
    for (b in count) {
        if (type == "qual") {
            printf "%.1f\t%d\t%d\n", b, count[b], 0
        } else if (type == "len") {
            printf "%d\t%d\t%d\n", b, count[b], bases[b]
        } else {
            printf "%d\t%d\t%d\n", b, count[b], 0
        }
    }
}
