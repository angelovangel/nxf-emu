def logColors() {
    return [
        reset: "\033[0m",
        green: "\033[0;32m",
        blue: "\033[0;34m",
        yellow: "\033[0;33m",
        cyan: "\033[0;36m"
    ]
}

def showHelp() {
    def c = logColors()

    log.info """
=============================================
${c.yellow}NXF-SAVONT${c.reset}
${c.yellow}taxonomic profiling for full-length 16S reads${c.reset}
=============================================

${c.yellow}Input options:${c.reset}
    ${c.green}--pod5 <dir>${c.reset}           Directory with POD5 files (use when basecalling)
    ${c.green}--samplename <str>${c.reset}     Sample name to use for non-barcoded runs
    ${c.green}--reads <file|dir>${c.reset}     BAM/FASTQ file or directory of reads (skips basecalling)
    ${c.green}--kit${c.reset}                  Use for barcoded run - barcoding kit name (--samplesheet required)
    ${c.green}--samplesheet${c.reset}          Use for barcoded run - CSV or XLSX with columns: sample,barcode (--kit required)

${c.yellow}Filtering options:${c.reset}
    ${c.green}--minreadlength <int>${c.reset}  Minimum read length filter (default: 1100)
    ${c.green}--maxreadlength <int>${c.reset}  Maximum read length filter (default: 2000)
    ${c.green}--norm <int>${c.reset}           Normalize all samples to this depth (smallest sample depth if not specified)
    ${c.green}--subsample <float>${c.reset}    Subsample reads to this proportion (0 to 1)

${c.yellow}Taxonomic profiling:${c.reset}
    ${c.green}--db <str>${c.reset}                Classification database (options: emu, silva; default: emu)
    ${c.green}--species_threshold <num>${c.reset} Percentage identity for species (default: 99)
    ${c.green}--genus_threshold <num>${c.reset}   Percentage identity for genus (default: 94.5)

${c.yellow}Output & generic:${c.reset}
    ${c.green}--outdir${c.reset}               Output directory name (default: output)
    ${c.green}--cpus${c.reset}                 Number of CPUs to use (default: 16)
    ${c.green}--help${c.reset}                 Show this help message
    """.stripIndent()
}
