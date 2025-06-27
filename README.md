# q2-checkm
![CI](https://github.com/bokulich-lab/q2-checkm/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/bokulich-lab/q2-checkm/branch/main/graph/badge.svg?token=RSZD1TD9HG)](https://codecov.io/gh/bokulich-lab/q2-checkm)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

QIIME 2 plugin for assessing the quality of (meta)genomes using CheckM.

## Installation
We recommend installing q2-checkm within a fresh conda environment. You can create such an environment by using one of the 
environment files from the [environment-files](./environment-files) directory:

```shell
conda env create -n checkm-env --file  https://raw.githubusercontent.com/bokulich-lab/q2-checkm/main/environment-files/q2-checkm-qiime2-tiny-2025.4.yml
```

Since `pplacer` is only available through conda for Linux - we need to install it manually. 
You can use our script to fetch the binary directly:
```shell
conda activate checkm-env
curl -s https://raw.githubusercontent.com/bokulich-lab/q2-checkm/main/install-pplacer.sh | bash
```

```shell
qiime dev refresh-cache
qiime checkm --help
```
