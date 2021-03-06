#!/usr/bin/env python
#
# Copyright (c) 2014-2016 Christian Schudoma, The Sainsbury Laboratory
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import sys
import subprocess
import argparse
from collections import Counter

from Bio import Entrez

whoami = None
assert whoami, 'Please set whoami=<your email address> in order to not anger NCBI...'
Entrez.email = whoami

def fetchTaxonomyData(ids):
    handle = Entrez.efetch(db='Taxonomy', id=','.join(ids), retmode='xml')
    records = Entrez.read(handle)
    return records

def writeKronaInput(fi, taxInfo, unclassified=0):
    if unclassified:
        fi.write('%i\tUnclassified\n' % unclassified)
    for tid in sorted(taxInfo, key=lambda x:taxInfo[x][0]['Lineage']):
        fi.write('%i\t%s\n' % (taxInfo[tid][1], '; '.join([taxInfo[tid][0]['Lineage'].strip(), taxInfo[tid][0]['ScientificName']]).replace('; ', '\t').strip('\t')))
    pass

def writeOutput(out, taxInfoDict, c):
    for tid in sorted(taxInfoDict, reverse=True, key=lambda x:taxInfoDict[x][1]):
        data = [tid, taxInfoDict[tid][1], taxInfoDict[tid][0]['TaxId'], taxInfoDict[tid][0]['Lineage'], taxInfoDict[tid][0]['ScientificName']]
        out.write('\t'.join(map(str, data)) + '\n')
    data = (sum(c.values()) - c['0'], sum(c.values()), (sum(c.values()) - c['0']) / float(sum(c.values())) * 100, c['0'])
    try:
        out.write('%i/%i (%.5f%%) classified, %i unclassified\n' % data)
    except:
        out.write(str(data) + ':ERR\n')



def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--include-unclassified', action='store_true')
    parser.add_argument('--draw-krona-plot', type=str, default='')
    parser.add_argument('--path-to-krona', type=str, default='')
    parser.add_argument('--write-summary', type=str, default='')
    parser.add_argument('kraken_results', type=str)
    args = parser.parse_args()

    assert args.write_summary or args.draw_krona_plot
    assert os.path.exists(args.kraken_results)

    with open(args.kraken_results) as kraken_results:
        try:
            taxCounter = Counter(line.strip().split()[2] for line in kraken_results)
        except:
            sys.stderr.write('Wrong input data.\n')
            sys.exit(1)

    taxids = sorted(taxCounter.keys(), key=lambda x:taxCounter[x], reverse=True)
    taxInfoDict = {tinfo['TaxId']: [tinfo, taxCounter[tinfo['TaxId']]] for tinfo in fetchTaxonomyData(taxids)}

    if args.draw_krona_plot:
        path_kr_in = args.kraken_results + '.krona_in'
        with open(path_kr_in, 'wb') as kr_in:
            if args.include_unclassified:
                writeKronaInput(kr_in, taxInfoDict, unclassified=taxCounter['0'])
            else:
                writeKronaInput(kr_in, taxInfoDict)

        kpath = 'ktImportText'
        if args.path_to_krona:
            kpath = os.path.join(args.path_to_krona, kpath)
            assert os.path.exists(kpath)
        else:
            try:
                p = subprocess.Popen('which ktImportText', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                so, se = p.communicate()
            except:
                sys.stderr.write('Failed to determine krona installation.\n')
                sys.exit(1)
            if not so:
                sys.stderr.write('krona installation not found in system path. Please install or use --path-to-krona option.\n')
                sys.exit(1)

        krona_cmd = '%s -o %s %s' % (kpath, args.draw_krona_plot, path_kr_in)

        try:
            p = subprocess.Popen(krona_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            so, se = p.communicate()
        except:
            sys.stderr.write('Krona call failed.\n')
            sys.exit(1)

    if args.write_summary:
        with open(args.write_summary, 'wb') as out:
            writeOutput(out, taxInfoDict, taxCounter)

    pass


if __name__ == '__main__': main()


__author__ = "Christian Schudoma"
__copyright__ = "Copyright 2014-2016, Christian Schudoma, The Sainsbury Laboratory"
__credits__ = ["Pirasteh Pahlavan", "Agathe Jouet", "Yogesh Gupta"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Christian Schudoma"
__email__ = "cschu1981@gmail.com"
__status__ = "Development"
