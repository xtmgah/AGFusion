import agfusion
import pyensembl
from Bio import SeqIO

def test_mouse_1(data,db):
    """
    test CDS and cDNA correct for junction that is on exon boundaries and
    produces an in-frame protein.
    """

    #test the dna and protein coding sequences are correct by comparing
    #with manually generally sequences

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31684294,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39648486,
        db=db,
        pyensembl_data=data
    )

    fusion.save_transcript_cdna('DLG1-BRAF_mouse')
    fusion.save_transcript_cds('DLG1-BRAF_mouse')
    fusion.save_proteins('DLG1-BRAF_mouse')
    fusion.save_images('DLG1-BRAF_mouse')

    test_cdna = SeqIO.parse(open('Dlg1-Braf_cdna_manual.fa','r'),'fasta')
    test_cds = SeqIO.parse(open('Dlg1-Braf_cds_manual.fa','r'),'fasta')

    expected_transcript_combinations = [
        'ENSMUST00000100001-ENSMUST00000002487',
        'ENSMUST00000064477-ENSMUST00000002487',
        'ENSMUST00000115205-ENSMUST00000002487',
        'ENSMUST00000023454-ENSMUST00000002487',
        'ENSMUST00000115201-ENSMUST00000002487',
        'ENSMUST00000132176-ENSMUST00000002487'
    ]

    assert len(set(fusion.transcripts.keys()).intersection(set(expected_transcript_combinations)))==6, "Test 1: unexpected number protein coding transcripts."

    for seq in test_cdna:
        trans=fusion.transcripts[str(seq.id)]
        assert seq.seq==trans.cdna.seq, "cDNA is wrongly predicted: %s" % seq.id

    for seq in test_cds:
        trans=fusion.transcripts[str(seq.id)]
        assert seq.seq==trans.cds.seq, "cds is wrongly predicted: %s" % seq.id


def test_mouse_2(data,db):
    """
    Test CDS correct for junction within the exon (not on boundary) for two
    genes on reverse strand
    """

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000002413",
        gene5primejunction=39725110,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610402,
        db=db,
        pyensembl_data=data
    )

    cds = 'ATGGCGGCGCTGAGTGGCGGCGGTGGCAGCAGCAGCGGTGGCGGCGGCGGCGGTGGCGGCGGCGG' + \
          'TGGCGGTGGCGACGGCGGCGGCGGCGCCGAGCAGGGCCAGGCTCTGTTCAATGGCGACATGGAGC' + \
          'CGGAGGCCGGCGCTGGCGCCGCGGCCTCTTCGGCTGCGGACCCGGCCATTCCTGAAGAATTTGCAGCCTTCAAGTAG'

    assert str(fusion.transcripts['ENSMUST00000002487-ENSMUST00000002487'].cds.seq)==cds, "Test 2: CDS wrong"

def test_mouse_3(data,db):
    """
    Test CDS correct for junction within the exon (not on boundary) for one gene
    one the forward and one gene on the reverse strand
    """

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664869,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610402,
        db=db,
        pyensembl_data=data
    )

    cds = 'ATGCCGGTCCGGAAGCAAGAATTTGCAGCCTTCAAGTAG'

    assert str(fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].cds.seq)==cds, "Test 3: CDS wrong"

def test_mouse_4(data,db):
    """
    Test cDNA correctly produced for junctions being in UTRs
    """

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664851,
        gene3prime="ENSMUSG00000022770",
        gene3primejunction=31873343,
        db=db,
        pyensembl_data=data
    )

    cdna = 'GGGGGTGCGGCCGCCGAAGGGGGAGCTCCTCCCCCGTCCCCTCACCCCCTCAGCTGAGCT' + \
          'CGGGGCGGGGCGGGGTACGTGGAGCGGGGCCGGGCGGGGAAGCTGCTCCGAGTCCGGCCG' + \
          'GAGCGCACCCGGGGCGCCCGCGTACGCCGCTCGCGGGAACTTTGCGGCGGAGCCGCAGGT' + \
          'GTGGAGGCCGCGGAGGGGGGTGCATGAGCGGCGCGGAGAGCGGCGGCTGTCCGGTCCGGC' + \
          'CCCTGCTGGAGTCGCCGCCGGGAGGAGACGAACGAGGAACCAG' + \
          'GTGTGTGCCGCCTTCCTGATTCTGGAGAAAA' + \
          'AAAA'

    assert str(fusion.transcripts['ENSMUST00000064477-ENSMUST00000064477'].cdna.seq)==cdna, "Test 4: cDNA wrong"

def test_mouse_5(data,db):
    """
    Test that AGFusion determines if the effect on each individual transcript
    """

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664852,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39651764,
        db=db,
        pyensembl_data=data
    )

    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_5prime=='CDS (start)',"Test 5: not CDS start"
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_3prime=='CDS',"Test 5: not CDS"

def test_mouse_6(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664851,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610381,
        db=db,
        pyensembl_data=data
    )

    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_5prime=='5UTR (end)',"Test 6: Not found in 5'UTR-end"
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_3prime=='3UTR (start)', "Test 6: Not found in at 3'UTR beginning"

def test_mouse_7(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664850,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610381,
        db=db,
        pyensembl_data=data
    )
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_5prime=='5UTR',"Test 7: Not found in 5'UTR"
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].effect_3prime=='3UTR (start)', "Test 7: Not found in at 3'UTR beginning"

def test_mouse_8(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664851,
        gene3prime="ENSMUSG00000022770",
        gene3primejunction=31871782,
        db=db,
        pyensembl_data=data
    )
    #import pdb; pdb.set_trace()
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000064477'].effect_5prime=='5UTR (end)',"Test 8: Not found in 5'UTR-end"
    assert fusion.transcripts['ENSMUST00000064477-ENSMUST00000064477'].effect_3prime=='3UTR (start)', "Test 8: Not found in at 3'UTR beginning"

def test_mouse_9(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000002413",
        gene5primejunction=39725296,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610381,
        db=db,
        pyensembl_data=data
    )

    assert fusion.transcripts['ENSMUST00000002487-ENSMUST00000002487'].effect_5prime=='5UTR (end)',"Test 9: Not found in 5'UTR-end"
    assert fusion.transcripts['ENSMUST00000002487-ENSMUST00000002487'].effect_3prime=='3UTR (start)', "Test 9: Not found in at 3'UTR beginning"

def test_mouse_10(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664850,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39603240,
        db=db,
        pyensembl_data=data
    )

    cdna = 'GGGGGTGCGGCCGCCGAAGGGGGAGCTCCTCCCCCGTCCCCTCACCCCCTCAGCTGAGCT' + \
          'CGGGGCGGGGCGGGGTACGTGGAGCGGGGCCGGGCGGGGAAGCTGCTCCGAGTCCGGCCG' + \
          'GAGCGCACCCGGGGCGCCCGCGTACGCCGCTCGCGGGAACTTTGCGGCGGAGCCGCAGGT' + \
          'GTGGAGGCCGCGGAGGGGGGTGCATGAGCGGCGCGGAGAGCGGCGGCTGTCCGGTCCGGC' + \
          'CCCTGCTGGAGTCGCCGCCGGGAGGAGACGAACGAGGAACCAG' + \
          'GTGTGTGCCGCCTTCCTGATTCTGGAGAAA' + \
          'GAAA'

    assert str(fusion.transcripts['ENSMUST00000064477-ENSMUST00000002487'].cdna.seq)==cdna,"Test 10: incorrect cDNA"

def test_mouse_11(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31743271,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39665003,
        db=db,
        pyensembl_data=data
    )
    t = fusion.transcripts['ENSMUST00000023454-ENSMUST00000002487']

    assert t.effect_5prime=="intron (cds)","Test 11: incorrect 5' effect: %s" % t.effect_5prime
    assert t.effect_3prime=="intron (cds)","Test 11: incorrect 3' effect: %s" % t.effect_3prime

def test_mouse_12(data,db):

    fusion = agfusion.Fusion(
        gene5prime="ENSMUSG00000022770",
        gene5primejunction=31664820,
        gene3prime="ENSMUSG00000002413",
        gene3primejunction=39610405,
        db=db,
        pyensembl_data=data
    )
    t = fusion.transcripts['ENSMUST00000023454-ENSMUST00000002487']

    assert t.effect_5prime=="intron (before cds)","Test 12: incorrect 5' effect: %s" % t.effect_5prime
    assert t.effect_3prime=="intron (cds)","Test 12: incorrect 3' effect: %s" % t.effect_3prime

data = pyensembl.EnsemblRelease(84,'mouse')
db = agfusion.AGFusionDB('../agfusion/data/agfusion.db')

test_mouse_1(data,db)
test_mouse_2(data,db)
test_mouse_3(data,db)
test_mouse_4(data,db)
test_mouse_5(data,db)
test_mouse_6(data,db)
test_mouse_7(data,db)
test_mouse_8(data,db)
test_mouse_9(data,db)
test_mouse_10(data,db)
test_mouse_11(data,db)
test_mouse_12(data,db)

print 'All tests passed!'
