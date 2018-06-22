#!/usr/bin/env bash

pushd /tmp
wget https://github.com/AGWA/git-crypt/archive/master.zip -O git-crypt.zip
unzip git-crypt.zip
cd git-crypt-master
make
popd