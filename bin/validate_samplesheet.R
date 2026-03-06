#!/usr/bin/env Rscript

# reads csv/tsv and checks if valid
#
# writes back *-checked.csv if ok

# arg[1] is csv

arg <- commandArgs(trailingOnly = T)

library(readr)
library(stringr)
library(dplyr)

# valid barcode names
bc_pattern <- "^barcode[0-9]+$"

# to print dataframe to stdout pretty
print_and_capture <- function(x) {
  paste(capture.output(print(x)), collapse = "\n")
}

df <- readr::read_delim(arg[1], col_names = T, trim_ws = T)

# CHECKS #####################################################
# colnames contain 'sample', 'barcode'
if (!all(c("sample", "barcode") %in% colnames(df))) {
  stop(
    paste0(
      "\n--------------------------------------\n",
      "\nSamplesheet must contain columns sample,barcode\n",
      "\nThe provided samplesheet has columns:\n",
      str_flatten(colnames(df), collapse = ", "),
      "\n--------------------------------------\n"
    )
  )
}

# remove rows where sample or barcode is NA
df <- df[complete.cases(df[, c("sample", "barcode")]), ]

# remove white space first, to lower
df$sample <- str_squish(df$sample) %>% str_replace_all("\\s+", "_")
df$barcode <- str_squish(df$barcode)

# valid barcode names barcode01 to barcode96
# bc_pattern <- '^barcode[0-9]+$'
bc_pattern <- "^barcode(0[1-9]|[1-8][0-9]|9[0-6])$"
bc_vector <- str_detect(df$barcode, bc_pattern)

if (!all(bc_vector)) {
  stop(
    paste0(
      "\n--------------------------------------\n",
      "\nBarcode names must be valid - barcode01 to barcode96!\n",
      print_and_capture(df[which(!bc_vector), ]),
      "\n--------------------------------------\n"
    )
  )
}

# barcode unique
# get indices of duplicates:) stupid R
dups_vector <- duplicated(df$barcode) | duplicated(df$barcode, fromLast = T)

if (any(dups_vector)) {
  stop(
    paste0(
      "\n--------------------------------------\n",
      "\nBarcodes must be unique!\n",
      print_and_capture(df[which(dups_vector), ]),
      "\n--------------------------------------\n"
    )
  )
}

# sample names unique
dups_vector <- duplicated(df$sample) | duplicated(df$sample, fromLast = T)

if (any(dups_vector)) {
  stop(
    paste0(
      "\n--------------------------------------\n",
      "\nSample names must be unique!\n",
      print_and_capture(df[which(dups_vector), ]),
      "\n--------------------------------------\n"
    )
  )
}

# max len of sample name is 24 - perbase weird crash
sl_vector <- str_length(df$sample)
if (!all(sl_vector <= 24)) {
  stop(paste0(
    "\nSamples with too long names:",
    "\n--------------------------------------\n",
    print_and_capture(df[sl_vector > 24, ]),
    "\n--------------------------------------\n",
    "Sample names have to be < 25 characters long",
    "\n--------------------------------------\n"
  ))
}

# special characters in sample names
sn_vector <- str_detect(df$sample, "^[a-zA-Z0-9\\_\\-]+$")
if (!all(sn_vector)) {
  stop(
    paste0(
      "\nSamples with special characters:",
      "\n--------------------------------------\n",
      print_and_capture(df[!sn_vector, ]),
      "\n--------------------------------------\n"
    )
  )
}

# only numerics in sample names
num_vector <- str_detect(df$sample, "^[0-9]+$")
if (any(num_vector)) {
  stop(
    paste0(
      "\nNumeric sample names: ",
      "\n--------------------------------------\n",
      print_and_capture(df[num_vector, ]),
      "\n--------------------------------------\n"
    )
  )
}

write_csv(df, file = "samplesheet-validated.csv")
