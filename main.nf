include {DORADO_BASECALL; DORADO_BASECALL_BARCODING} from "./modules/basecall.nf"
include {MERGE_READS; READ_STATS; READ_HIST; CONVERT_EXCEL; VALIDATE_SAMPLESHEET; CONVERT_READS; FILTER_READS} from './modules/reads.nf'
include {EMU} from './modules/taxonomy.nf'

if (params.kit && !params.samplesheet) {
    error "If --kit is specified, --samplesheet must also be provided."
}

if (!params.kit && params.samplesheet) {
    error "If --samplesheet is provided, --kit must also be specified."
}

workflow basecall {
    ch_pod5 = Channel.fromPath(params.pod5, checkIfExists: true)
    ch_samplesheet = params.samplesheet ? Channel.fromPath(params.samplesheet, checkIfExists: true) : null
    
    if (params.kit) {    
        if (params.samplesheet.endsWith('.xlsx')) {
            ch_samplesheet_validated = CONVERT_EXCEL(ch_samplesheet) | VALIDATE_SAMPLESHEET
        
        } else if (params.samplesheet.endsWith('.csv')) {
            ch_samplesheet_validated = VALIDATE_SAMPLESHEET(ch_samplesheet)
        
        } else {
            error "Unsupported samplesheet format. Use .xlsx or .csv"
        }
        
        DORADO_BASECALL_BARCODING(ch_pod5)  

        ch_samplesheet_validated
        .splitCsv(header:true)
        .filter{ it -> it.barcode =~ /^barcode*/ }
        .map { row -> tuple( row.sample, row.barcode ) }
        .combine( DORADO_BASECALL_BARCODING.out.ch_bam_pass )
        | MERGE_READS 

    } else {
        DORADO_BASECALL(ch_pod5)
    }

    emit:
    ch_basecall = params.kit ? MERGE_READS.out : DORADO_BASECALL.out
}

workflow {
    if (params.reads) {        
        if ( file(params.reads).isDirectory() ) {
            pattern = "*.{bam,fasta,fastq,fastq.gz,fq,fq.gz}"
            ch_reads = Channel.fromPath(params.reads + "/" + pattern, type: 'file', checkIfExists: true)           
        } else {
            ch_reads = Channel.fromPath(params.reads, checkIfExists: true)        
        }
    } else {
        ch_reads = basecall().ch_basecall
    }
    
    
    CONVERT_READS(ch_reads) | READ_STATS
    
    ch_reads_conv = CONVERT_READS.out
    ch_reads_conv = params.filter ? FILTER_READS(ch_reads_conv).ch_filtered_reads : ch_reads_conv
    
    EMU(ch_reads_conv)
}