
process EMU {
    container 'docker.io/aangeloo/emu:latest'
    //errorStrategy 'ignore'
    tag "${reads.name}"
    publishDir "${params.outdir}/01-taxonomy", mode: 'copy', pattern: '**.tsv'

    input:
        path reads

    output:
        path "*.tsv"

    script:
    """
    emu abundance --keep-counts --output-dir . --threads $task.cpus $reads
    """
}