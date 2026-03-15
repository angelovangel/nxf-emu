#!/usr/bin/env nextflow


process DORADO_BASECALL {
    // pod5 view is available in container
    container 'docker.io/nanoporetech/dorado:latest'

    publishDir "${params.outdir}/00-basecall", mode: 'copy', pattern: '*.bam'
    tag "${params.model}"
    
    input:
        path pod5

    output:
        path "*.bam"
        path "versions.txt", emit: versions

    script:
    """
    dorado basecaller ${params.model} ${pod5} > reads.bam

    # check if reads.bam has reads and exit if no
    nreads=\$(wc -l < reads.bam)

    if [ "\$nreads" -eq 0 ]; then
        echo "No reads found in reads.bam, exiting." >&2
        exit 1
    fi
    
    samplename=\$(samtools head reads.bam | grep "^@RG" | grep -o "LB:[^[:space:]]*" | cut -d: -f2 | head -n 1)
    clean_name=\$(echo "\$samplename" | LC_ALL=C tr -dc '[:graph:]')

    if [ "${params.samplename}" != null ]; then
        clean_name=${params.samplename}
    fi
    echo "samplename: \$samplename"
    echo "clean name: \$clean_name"
    mv reads.bam \$clean_name.bam

    cat <<EOF > versions.txt
    ${task.process}: dorado \$(dorado --version 2>&1 | sed 's/dorado //')
    ${task.process}: samtools \$(samtools --version | head -n 1 | awk '{print \$2}')
    EOF
    """
}

process DORADO_BASECALL_BARCODING {

    container 'docker.io/nanoporetech/dorado:latest'

    //publishDir "${params.outdir}/00-basecall", mode: 'copy'
    tag "${params.model}"

    input:
        path pod5

    output:
        path "bam_pass", type: 'dir', emit: ch_bam_pass
        path "versions.txt", emit: versions

    script:
    """
    dorado basecaller --kit-name ${params.kit} -o basecalls ${params.model} ${pod5}
    # the folder with barcodes is basecalls/folder1/folder2/folder3/bam_pass
    [ -d "basecalls" ] || { echo "Basecalls output folder empty!" >&2; exit 1; }
    ln -s basecalls/*/*/*/bam_pass bam_pass

    cat <<EOF > versions.txt
    ${task.process}: dorado \$(dorado --version 2>&1 | sed 's/dorado //')
    EOF
    """
}
