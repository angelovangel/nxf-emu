# emu image
FROM continuumio/miniconda3:latest

#
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    tar \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN conda config --add channels defaults && \
    conda config --add channels bioconda && \
    conda config --add channels conda-forge && \
    conda install -y emu osfclient && \
    conda clean -afy

# Download the Emu default database (v3.0+)
ENV EMU_DATABASE_DIR=/opt/emu_database
RUN mkdir -p ${EMU_DATABASE_DIR} && \
    cd ${EMU_DATABASE_DIR} && \
    osf -p 56uf7 fetch osfstorage/emu-prebuilt/emu.tar && \
    tar -xvf emu.tar && \
    rm emu.tar


