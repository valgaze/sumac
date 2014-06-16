"""
SUMAC: supermatrix constructor

Copyright 2014 Will Freyman - freyman@berkeley.edu
License: GNU GPLv3 http://www.gnu.org/licenses/gpl.html
"""


import os
import sys
import csv
import multiprocessing
import copy_reg
import types
from Bio import Entrez
from Bio import SeqIO
from Bio.Align.Applications import MuscleCommandline
from util import Color



class Alignments(object):
    """
    Class responsible for managing sequence alignments
    """


    files = []
    taxa = None


    def __init__(self, cluster_files):
        """
        Inputs a list of FASTA files, each file containing an unaligned sequence cluster.
        Creates new processes to align each sequence cluster.
        Generates a list of aligned FASTA files.
        """
        taxa = None
        alignment_files = []
        if not os.path.exists("alignments"):
            os.makedirs("alignments")
        color = Color()
        print(color.blue + "Spawning " + color.red + str(multiprocessing.cpu_count()) + color.blue + " processes to align clusters." + color.done)
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        alignment_files = pool.map(self.align_cluster, cluster_files)
        pool.close()
        pool.join()
        self.files = alignment_files



    def align_cluster(self, cluster_file):
        """
        Worker fuction for align_clusters
        Inputs a FASTA file containing an unaligned sequence cluster.
        Uses MUSCLE to align the cluster.
        """
        # TODO:   
        # use MAFFT instead of MUSCLE to deal with forward/reverse strand issue
        alignment_file = "alignments" + cluster_file[cluster_file.index("/"):]
        muscle_cline = MuscleCommandline(input=cluster_file, out=alignment_file)
        color = Color()
        print(color.red + str(muscle_cline) + color.done)
        sys.stdout.flush()
        stdout, stderr = muscle_cline()
        return alignment_file



    def print_data(self):
        """
        Prints the name of each DNA region, the number of taxa, the aligned length,
        missing data (%), and taxon coverage density
        """
        # first get list of all taxa
        taxa = self.get_all_taxa()

        # print data for each region
        i = 1
        color = Color()
        for alignment in self.files:
            records = list(SeqIO.parse(alignment, "fasta"))
            descriptors = records[0].description.split(" ")
            print(color.blue + "Aligned cluster #: " + color.red + str(i) + color.done)
            print(color.yellow + "DNA region: " + color.red + " ".join(descriptors[3:]) + color.done)
            print(color.yellow + "OTUs: " + color.red + str(len(records)) + color.done)
            print(color.yellow + "Aligned length: " + color.red + str(len(records[0].seq)) + color.done)
            print(color.yellow + "Missing data (%): " + color.red + str(round(100 - (100 * len(records)/float(len(taxa))), 1)) + color.done)
            print(color.yellow + "Taxon coverage density: "  + color.red + str(round(len(records)/float(len(taxa)), 2)) + color.done)
            i += 1



    def make_gene_region_csv(self):
        """
        Generates a CSV files with the data for each DNA region.
        """
        taxa = self.get_all_taxa()
        with open('gene_regions.csv', 'wb') as csv_output:
            csvwriter = csv.writer(csv_output)
            header = ["Gene Region #", "Description", "# of OTUs", "Aligned Length", "Missing Data (%)", "Taxon Coverage Density"]
            csvwriter.writerow(header)
            i = 1
            for alignment in self.files:
                row = []
                records = list(SeqIO.parse(alignment, "fasta"))
                descriptors = records[0].description.split(" ")
                row.append(str(i))
                row.append(" ".join(descriptors[3:]))
                row.append(str(len(records)))
                row.append(str(len(records[0].seq)))
                row.append(str(round(100 - (100 * len(records)/float(len(taxa))), 1)))
                row.append(str(round(len(records)/float(len(taxa)), 2)))
                csvwriter.writerow(row)
                i += 1




    def get_all_taxa(self):
        """
        Helper method to get a list of all taxa found in the alignments.
        """
        if self.taxa != None:
            return self.taxa
        else:
            taxa = []
            for alignment in self.files:
                records = SeqIO.parse(alignment, "fasta")
                for record in records:
                    descriptors = record.description.split(" ")
                    taxon = descriptors[1] + " " + descriptors[2]
                    if taxon not in taxa:
                        taxa.append(taxon)
            self.taxa = taxa
            return self.taxa



# pickle method recipe by Steven Bethard
# see http://stackoverflow.com/questions/1816958/cant-pickle-type-instancemethod-when-using-pythons-multiprocessing-pool-ma/
def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)



def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
