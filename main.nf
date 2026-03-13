include {DORADO_BASECALL; DORADO_BASECALL_BARCODING} from "./modules/basecall.nf"
include {MERGE_READS; READ_STATS; READ_HIST; CONVERT_EXCEL; VALIDATE_SAMPLESHEET; CONVERT_READS; SUBSAMPLE_READS} from './modules/reads.nf'
include {SAVONT_ASV; SAVONT_CLASSIFY; SAVONT_COMBINE} from './modules/taxonomy.nf'
//include {EMU_ABUNDANCE; EMU_COMBINE} from './modules/taxonomy.nf'

include {MAKE_REPORT} from './modules/report.nf'

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
    
    ch_filtered_counts = Channel.empty()
    
    if (params.subsample) {
        SUBSAMPLE_READS(ch_reads_conv)
        ch_reads_conv = SUBSAMPLE_READS.out.reads
        ch_subsampled_stats = SUBSAMPLE_READS.out.stats
    } else {
        ch_subsampled_stats = Channel.empty()
    }
    
    SAVONT_ASV(ch_reads_conv)
    SAVONT_CLASSIFY(SAVONT_ASV.out.ch_asvs)
    SAVONT_COMBINE(SAVONT_CLASSIFY.out.ch_abundance.collect())
    
    MAKE_REPORT(
        READ_STATS.out.stats.collect(),
        SAVONT_ASV.out.counts.collect(),
        SAVONT_CLASSIFY.out.ch_abundance.collect().ifEmpty([]),
        SAVONT_COMBINE.out.ch_combined
    )
}
