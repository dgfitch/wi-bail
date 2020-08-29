#!/bin/sh

zip -r cases.zip cases
scp cases.zip mindfill.com:
rm cases.zip
